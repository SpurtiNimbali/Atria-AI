"""
FHIR client for pulling patient resources from EHR.
Supports public FHIR servers and Bearer token authentication.
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
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime


class FHIRClient:
    """Client for interacting with FHIR servers."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30
    ):
        self.base_url = base_url or os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4")
        self.token = token or os.getenv("FHIR_TOKEN")
        self.timeout = timeout
        
        # Remove trailing slash
        self.base_url = self.base_url.rstrip("/")
        
        # Setup headers
        self.headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json"
        }
        
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    def _get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to FHIR server."""
        url = f"{self.base_url}/{path}"
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=self.headers, params=params or {})
            response.raise_for_status()
            return response.json()
    
    def _get_all_pages(self, path: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Get all resources from a paginated FHIR bundle.
        Follows 'next' links to retrieve all pages.
        """
        all_entries = []
        
        bundle = self._get(path, params)
        
        # Extract entries from first page
        if bundle.get("entry"):
            all_entries.extend(bundle["entry"])
        
        # Follow pagination links
        while bundle.get("link"):
            next_link = None
            for link in bundle["link"]:
                if link.get("relation") == "next":
                    next_link = link.get("url")
                    break
            
            if not next_link:
                break
            
            # Fetch next page
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(next_link, headers=self.headers)
                response.raise_for_status()
                bundle = response.json()
                
                if bundle.get("entry"):
                    all_entries.extend(bundle["entry"])
        
        return all_entries
    
    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        """Get Patient resource."""
        return self._get(f"Patient/{patient_id}")
    
    def get_conditions(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all Condition resources for a patient."""
        entries = self._get_all_pages(
            "Condition",
            params={"patient": patient_id, "_count": 100}
        )
        return [entry["resource"] for entry in entries if entry.get("resource")]
    
    def get_medication_requests(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all MedicationRequest resources for a patient."""
        entries = self._get_all_pages(
            "MedicationRequest",
            params={"patient": patient_id, "_count": 100}
        )
        return [entry["resource"] for entry in entries if entry.get("resource")]
    
    def get_medication_statements(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all MedicationStatement resources for a patient."""
        try:
            entries = self._get_all_pages(
                "MedicationStatement",
                params={"patient": patient_id, "_count": 100}
            )
            return [entry["resource"] for entry in entries if entry.get("resource")]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []  # Not all servers support MedicationStatement
            raise
    
    def get_allergies(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all AllergyIntolerance resources for a patient."""
        entries = self._get_all_pages(
            "AllergyIntolerance",
            params={"patient": patient_id, "_count": 100}
        )
        return [entry["resource"] for entry in entries if entry.get("resource")]
    
    def get_observations(
        self,
        patient_id: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get Observation resources for a patient.
        
        Args:
            patient_id: Patient ID
            category: Optional category filter (e.g., 'vital-signs', 'laboratory')
        """
        params = {"patient": patient_id, "_count": 100, "_sort": "-date"}
        
        if category:
            params["category"] = category
        
        entries = self._get_all_pages("Observation", params=params)
        return [entry["resource"] for entry in entries if entry.get("resource")]
    
    def get_encounters(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all Encounter resources for a patient."""
        entries = self._get_all_pages(
            "Encounter",
            params={"patient": patient_id, "_count": 100, "_sort": "-date"}
        )
        return [entry["resource"] for entry in entries if entry.get("resource")]
    
    def get_procedures(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all Procedure resources for a patient."""
        entries = self._get_all_pages(
            "Procedure",
            params={"patient": patient_id, "_count": 100, "_sort": "-date"}
        )
        return [entry["resource"] for entry in entries if entry.get("resource")]
    
    def get_coverage(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all Coverage resources (insurance) for a patient."""
        entries = self._get_all_pages(
            "Coverage",
            params={"patient": patient_id, "_count": 100}
        )
        return [entry["resource"] for entry in entries if entry.get("resource")]
    
    def get_all_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Pull all relevant FHIR resources for a patient.
        
        Returns a dict with resource types as keys.
        """
        print(f"Fetching FHIR data for patient: {patient_id}")
        
        data = {
            "patient": self.get_patient(patient_id),
            "conditions": self.get_conditions(patient_id),
            "medication_requests": self.get_medication_requests(patient_id),
            "medication_statements": self.get_medication_statements(patient_id),
            "allergies": self.get_allergies(patient_id),
            "vital_signs": self.get_observations(patient_id, category="vital-signs"),
            "lab_results": self.get_observations(patient_id, category="laboratory"),
            "encounters": self.get_encounters(patient_id),
            "procedures": self.get_procedures(patient_id),
            "coverage": self.get_coverage(patient_id)
        }
        
        # Print summary
        print(f"Retrieved:")
        for resource_type, resources in data.items():
            if resource_type == "patient":
                print(f"  - Patient: 1 resource")
            else:
                count = len(resources) if isinstance(resources, list) else 0
                print(f"  - {resource_type}: {count} resources")
        
        return data


# Test function
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    client = FHIRClient()
    
    # Test with example patient
    patient_id = "example"
    print(f"\nTesting FHIR client with patient: {patient_id}\n")
    
    try:
        data = client.get_all_patient_data(patient_id)
        print(f"\n✓ Successfully retrieved patient data")
    except Exception as e:
        print(f"\n✗ Error: {e}")
