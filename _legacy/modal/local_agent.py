#!/usr/bin/env python3
"""
Local agent - runs the agent logic on your machine.
Same logic as Modal function, just running locally.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if not env_file.exists():
    env_file = project_root / "env.example"
load_dotenv(env_file)

# Set environment variables for local use
os.environ.setdefault("ELASTIC_URL", "http://localhost:9200")
os.environ.setdefault("ELASTIC_USER", "elastic")
os.environ.setdefault("ELASTIC_PASSWORD", "changeme")
os.environ.setdefault("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4")

# Verify API keys are set
if not os.getenv("JINA_API_KEY") or os.getenv("JINA_API_KEY").startswith("your_"):
    os.environ["JINA_API_KEY"] = "jina_df357fda5d5d41f580b595e80f8920c8HS4s_-a69Vtry9OyS0YLQ_VUL1iX"

if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY").startswith("sk-xxxxx"):
    os.environ["OPENAI_API_KEY"] = "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"


def answer_query(patient_id: str, user_query: str) -> Dict[str, Any]:
    """
    Answer a clinical query using RAG over patient's EHR data.
    Same logic as Modal function, just runs locally.
    
    Args:
        patient_id: Patient ID
        user_query: Clinician's question
    
    Returns:
        Dict with events, final_answer, and citations
    """
    from elastic_client import get_elastic_client
    from search import hybrid_search, get_patient_summary
    from embeddings import generate_embedding
    from openai import OpenAI
    
    print(f"🤔 Answering query for patient {patient_id}: {user_query}")
    
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
                "content": "No patient data found. Please run ingestion first."
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


if __name__ == "__main__":
    # Test the agent
    import sys
    
    patient_id = sys.argv[1] if len(sys.argv) > 1 else "example"
    query = sys.argv[2] if len(sys.argv) > 2 else "What medications is this patient taking?"
    
    print(f"\nTesting agent with query: {query}\n")
    
    result = answer_query(patient_id, query)
    
    print("\n" + "=" * 60)
    print("AGENT RESPONSE")
    print("=" * 60)
    print(f"\n{result['final_answer']}\n")
    print(f"Citations: {len(result['citations'])}")
    for citation in result['citations']:
        print(f"  [{citation['id']}] {citation['resource_type']} - {citation['snippet'][:80]}...")
