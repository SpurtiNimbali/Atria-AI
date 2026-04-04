"""
Hybrid search implementation combining BM25 and vector search.
"""
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch


def hybrid_search(
    es: Elasticsearch,
    patient_id: str,
    query: str,
    embedding: List[float],
    k: int = 10,
    index_name: str = "ehr_chunks",
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining BM25 and vector similarity.
    
    Args:
        es: Elasticsearch client
        patient_id: Patient ID to filter by
        query: Text query for BM25
        embedding: Query embedding vector for KNN
        k: Number of results to return
        index_name: Index to search
        bm25_weight: Weight for BM25 score (0-1)
        vector_weight: Weight for vector score (0-1)
    
    Returns:
        List of chunks with combined scores
    """
    
    # Elasticsearch 8.x hybrid search using RRF (Reciprocal Rank Fusion)
    search_body = {
        "size": k,
        "query": {
            "bool": {
                "must": [
                    {"term": {"patient_id": patient_id}}
                ],
                "should": [
                    {
                        "match": {
                            "text": {
                                "query": query,
                                "boost": bm25_weight
                            }
                        }
                    }
                ]
            }
        },
        "knn": {
            "field": "embedding",
            "query_vector": embedding,
            "k": k,
            "num_candidates": k * 2,
            "boost": vector_weight,
            "filter": {
                "term": {"patient_id": patient_id}
            }
        },
        "_source": {
            "excludes": ["embedding"]  # Don't return embeddings in results
        }
    }
    
    response = es.search(index=index_name, body=search_body)
    
    results = []
    for hit in response["hits"]["hits"]:
        chunk = hit["_source"]
        chunk["_score"] = hit["_score"]
        chunk["_id"] = hit["_id"]
        results.append(chunk)
    
    return results


def get_patient_summary(
    es: Elasticsearch,
    patient_id: str,
    index_name: str = "ehr_chunks"
) -> Dict[str, Any]:
    """
    Get a summary of available data for a patient.
    
    Returns counts by resource type and most recent timestamp.
    """
    # Check if index exists first
    if not es.indices.exists(index=index_name):
        return {
            "patient_id": patient_id,
            "total_chunks": 0,
            "resource_types": {},
            "latest_timestamp": None,
            "message": "Index does not exist. Please ingest patient data first."
        }
    
    agg_body = {
        "size": 0,
        "query": {
            "term": {"patient_id": patient_id}
        },
        "aggs": {
            "by_resource_type": {
                "terms": {
                    "field": "resource_type",
                    "size": 20
                }
            },
            "latest_timestamp": {
                "max": {
                    "field": "timestamp"
                }
            }
        }
    }
    
    try:
        # Add timeout to search request
        response = es.search(index=index_name, body=agg_body, request_timeout=30)
        
        resource_counts = {}
        if "aggregations" in response and "by_resource_type" in response["aggregations"]:
            for bucket in response["aggregations"]["by_resource_type"]["buckets"]:
                resource_counts[bucket["key"]] = bucket["doc_count"]
        
        total_chunks = response["hits"]["total"]["value"] if "hits" in response else 0
        latest_timestamp = None
        if "aggregations" in response and "latest_timestamp" in response["aggregations"]:
            latest_timestamp = response["aggregations"]["latest_timestamp"].get("value_as_string")
        
        return {
            "patient_id": patient_id,
            "total_chunks": total_chunks,
            "resource_types": resource_counts,
            "latest_timestamp": latest_timestamp
        }
    except Exception as e:
        # Return empty summary on error
        return {
            "patient_id": patient_id,
            "total_chunks": 0,
            "resource_types": {},
            "latest_timestamp": None,
            "error": str(e),
            "message": f"Error retrieving patient data: {str(e)}"
        }


def get_recent_chunks(
    es: Elasticsearch,
    patient_id: str,
    limit: int = 20,
    index_name: str = "ehr_chunks"
) -> List[Dict[str, Any]]:
    """Get most recent chunks for a patient (for context display)."""
    
    search_body = {
        "size": limit,
        "query": {
            "term": {"patient_id": patient_id}
        },
        "sort": [
            {"timestamp": {"order": "desc"}}
        ],
        "_source": {
            "excludes": ["embedding"]
        }
    }
    
    response = es.search(index=index_name, body=search_body)
    
    return [hit["_source"] for hit in response["hits"]["hits"]]
