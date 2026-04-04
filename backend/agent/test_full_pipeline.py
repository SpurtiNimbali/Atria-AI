"""
Test the full pipeline: FHIR → Normalize → Embed → Index → Search
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_full_pipeline(patient_id: str = "example"):
    """Test complete ingestion and retrieval pipeline."""
    
    print("=" * 60)
    print("EHR COPILOT - FULL PIPELINE TEST")
    print("=" * 60)
    print()
    
    # Step 1: FHIR Client
    print("Step 1: Fetching FHIR data...")
    from fhir_client import FHIRClient
    
    fhir_client = FHIRClient()
    fhir_data = fhir_client.get_all_patient_data(patient_id)
    print(f"✓ Fetched FHIR data for patient: {patient_id}")
    print()
    
    # Step 2: Normalize
    print("Step 2: Normalizing FHIR resources to chunks...")
    from normalize import normalize_fhir_data
    
    chunks = normalize_fhir_data(fhir_data)
    print(f"✓ Created {len(chunks)} chunks")
    print()
    
    # Show sample chunk
    if chunks:
        print("Sample chunk:")
        sample = chunks[0]
        print(f"  Resource: {sample['resource_type']}")
        print(f"  Text: {sample['text'][:100]}...")
        print()
    
    # Step 3: Generate embeddings
    print("Step 3: Generating embeddings...")
    from embeddings import generate_embeddings
    
    texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(texts)
    
    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding
    
    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"  Embedding dimension: {len(embeddings[0])}")
    print()
    
    # Step 4: Index into Elasticsearch
    print("Step 4: Indexing into Elasticsearch...")
    from elastic_client import get_elastic_client, create_index, delete_patient_chunks, index_chunks
    
    es = get_elastic_client()
    create_index(es)
    
    # Delete old data
    delete_patient_chunks(es, patient_id)
    
    # Index new data
    result = index_chunks(es, chunks)
    print(f"✓ Indexed {result['success']} chunks")
    if result['failed'] > 0:
        print(f"  ⚠ {result['failed']} chunks failed")
    print()
    
    # Step 5: Test search
    print("Step 5: Testing hybrid search...")
    from search import hybrid_search, get_patient_summary
    
    # Get summary
    summary = get_patient_summary(es, patient_id)
    print(f"✓ Patient summary:")
    print(f"  Total chunks: {summary['total_chunks']}")
    print(f"  Resource types: {list(summary['resource_counts'].keys())}")
    print()
    
    # Test query
    test_query = "medications"
    print(f"Test query: '{test_query}'")
    
    query_embedding = generate_embeddings(test_query)
    
    results = hybrid_search(
        es,
        patient_id=patient_id,
        query=test_query,
        embedding=query_embedding,
        k=5
    )
    
    print(f"✓ Found {len(results)} results")
    print()
    
    if results:
        print("Top 3 results:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result['resource_type']} (score: {result['_score']:.3f})")
            print(f"   {result['text'][:150]}...")
    
    print()
    print("=" * 60)
    print("✅ FULL PIPELINE TEST COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Start gateway: cd gateway && uvicorn main:app --reload")
    print("  2. Start frontend: cd frontend && npm run dev")
    print("  3. Open http://localhost:3000")
    print()


if __name__ == "__main__":
    import sys
    
    patient_id = sys.argv[1] if len(sys.argv) > 1 else "example"
    
    try:
        test_full_pipeline(patient_id)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
