"""
SMART on FHIR OAuth2 authentication support.
Implements authorization code flow for EHR access.
"""
import os
from typing import Dict, Any, Optional
import httpx
from urllib.parse import urlencode


class SMARTFHIRClient:
    """
    SMART on FHIR client with OAuth2 support.
    
    For hackathon/demo purposes, we'll use a public FHIR sandbox.
    For production, implement full OAuth2 flow.
    """
    
    def __init__(
        self,
        fhir_base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        self.fhir_base_url = fhir_base_url or os.getenv("FHIR_BASE_URL")
        self.client_id = client_id or os.getenv("FHIR_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("FHIR_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("FHIR_REDIRECT_URI", "http://localhost:3000/callback")
        
        self.access_token: Optional[str] = None
        self.token_type: str = "Bearer"
        
        # Discover SMART configuration
        self.smart_config = self._discover_smart_config()
    
    def _discover_smart_config(self) -> Dict[str, Any]:
        """
        Discover SMART on FHIR configuration from .well-known endpoint.
        
        Returns authorization and token endpoints.
        """
        if not self.fhir_base_url:
            return {}
        
        try:
            well_known_url = f"{self.fhir_base_url.rstrip('/')}/.well-known/smart-configuration"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(well_known_url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Could not discover SMART config: {e}")
            return {}
    
    def get_authorization_url(self, scope: str = "patient/*.read launch/patient") -> str:
        """
        Generate OAuth2 authorization URL.
        
        Args:
            scope: SMART scopes (e.g., "patient/*.read launch/patient")
        
        Returns:
            Authorization URL to redirect user to
        """
        if not self.smart_config.get("authorization_endpoint"):
            raise ValueError("No authorization endpoint found in SMART config")
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": "random_state_string",  # In production, use secure random
            "aud": self.fhir_base_url
        }
        
        auth_url = f"{self.smart_config['authorization_endpoint']}?{urlencode(params)}"
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth2 callback
        
        Returns:
            Token response with access_token, patient, etc.
        """
        if not self.smart_config.get("token_endpoint"):
            raise ValueError("No token endpoint found in SMART config")
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id
        }
        
        # Add client_secret if using confidential client
        if self.client_secret:
            token_data["client_secret"] = self.client_secret
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                self.smart_config["token_endpoint"],
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            token_response = response.json()
        
        # Store access token
        self.access_token = token_response.get("access_token")
        self.token_type = token_response.get("token_type", "Bearer")
        
        return token_response
    
    def get_patient_from_token(self, token_response: Dict[str, Any]) -> Optional[str]:
        """
        Extract patient ID from token response.
        
        SMART on FHIR includes patient context in token response.
        """
        return token_response.get("patient")


# Public FHIR Sandboxes (no auth required)
PUBLIC_FHIR_SERVERS = {
    "hapi": {
        "name": "HAPI FHIR Public Server",
        "base_url": "https://hapi.fhir.org/baseR4",
        "auth_required": False,
        "demo_patients": ["example", "smart-1032702"]
    },
    "smart_health_it": {
        "name": "SMART Health IT Sandbox",
        "base_url": "https://launch.smarthealthit.org/v/r4/fhir",
        "auth_required": True,
        "demo_patients": ["smart-1032702", "smart-1137192"]
    }
}


def get_public_fhir_client(server: str = "hapi"):
    """
    Get a pre-configured client for public FHIR servers.
    
    Args:
        server: Server key from PUBLIC_FHIR_SERVERS
    
    Returns:
        FHIRClient configured for the server
    """
    from fhir_client import FHIRClient
    
    if server not in PUBLIC_FHIR_SERVERS:
        raise ValueError(f"Unknown server: {server}. Available: {list(PUBLIC_FHIR_SERVERS.keys())}")
    
    config = PUBLIC_FHIR_SERVERS[server]
    
    return FHIRClient(base_url=config["base_url"])


# Test function
if __name__ == "__main__":
    print("=== Public FHIR Servers ===\n")
    
    for key, config in PUBLIC_FHIR_SERVERS.items():
        print(f"{config['name']}")
        print(f"  URL: {config['base_url']}")
        print(f"  Auth: {'Required' if config['auth_required'] else 'Not required'}")
        print(f"  Demo patients: {', '.join(config['demo_patients'])}")
        print()
    
    print("\n=== Testing HAPI FHIR ===\n")
    
    client = get_public_fhir_client("hapi")
    try:
        patient = client.get_patient("example")
        print(f"✓ Successfully fetched patient: {patient.get('id')}")
    except Exception as e:
        print(f"✗ Error: {e}")
