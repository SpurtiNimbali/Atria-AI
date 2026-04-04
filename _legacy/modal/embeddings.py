"""
Generate embeddings using Jina AI API.
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
from typing import List, Union, Optional
import httpx


def generate_embeddings(
    texts: Union[str, List[str]],
    model: str = "jina-embeddings-v2-base-en",
    api_key: Optional[str] = None
) -> Union[List[float], List[List[float]]]:
    """
    Generate embeddings using Jina AI API.
    
    Args:
        texts: Single text or list of texts to embed
        model: Jina model name
        api_key: Jina API key (defaults to JINA_API_KEY env var)
    
    Returns:
        Single embedding or list of embeddings
    """
    api_key = api_key or os.getenv("JINA_API_KEY")
    if not api_key:
        raise ValueError("JINA_API_KEY not set")
    
    is_single = isinstance(texts, str)
    if is_single:
        texts = [texts]
    
    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "input": texts
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
    
    embeddings = [item["embedding"] for item in result["data"]]
    
    return embeddings[0] if is_single else embeddings


def generate_embedding(text: str, **kwargs) -> List[float]:
    """Generate single embedding (convenience function)."""
    return generate_embeddings(text, **kwargs)


# Test function
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    test_texts = [
        "Patient has type 2 diabetes",
        "Blood pressure reading: 120/80 mmHg"
    ]
    
    print("Generating embeddings...")
    embeddings = generate_embeddings(test_texts)
    
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    print(f"First few values: {embeddings[0][:5]}")
