"""
Elasticsearch client for EHR chunks indexing and retrieval.
"""

# Fix certifi compatibility issue with Python 3.14
import certifi
if not hasattr(certifi, 'where'):
    import ssl
    import os as os_module
    def certifi_where():
        if hasattr(certifi, '__file__') and certifi.__file__:
            cert_path = os_module.path.join(os_module.path.dirname(certifi.__file__), 'cacert.pem')
            if os_module.path.exists(cert_path):
                return cert_path
        default_paths = ssl.get_default_verify_paths()
        return default_paths.cafile or default_paths.capath or '/etc/ssl/cert.pem'
    certifi.where = certifi_where

import os
import socket
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urlunparse

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


def _railway_private_es_url(url: str) -> str:
    """
    Railway private networking is IPv6-oriented; urllib3 often stalls trying IPv4 first.
    If we can resolve an IPv6 address for *.railway.internal, use a literal in the URL.
    Set ELASTIC_RAILWAY_RAW_URL=1 to skip (use hostname only).
    """
    if (
        ".railway.internal" not in url
        or os.getenv("ELASTIC_RAILWAY_RAW_URL", "").strip() == "1"
    ):
        return url
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 9200
        if not host:
            return url
        v6: Optional[str] = None
        for family, _, _, _, sockaddr in socket.getaddrinfo(
            host, port, type=socket.SOCK_STREAM
        ):
            if family == socket.AF_INET6:
                v6 = sockaddr[0]
                break
        if v6:
            netloc = f"[{v6}]:{port}"
            return urlunparse(
                (parsed.scheme, netloc, "", "", "", "")
            )
    except OSError:
        pass
    return url


def get_elastic_client() -> Elasticsearch:
    """Create and return Elasticsearch client."""
    raw_elastic_url = os.getenv("ELASTIC_URL", "http://localhost:9200").strip()
    elastic_url = _railway_private_es_url(raw_elastic_url)
    elastic_api_key = os.getenv("ELASTIC_API_KEY")
    elastic_password = (os.getenv("ELASTIC_PASSWORD") or "").strip()

    # Common connection settings with timeout
    connection_params = {
        "timeout": 30,  # 30 second timeout
        "max_retries": 3,
        "retry_on_timeout": True
    }

    # Local / dev — security off
    if "localhost" in raw_elastic_url or "127.0.0.1" in raw_elastic_url:
        return Elasticsearch(
            elastic_url,
            verify_certs=False,
            ssl_show_warn=False,
            **connection_params
        )

    # Railway private cluster — xpack.security disabled, no basic_auth
    if ".railway.internal" in raw_elastic_url and not elastic_api_key and not elastic_password:
        return Elasticsearch(
            elastic_url,
            verify_certs=False,
            ssl_show_warn=False,
            **connection_params
        )

    # Elastic Cloud / secured cluster
    if elastic_api_key:
        return Elasticsearch(
            elastic_url,
            api_key=elastic_api_key,
            verify_certs=True,
            **connection_params
        )

    elastic_user = os.getenv("ELASTIC_USER", "elastic")
    return Elasticsearch(
        elastic_url,
        basic_auth=(elastic_user, elastic_password or "changeme"),
        verify_certs=True,
        **connection_params
    )


def create_index(es: Elasticsearch, index_name: str = "ehr_chunks"):
    """Create the EHR chunks index with proper mappings."""
    
    if es.indices.exists(index=index_name):
        print(f"Index {index_name} already exists")
        return
    
    mappings = {
        "properties": {
            "patient_id": {"type": "keyword"},
            "resource_type": {"type": "keyword"},
            "resource_id": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "text": {
                "type": "text",
                "analyzer": "standard"
            },
            "metadata": {
                "type": "object",
                "enabled": True
            },
            "embedding": {
                "type": "dense_vector",
                "dims": 768,  # Jina embeddings v2-base-en dimension
                "index": True,
                "similarity": "cosine"
            }
        }
    }
    
    es.indices.create(
        index=index_name,
        mappings=mappings,
        settings={
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    )
    print(f"Created index: {index_name}")


def index_chunks(
    es: Elasticsearch,
    chunks: List[Dict[str, Any]],
    index_name: str = "ehr_chunks"
) -> Dict[str, int]:
    """
    Bulk index EHR chunks into Elasticsearch.
    
    Args:
        es: Elasticsearch client
        chunks: List of chunk dicts with fields:
            - patient_id
            - resource_type
            - resource_id
            - timestamp
            - text
            - metadata
            - embedding
        index_name: Target index name
    
    Returns:
        Dict with success/failed counts
    """
    actions = [
        {
            "_index": index_name,
            "_id": f"{chunk['patient_id']}_{chunk['resource_type']}_{chunk['resource_id']}",
            "_source": chunk
        }
        for chunk in chunks
    ]
    
    success, failed = bulk(es, actions, raise_on_error=False)
    
    return {
        "success": success,
        "failed": len(failed) if failed else 0
    }


def delete_patient_chunks(
    es: Elasticsearch,
    patient_id: str,
    index_name: str = "ehr_chunks"
):
    """Delete all chunks for a patient (for re-indexing)."""
    es.delete_by_query(
        index=index_name,
        body={
            "query": {
                "term": {"patient_id": patient_id}
            }
        }
    )
