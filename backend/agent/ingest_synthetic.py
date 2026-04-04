#!/usr/bin/env python3
"""
Ingest synthetic FHIR data from a JSON file into Elasticsearch.
"""
import os
import sys
import json
from dotenv import load_dotenv
from pathlib import Path

# Repo root: backend/agent/ingest_synthetic.py -> parents[2]
_project_root = Path(__file__).resolve().parents[2]
_env = _project_root / ".env"
if not _env.exists():
    _env = _project_root / "env.example"
try:
    load_dotenv(_env)
except PermissionError:
    pass

os.environ.setdefault("ELASTIC_URL", "http://localhost:9200")


def convert_bundle_to_structured(bundle: dict) -> dict:
    """
    Convert a FHIR Bundle into the structured format expected by normalize_fhir_data.
    
    Args:
        bundle: FHIR Bundle with entry list
    
    Returns:
        Dict with keys: patient, conditions, medication_requests, etc.
    """
    result = {
        "patient": None,
        "conditions": [],
        "medication_requests": [],
        "medication_statements": [],
        "allergies": [],
        "vital_signs": [],
        "lab_results": [],
        "encounters": [],
        "procedures": []
    }
    
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        
        if resource_type == "Patient":
            result["patient"] = resource
        elif resource_type == "Condition":
            result["conditions"].append(resource)
        elif resource_type == "MedicationRequest":
            result["medication_requests"].append(resource)
        elif resource_type == "MedicationStatement":
            result["medication_statements"].append(resource)
        elif resource_type == "AllergyIntolerance":
            result["allergies"].append(resource)
        elif resource_type == "Observation":
            # Categorize observations
            category = resource.get("category", [{}])[0].get("coding", [{}])[0].get("code", "")
            if "vital-signs" in category:
                result["vital_signs"].append(resource)
            elif "laboratory" in category:
                result["lab_results"].append(resource)
            else:
                result["lab_results"].append(resource)  # Default to lab results
        elif resource_type == "Encounter":
            result["encounters"].append(resource)
        elif resource_type == "Procedure":
            result["procedures"].append(resource)
    
    return result


def ingest_synthetic_patient(json_file: str):
    """
    Ingest a synthetic patient from a FHIR Bundle JSON file.
    
    Args:
        json_file: Path to the JSON file containing the FHIR Bundle
    """
    print("=" * 60)
    print("🏥 SYNTHETIC PATIENT INGESTION")
    print("=" * 60)
    print()
    
    # Step 1: Load the Bundle
    print(f"📂 Step 1: Loading FHIR Bundle from {json_file}...")
    with open(json_file, 'r') as f:
        bundle = json.load(f)
    
    if bundle.get("resourceType") != "Bundle":
        raise ValueError("JSON file does not contain a FHIR Bundle")
    
    entry_count = len(bundle.get("entry", []))
    print(f"✓ Loaded Bundle with {entry_count} resources")
    print()
    
    # Step 2: Convert Bundle to structured format
    print("🔄 Step 2: Converting Bundle to structured format...")
    structured_data = convert_bundle_to_structured(bundle)
    
    if not structured_data["patient"]:
        raise ValueError("No Patient resource found in Bundle")
    
    patient_id = structured_data["patient"]["id"]
    print(f"✓ Patient ID: {patient_id}")
    print(f"✓ Conditions: {len(structured_data['conditions'])}")
    print(f"✓ Medications: {len(structured_data['medication_requests'])}")
    print(f"✓ Allergies: {len(structured_data['allergies'])}")
    print(f"✓ Vital Signs: {len(structured_data['vital_signs'])}")
    print(f"✓ Lab Results: {len(structured_data['lab_results'])}")
    print(f"✓ Encounters: {len(structured_data['encounters'])}")
    print(f"✓ Procedures: {len(structured_data['procedures'])}")
    print()
    
    # Step 3: Normalize to chunks
    print("📝 Step 3: Normalizing to searchable chunks...")
    from normalize import normalize_fhir_data
    
    chunks = normalize_fhir_data(structured_data)
    print(f"✓ Created {len(chunks)} chunks")
    print()
    
    if not chunks:
        print("❌ No chunks created - nothing to index")
        return {
            "patient_id": patient_id,
            "status": "no_data",
            "message": "No chunks created from FHIR data"
        }
    
    # Show sample chunks
    print("📄 Sample chunks:")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"  {i}. {chunk['resource_type']}: {chunk['text'][:80]}...")
    print()
    
    # Step 4: Generate embeddings
    print("🧠 Step 4: Generating embeddings with Jina AI...")
    from embeddings import generate_embeddings
    
    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)
    
    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    
    print(f"✓ Generated {len(embeddings)} embeddings")
    print()
    
    # Step 5: Index into Elasticsearch
    print("💾 Step 5: Indexing into Elasticsearch...")
    from elastic_client import get_elastic_client, create_index, delete_patient_chunks, index_chunks
    
    es = get_elastic_client()
    create_index(es)
    
    # Delete old data for this patient
    print(f"  Removing old data for patient {patient_id}...")
    delete_patient_chunks(es, patient_id)
    
    # Index new data
    print(f"  Indexing {len(chunks)} chunks...")
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
    print("Next steps:")
    print("  1. Start the API: cd ../../backend && source venv/bin/activate && uvicorn main:app --reload --port 8000")
    print("  2. Start the UI: cd ../../web && npm run dev")
    print(f"  3. Query the patient: Use patient ID '{patient_id}'")
    print()
    
    return {
        "patient_id": patient_id,
        "status": "success",
        "chunks_indexed": result["success"],
        "chunks_failed": result["failed"]
    }


if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else "synthetic_patient.json"
    
    try:
        result = ingest_synthetic_patient(json_file)
        sys.exit(0 if result["status"] == "success" else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
