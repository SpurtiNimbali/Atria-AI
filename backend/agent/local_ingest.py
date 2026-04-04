#!/usr/bin/env python3
"""
Local ingestion script - runs ingestion on your machine.
This is the same logic as the Modal function, just running locally.
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Repo root: backend/agent/local_ingest.py -> parents[2] == repository root
project_root = Path(__file__).resolve().parents[2]
env_file = project_root / ".env"
if not env_file.exists():
    env_file = project_root / "env.example"
# Load .env file (handle permission errors gracefully)
try:
    load_dotenv(env_file)
except PermissionError:
    # Environment variables may already be set
    pass

# Sensible local defaults only (no secrets committed)
os.environ.setdefault("ELASTIC_URL", "http://localhost:9200")
os.environ.setdefault("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4")

def ingest_patient_local(patient_id: str):
    """
    Ingest a patient's FHIR data locally.
    Same logic as Modal function, just runs on your machine.
    """
    print(f"🏥 Starting local ingestion for patient: {patient_id}")
    print()
    
    # Step 1: Pull FHIR data
    print("📋 Step 1: Pulling FHIR data...")
    
    # Check if this is a synthetic patient (load from local JSON file)
    if patient_id.startswith("synthetic"):
        import json
        json_file = Path(__file__).parent / "synthetic_patient.json"
        print(f"Loading from local file: {json_file}")
        
        with open(json_file, "r") as f:
            bundle = json.load(f)
        
        # Convert FHIR Bundle to the format expected by normalize_fhir_data
        fhir_data = {
            "patient": None,
            "conditions": [],
            "medication_requests": [],
            "medication_statements": [],
            "allergies": [],
            "vital_signs": [],
            "lab_results": [],
            "encounters": [],
            "procedures": [],
            "coverage": []
        }
        
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            if resource_type == "Patient":
                fhir_data["patient"] = resource
            elif resource_type == "Condition":
                fhir_data["conditions"].append(resource)
            elif resource_type == "MedicationRequest":
                fhir_data["medication_requests"].append(resource)
            elif resource_type == "MedicationStatement":
                fhir_data["medication_statements"].append(resource)
            elif resource_type == "AllergyIntolerance":
                fhir_data["allergies"].append(resource)
            elif resource_type == "Observation":
                # Categorize observations
                category = resource.get("category", [{}])[0].get("coding", [{}])[0].get("code", "")
                if "vital-signs" in category:
                    fhir_data["vital_signs"].append(resource)
                else:
                    fhir_data["lab_results"].append(resource)
            elif resource_type == "Encounter":
                fhir_data["encounters"].append(resource)
            elif resource_type == "Procedure":
                fhir_data["procedures"].append(resource)
            elif resource_type == "Coverage":
                fhir_data["coverage"].append(resource)
        
        print("✓ Loaded synthetic patient data from file")
        print(f"  - Patient: {'1 resource' if fhir_data['patient'] else '0 resources'}")
        print(f"  - Conditions: {len(fhir_data['conditions'])} resources")
        print(f"  - Medications: {len(fhir_data['medication_requests'])} resources")
        print(f"  - Observations: {len(fhir_data['vital_signs']) + len(fhir_data['lab_results'])} resources")
        print(f"  - Encounters: {len(fhir_data['encounters'])} resources")
        print(f"  - Procedures: {len(fhir_data['procedures'])} resources")
        print(f"  - Coverage: {len(fhir_data['coverage'])} resources")
    else:
        # Pull from FHIR server
        from fhir_client import FHIRClient
        
        fhir_client = FHIRClient()
        fhir_data = fhir_client.get_all_patient_data(patient_id)
        print("✓ FHIR data retrieved")
    print()
    
    # Step 2: Normalize to chunks
    print("🔄 Step 2: Normalizing to searchable chunks...")
    from normalize import normalize_fhir_data
    
    chunks = normalize_fhir_data(fhir_data)
    print(f"✓ Created {len(chunks)} chunks")
    print()
    
    if not chunks:
        print("❌ No data found for patient")
        return {
            "patient_id": patient_id,
            "status": "no_data",
            "message": "No FHIR data found for patient"
        }
    
    # Step 3: Generate embeddings
    print("🧠 Step 3: Generating embeddings with Jina AI...")
    from embeddings import generate_embeddings
    
    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)
    
    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    
    print(f"✓ Generated {len(embeddings)} embeddings")
    print()
    
    # Step 4: Index into Elasticsearch
    print("💾 Step 4: Indexing into Elasticsearch...")
    from elastic_client import get_elastic_client, create_index, delete_patient_chunks, index_chunks
    
    es = get_elastic_client()
    create_index(es)
    
    # Delete old data for this patient
    delete_patient_chunks(es, patient_id)
    
    # Index new data
    result = index_chunks(es, chunks)
    
    print(f"✓ Indexed {result['success']} chunks")
    if result['failed'] > 0:
        print(f"⚠️  {result['failed']} chunks failed")
    print()
    
    print("=" * 60)
    print("✅ INGESTION COMPLETE!")
    print("=" * 60)
    print()
    print(f"Patient ID: {patient_id}")
    print(f"Chunks indexed: {result['success']}")
    print(f"Ready for queries!")
    print()
    
    return {
        "patient_id": patient_id,
        "status": "success",
        "chunks_indexed": result["success"],
        "chunks_failed": result["failed"]
    }


if __name__ == "__main__":
    patient_id = sys.argv[1] if len(sys.argv) > 1 else "example"
    
    try:
        result = ingest_patient_local(patient_id)
        sys.exit(0 if result["status"] == "success" else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
