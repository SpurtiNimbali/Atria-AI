"""
Test script for Elasticsearch hybrid search.
Run after indexing some test data.
"""
import os
from dotenv import load_dotenv
from elastic_client import get_elastic_client, create_index
from search import hybrid_search, get_patient_summary, get_recent_chunks

load_dotenv()


def test_search():
    """Test hybrid search functionality."""
    es = get_elastic_client()
    
    # Ensure index exists
    create_index(es)
    
    # Test patient ID (use after ingestion)
    patient_id = "example"
    
    print(f"\n=== Patient Summary for {patient_id} ===")
    summary = get_patient_summary(es, patient_id)
    print(f"Total chunks: {summary['total_chunks']}")
    print(f"Resource counts: {summary['resource_counts']}")
    print(f"Latest timestamp: {summary['latest_timestamp']}")
    
    print(f"\n=== Recent Chunks ===")
    recent = get_recent_chunks(es, patient_id, limit=5)
    for chunk in recent:
        print(f"\n{chunk['resource_type']} ({chunk['timestamp']})")
        print(f"  {chunk['text'][:150]}...")
    
    # Test hybrid search (requires embedding)
    # Note: This will fail without actual embeddings indexed
    # Uncomment after full ingestion pipeline is working
    """
    print(f"\n=== Hybrid Search Test ===")
    query = "diabetes medications"
    # Need to generate embedding for query first
    from embeddings import generate_embedding
    query_embedding = generate_embedding(query)
    
    results = hybrid_search(
        es,
        patient_id=patient_id,
        query=query,
        embedding=query_embedding,
        k=5
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['resource_type']} (score: {result['_score']:.3f})")
        print(f"   {result['text'][:200]}...")
    """


if __name__ == "__main__":
    test_search()
