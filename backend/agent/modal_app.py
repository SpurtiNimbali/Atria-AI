"""
Modal app for EHR Copilot.
Includes: FHIR ingestion, embedding generation, and agent reasoning.
"""
# Fix certifi compatibility issue with Python 3.14
import certifi
if not hasattr(certifi, 'where'):
    import ssl
    import os as os_module
    def certifi_where():
        cert_path = os_module.path.join(os_module.path.dirname(certifi.__file__), 'cacert.pem')
        if os_module.path.exists(cert_path):
            return cert_path
        return ssl.get_default_verify_paths().cafile or '/etc/ssl/cert.pem'
    certifi.where = certifi_where

import modal
import os
from typing import List, Dict, Any, Optional

# Create Modal app
app = modal.App("ehr-copilot")

# Define image with dependencies and local Python files
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "elasticsearch>=8.11.0",
        "httpx>=0.25.0",
        "python-dotenv>=1.0.0",
        "openai>=1.6.0",
        "pydantic>=2.5.0"
    )
    .add_local_python_source("fhir_client")
    .add_local_python_source("normalize")
    .add_local_python_source("embeddings")
    .add_local_python_source("elastic_client")
    .add_local_python_source("search")
)

# Secrets for API keys
secrets = [
    modal.Secret.from_name("elastic-secret"),  # ELASTIC_URL, ELASTIC_USER, ELASTIC_PASSWORD
    modal.Secret.from_name("fhir-secret"),     # FHIR_BASE_URL, FHIR_TOKEN (optional)
    modal.Secret.from_name("jina-secret"),     # JINA_API_KEY
    modal.Secret.from_name("openai-secret")    # OPENAI_API_KEY
]


@app.function(
    image=image,
    secrets=secrets,
    timeout=600
)
def ingest_patient(patient_id: str) -> Dict[str, Any]:
    """
    Ingest a single patient's FHIR data into Elasticsearch.
    
    Steps:
    1. Pull FHIR resources
    2. Normalize into chunks
    3. Generate embeddings
    4. Index into Elasticsearch
    
    Returns:
        Summary of ingestion results
    """
    from fhir_client import FHIRClient
    from normalize import normalize_fhir_data
    from embeddings import generate_embeddings
    from elastic_client import get_elastic_client, create_index, delete_patient_chunks, index_chunks
    
    print(f"Starting ingestion for patient: {patient_id}")
    
    # Step 1: Pull FHIR data
    fhir_client = FHIRClient()
    fhir_data = fhir_client.get_all_patient_data(patient_id)
    
    # Step 2: Normalize to chunks
    chunks = normalize_fhir_data(fhir_data)
    
    if not chunks:
        return {
            "patient_id": patient_id,
            "status": "no_data",
            "message": "No FHIR data found for patient"
        }
    
    # Step 3: Generate embeddings
    print(f"Generating embeddings for {len(chunks)} chunks...")
    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)
    
    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    
    # Step 4: Index into Elasticsearch
    es = get_elastic_client()
    create_index(es)  # Ensure index exists
    
    # Delete old data for this patient
    delete_patient_chunks(es, patient_id)
    
    # Index new data
    result = index_chunks(es, chunks)
    
    print(f"Ingestion complete: {result['success']} chunks indexed")
    
    return {
        "patient_id": patient_id,
        "status": "success",
        "chunks_indexed": result["success"],
        "chunks_failed": result["failed"]
    }


@app.function(
    image=image,
    secrets=secrets,
    timeout=3600
)
def ingest_cohort(patient_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Ingest multiple patients in parallel.
    
    Returns:
        List of ingestion results for each patient
    """
    results = []
    for patient_id in patient_ids:
        try:
            result = ingest_patient.remote(patient_id)
            results.append(result)
        except Exception as e:
            results.append({
                "patient_id": patient_id,
                "status": "error",
                "message": str(e)
            })
    
    return results


@app.function(
    image=image,
    secrets=secrets,
    schedule=modal.Cron("0 */6 * * *"),  # Every 6 hours
    timeout=7200
)
def scheduled_ingest():
    """
    Scheduled job to refresh patient data.
    Configure patient IDs in environment or database.
    """
    # Example: hardcoded patient IDs for demo
    # In production, fetch from database or config
    patient_ids = os.getenv("PATIENT_IDS", "example").split(",")
    
    print(f"Starting scheduled ingestion for {len(patient_ids)} patients")
    results = ingest_cohort.remote(patient_ids)
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    print(f"Scheduled ingestion complete: {success_count}/{len(patient_ids)} successful")
    
    return results


@app.function(
    image=image,
    secrets=secrets,
    timeout=300
)
def answer(patient_id: str, user_query: str) -> Dict[str, Any]:
    """
    Answer a clinical query using RAG over patient's EHR data.
    
    Args:
        patient_id: Patient ID
        user_query: Clinician's question
    
    Returns:
        Dict with:
        - events: List of UI events (reasoning_step, response, timeline_commit)
        - final_answer: Complete answer text
        - citations: List of source chunks
    """
    from elastic_client import get_elastic_client
    from search import hybrid_search, get_patient_summary
    from embeddings import generate_embedding
    from openai import OpenAI
    
    print(f"Answering query for patient {patient_id}: {user_query}")
    
    events = []
    
    # Step 1: Get patient summary
    es = get_elastic_client()
    summary = get_patient_summary(es, patient_id)
    
    events.append({
        "type": "reasoning_step",
        "content": f"Checking patient data: {summary['total_chunks']} chunks available"
    })
    
    if summary["total_chunks"] == 0:
        return {
            "events": events + [{
                "type": "response",
                "content": "No patient data found. Please refresh patient data first."
            }],
            "final_answer": "No patient data available.",
            "citations": []
        }
    
    # Step 2: Generate query embedding
    events.append({
        "type": "reasoning_step",
        "content": "Searching EHR records..."
    })
    
    query_embedding = generate_embedding(user_query)
    
    # Step 3: Hybrid search
    results = hybrid_search(
        es,
        patient_id=patient_id,
        query=user_query,
        embedding=query_embedding,
        k=10
    )
    
    events.append({
        "type": "reasoning_step",
        "content": f"Found {len(results)} relevant records"
    })
    
    if not results:
        return {
            "events": events + [{
                "type": "response",
                "content": "No relevant records found for this query."
            }],
            "final_answer": "No relevant information found.",
            "citations": []
        }
    
    # Step 4: Build context for LLM
    context_parts = []
    citations = []
    
    for i, result in enumerate(results[:5], 1):  # Top 5 results
        context_parts.append(f"[{i}] {result['text']}")
        citations.append({
            "id": i,
            "resource_type": result["resource_type"],
            "resource_id": result["resource_id"],
            "snippet": result["text"][:200],
            "timestamp": result["timestamp"],
            "score": result["_score"]
        })
    
    context = "\n\n".join(context_parts)
    
    # Step 5: Generate answer with OpenAI
    events.append({
        "type": "reasoning_step",
        "content": "Analyzing records and formulating answer..."
    })
    
    client = OpenAI()
    
    system_prompt = """You are a clinical assistant helping clinicians understand patient EHR data.

CRITICAL RULES:
- Only use information from the provided EHR records
- Cite sources using [1], [2], etc.
- If information is missing, explicitly state what's missing
- Never fabricate patient data
- Suggest next steps when data is incomplete
- This is NOT medical advice - educational support only

Format your response as:
1. Direct answer to the question
2. Supporting details from records (with citations)
3. What's missing (if anything)
4. Suggested next steps (if applicable)
"""
    
    user_prompt = f"""Patient Query: {user_query}

Available EHR Records:
{context}

Please answer the query based on these records."""
    
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    answer = response.choices[0].message.content
    
    # Step 6: Return events
    events.append({
        "type": "response",
        "content": answer
    })
    
    # Create timeline commit
    events.append({
        "type": "timeline_commit",
        "title": user_query[:50] + ("..." if len(user_query) > 50 else ""),
        "summary": answer[:150] + ("..." if len(answer) > 150 else ""),
        "citations": [c["id"] for c in citations]
    })
    
    return {
        "events": events,
        "final_answer": answer,
        "citations": citations
    }


@app.local_entrypoint()
def main(command: str = "help", patient_id: str = "example"):
    """
    Local CLI for testing Modal functions.
    
    Usage:
        modal run modal_app.py --command ingest --patient-id example
        modal run modal_app.py --command answer --patient-id example
    """
    if command == "ingest":
        print(f"Ingesting patient: {patient_id}")
        result = ingest_patient.remote(patient_id)
        print(f"Result: {result}")
    
    elif command == "answer":
        query = "What medications is this patient taking?"
        print(f"Query: {query}")
        result = answer.remote(patient_id, query)
        print(f"\nAnswer: {result['final_answer']}")
        print(f"\nCitations: {len(result['citations'])}")
    
    elif command == "cohort":
        patient_ids = patient_id.split(",")
        print(f"Ingesting cohort: {patient_ids}")
        results = ingest_cohort.remote(patient_ids)
        for r in results:
            print(f"  {r['patient_id']}: {r['status']}")
    
    else:
        print("""
EHR Copilot Modal CLI

Commands:
  ingest   - Ingest a patient's FHIR data
  answer   - Test agent with a query
  cohort   - Ingest multiple patients (comma-separated IDs)
  
Examples:
  modal run modal_app.py --command ingest --patient-id example
  modal run modal_app.py --command cohort --patient-id "example,smart-1032702"
  modal run modal_app.py --command answer --patient-id example
        """)
