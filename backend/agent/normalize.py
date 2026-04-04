"""
Normalize FHIR resources into searchable text chunks.
Each chunk is 1-3 paragraphs with stable IDs and metadata.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


def safe_get(obj: Any, *keys, default=None):
    """Safely navigate nested dict/list structures."""
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list) and isinstance(key, int) and len(current) > key:
            current = current[key]
        else:
            return default
        if current is None:
            return default
    return current


def get_coding_display(coding_list: List[Dict]) -> str:
    """Extract display text from FHIR coding."""
    if not coding_list:
        return ""
    
    displays = []
    for coding in coding_list:
        if coding.get("display"):
            displays.append(coding["display"])
        elif coding.get("code"):
            displays.append(coding["code"])
    
    return ", ".join(displays) if displays else ""


def normalize_patient(patient: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert Patient resource to chunks."""
    patient_id = patient.get("id", "unknown")
    
    # Extract name
    name_parts = []
    if patient.get("name"):
        name = patient["name"][0]
        if name.get("given"):
            name_parts.extend(name["given"])
        if name.get("family"):
            name_parts.append(name["family"])
    
    full_name = " ".join(name_parts) if name_parts else "Unknown"
    
    # Extract demographics
    gender = patient.get("gender", "unknown")
    birth_date = patient.get("birthDate", "unknown")
    
    text = f"Patient: {full_name}\n"
    text += f"Gender: {gender}\n"
    text += f"Date of Birth: {birth_date}\n"
    
    # Add addresses
    if patient.get("address"):
        addr = patient["address"][0]
        text += f"Address: {addr.get('city', '')}, {addr.get('state', '')} {addr.get('postalCode', '')}\n"
    
    # Add contact
    if patient.get("telecom"):
        for telecom in patient["telecom"]:
            system = telecom.get("system", "")
            value = telecom.get("value", "")
            text += f"{system.capitalize()}: {value}\n"
    
    return [{
        "patient_id": patient_id,
        "resource_type": "Patient",
        "resource_id": patient_id,
        "timestamp": datetime.now().isoformat(),
        "text": text.strip(),
        "metadata": {
            "name": full_name,
            "gender": gender,
            "birth_date": birth_date
        }
    }]


def normalize_condition(condition: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
    """Convert Condition resource to chunks."""
    resource_id = condition.get("id", "unknown")
    
    # Get condition name
    code = condition.get("code", {})
    condition_name = get_coding_display(code.get("coding", [])) or code.get("text", "Unknown condition")
    
    # Clinical status
    clinical_status = safe_get(condition, "clinicalStatus", "coding", 0, "code", default="unknown")
    
    # Onset date
    onset = condition.get("onsetDateTime") or condition.get("onsetPeriod", {}).get("start") or "unknown"
    
    # Recorded date
    recorded = condition.get("recordedDate", onset)
    
    # Severity
    severity = ""
    if condition.get("severity"):
        severity_display = get_coding_display(condition["severity"].get("coding", []))
        if severity_display:
            severity = f"Severity: {severity_display}\n"
    
    text = f"Condition: {condition_name}\n"
    text += f"Status: {clinical_status}\n"
    text += f"Onset: {onset}\n"
    if severity:
        text += severity
    
    # Add notes if present
    if condition.get("note"):
        notes = " ".join([note.get("text", "") for note in condition["note"]])
        text += f"Notes: {notes}\n"
    
    return [{
        "patient_id": patient_id,
        "resource_type": "Condition",
        "resource_id": resource_id,
        "timestamp": recorded,
        "text": text.strip(),
        "metadata": {
            "condition_name": condition_name,
            "clinical_status": clinical_status,
            "onset": onset
        }
    }]


def normalize_medication_request(med_req: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
    """Convert MedicationRequest to chunks."""
    resource_id = med_req.get("id", "unknown")
    
    # Get medication name
    medication = med_req.get("medicationCodeableConcept", {})
    med_name = get_coding_display(medication.get("coding", [])) or medication.get("text", "Unknown medication")
    
    # Status
    status = med_req.get("status", "unknown")
    
    # Dosage
    dosage_text = ""
    if med_req.get("dosageInstruction"):
        dosage = med_req["dosageInstruction"][0]
        dosage_text = dosage.get("text", "")
        if not dosage_text and dosage.get("doseAndRate"):
            dose = safe_get(dosage, "doseAndRate", 0, "doseQuantity")
            if dose:
                dosage_text = f"{dose.get('value', '')} {dose.get('unit', '')}"
    
    # Authored date
    authored = med_req.get("authoredOn", datetime.now().isoformat())
    
    text = f"Medication: {med_name}\n"
    text += f"Status: {status}\n"
    if dosage_text:
        text += f"Dosage: {dosage_text}\n"
    text += f"Prescribed: {authored}\n"
    
    # Reason
    if med_req.get("reasonCode"):
        reason = get_coding_display(med_req["reasonCode"][0].get("coding", []))
        if reason:
            text += f"Reason: {reason}\n"
    
    return [{
        "patient_id": patient_id,
        "resource_type": "MedicationRequest",
        "resource_id": resource_id,
        "timestamp": authored,
        "text": text.strip(),
        "metadata": {
            "medication_name": med_name,
            "status": status,
            "dosage": dosage_text
        }
    }]


def normalize_allergy(allergy: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
    """Convert AllergyIntolerance to chunks."""
    resource_id = allergy.get("id", "unknown")
    
    # Get allergen
    code = allergy.get("code", {})
    allergen = get_coding_display(code.get("coding", [])) or code.get("text", "Unknown allergen")
    
    # Clinical status
    clinical_status = safe_get(allergy, "clinicalStatus", "coding", 0, "code", default="active")
    
    # Criticality
    criticality = allergy.get("criticality", "unknown")
    
    # Type
    allergy_type = allergy.get("type", "allergy")
    
    # Recorded date
    recorded = allergy.get("recordedDate", datetime.now().isoformat())
    
    text = f"Allergy: {allergen}\n"
    text += f"Type: {allergy_type}\n"
    text += f"Criticality: {criticality}\n"
    text += f"Status: {clinical_status}\n"
    
    # Reactions
    if allergy.get("reaction"):
        reactions = []
        for reaction in allergy["reaction"]:
            manifestations = reaction.get("manifestation", [])
            for manifest in manifestations:
                display = get_coding_display(manifest.get("coding", []))
                if display:
                    reactions.append(display)
        if reactions:
            text += f"Reactions: {', '.join(reactions)}\n"
    
    return [{
        "patient_id": patient_id,
        "resource_type": "AllergyIntolerance",
        "resource_id": resource_id,
        "timestamp": recorded,
        "text": text.strip(),
        "metadata": {
            "allergen": allergen,
            "criticality": criticality,
            "type": allergy_type
        }
    }]


def normalize_observation(obs: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
    """Convert Observation to chunks."""
    resource_id = obs.get("id", "unknown")
    
    # Get observation name
    code = obs.get("code", {})
    obs_name = get_coding_display(code.get("coding", [])) or code.get("text", "Unknown observation")
    
    # Get value - handle both simple values and component values
    value_str = ""
    if obs.get("valueQuantity"):
        val = obs["valueQuantity"]
        value_str = f"{val.get('value', '')} {val.get('unit', '')}"
    elif obs.get("valueString"):
        value_str = obs["valueString"]
    elif obs.get("valueCodeableConcept"):
        value_str = get_coding_display(obs["valueCodeableConcept"].get("coding", []))
    elif obs.get("component"):
        # Handle component observations (e.g., blood pressure)
        component_values = []
        for component in obs["component"]:
            comp_code = component.get("code", {})
            comp_name = get_coding_display(comp_code.get("coding", [])) or comp_code.get("text", "")
            if component.get("valueQuantity"):
                comp_val = component["valueQuantity"]
                comp_value_str = f"{comp_val.get('value', '')} {comp_val.get('unit', '')}"
                component_values.append(f"{comp_name}: {comp_value_str}")
        value_str = ", ".join(component_values)
    
    # Effective date
    effective = obs.get("effectiveDateTime") or obs.get("effectivePeriod", {}).get("start") or datetime.now().isoformat()
    
    # Status
    status = obs.get("status", "final")
    
    text = f"Observation: {obs_name}\n"
    if value_str:
        text += f"Value: {value_str}\n"
    text += f"Date: {effective}\n"
    text += f"Status: {status}\n"
    
    # Interpretation
    if obs.get("interpretation"):
        interp = get_coding_display(obs["interpretation"][0].get("coding", []))
        if interp:
            text += f"Interpretation: {interp}\n"
    
    # Category
    category = ""
    if obs.get("category"):
        category = get_coding_display(obs["category"][0].get("coding", []))
    
    return [{
        "patient_id": patient_id,
        "resource_type": "Observation",
        "resource_id": resource_id,
        "timestamp": effective,
        "text": text.strip(),
        "metadata": {
            "observation_name": obs_name,
            "value": value_str,
            "category": category
        }
    }]


def normalize_encounter(encounter: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
    """Convert Encounter to chunks."""
    resource_id = encounter.get("id", "unknown")
    
    # Type
    enc_type = ""
    if encounter.get("type"):
        enc_type = get_coding_display(encounter["type"][0].get("coding", []))
    
    # Status
    status = encounter.get("status", "unknown")
    
    # Class
    enc_class = safe_get(encounter, "class", "display", default="unknown")
    
    # Period
    period = encounter.get("period", {})
    start = period.get("start", "unknown")
    end = period.get("end", "ongoing")
    
    text = f"Encounter: {enc_type or enc_class}\n"
    text += f"Status: {status}\n"
    text += f"Start: {start}\n"
    text += f"End: {end}\n"
    
    # Reason
    if encounter.get("reasonCode"):
        reason = get_coding_display(encounter["reasonCode"][0].get("coding", []))
        if reason:
            text += f"Reason: {reason}\n"
    
    return [{
        "patient_id": patient_id,
        "resource_type": "Encounter",
        "resource_id": resource_id,
        "timestamp": start,
        "text": text.strip(),
        "metadata": {
            "type": enc_type or enc_class,
            "status": status,
            "start": start
        }
    }]


def normalize_procedure(procedure: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
    """Convert Procedure to chunks."""
    resource_id = procedure.get("id", "unknown")
    
    # Get procedure name
    code = procedure.get("code", {})
    proc_name = get_coding_display(code.get("coding", [])) or code.get("text", "Unknown procedure")
    
    # Status
    status = procedure.get("status", "unknown")
    
    # Performed date
    performed = procedure.get("performedDateTime") or \
                safe_get(procedure, "performedPeriod", "start") or \
                datetime.now().isoformat()
    
    text = f"Procedure: {proc_name}\n"
    text += f"Status: {status}\n"
    text += f"Performed: {performed}\n"
    
    # Reason
    if procedure.get("reasonCode"):
        reason = get_coding_display(procedure["reasonCode"][0].get("coding", []))
        if reason:
            text += f"Reason: {reason}\n"
    
    # Outcome
    if procedure.get("outcome"):
        outcome = get_coding_display(procedure["outcome"].get("coding", []))
        if outcome:
            text += f"Outcome: {outcome}\n"
    
    return [{
        "patient_id": patient_id,
        "resource_type": "Procedure",
        "resource_id": resource_id,
        "timestamp": performed,
        "text": text.strip(),
        "metadata": {
            "procedure_name": proc_name,
            "status": status,
            "performed": performed
        }
    }]


def normalize_coverage(coverage: Dict[str, Any], patient_id: str) -> List[Dict[str, Any]]:
    """Convert Coverage resource (insurance) to chunks."""
    resource_id = coverage.get("id", "unknown")
    
    # Extract status
    status = coverage.get("status", "unknown")
    
    # Extract payor info
    payors = coverage.get("payor", [])
    payor_names = []
    for payor in payors:
        if payor.get("display"):
            payor_names.append(payor["display"])
        elif payor.get("reference"):
            payor_names.append(payor["reference"])
    payor_text = ", ".join(payor_names) if payor_names else "Unknown payor"
    
    # Extract coverage type
    coverage_type = safe_get(coverage, "type", "text", default="")
    if not coverage_type and coverage.get("type", {}).get("coding"):
        coverage_type = get_coding_display(coverage["type"]["coding"])
    
    # Extract subscriber info if present
    subscriber_id = safe_get(coverage, "subscriberId", default="")
    
    # Extract period if present
    period_start = safe_get(coverage, "period", "start", default="")
    period_end = safe_get(coverage, "period", "end", default="")
    
    # Build text
    text = f"Insurance Coverage: {payor_text}"
    if coverage_type:
        text += f"\nCoverage Type: {coverage_type}"
    if status:
        text += f"\nStatus: {status}"
    if subscriber_id:
        text += f"\nSubscriber ID: {subscriber_id}"
    if period_start:
        text += f"\nEffective from: {period_start}"
    if period_end:
        text += f" to {period_end}"
    
    return [{
        "chunk_id": f"coverage-{resource_id}",
        "patient_id": patient_id,
        "resource_type": "Coverage",
        "resource_id": resource_id,
        "timestamp": period_start or datetime.now().isoformat(),
        "text": text.strip(),
        "metadata": {
            "payor": payor_text,
            "coverage_type": coverage_type,
            "status": status,
            "subscriber_id": subscriber_id
        }
    }]


def normalize_fhir_data(fhir_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize all FHIR resources into searchable chunks.
    
    Args:
        fhir_data: Dict with keys like 'patient', 'conditions', 'medication_requests', etc.
    
    Returns:
        List of normalized chunks ready for indexing
    """
    chunks = []
    
    # Get patient ID
    patient = fhir_data.get("patient", {})
    patient_id = patient.get("id", "unknown")
    
    # Normalize patient
    if patient:
        chunks.extend(normalize_patient(patient))
    
    # Normalize conditions
    for condition in fhir_data.get("conditions", []):
        chunks.extend(normalize_condition(condition, patient_id))
    
    # Normalize medications
    for med_req in fhir_data.get("medication_requests", []):
        chunks.extend(normalize_medication_request(med_req, patient_id))
    
    for med_stmt in fhir_data.get("medication_statements", []):
        chunks.extend(normalize_medication_request(med_stmt, patient_id))
    
    # Normalize allergies
    for allergy in fhir_data.get("allergies", []):
        chunks.extend(normalize_allergy(allergy, patient_id))
    
    # Normalize observations
    for obs in fhir_data.get("vital_signs", []):
        chunks.extend(normalize_observation(obs, patient_id))
    
    for obs in fhir_data.get("lab_results", []):
        chunks.extend(normalize_observation(obs, patient_id))
    
    # Normalize encounters
    for encounter in fhir_data.get("encounters", []):
        chunks.extend(normalize_encounter(encounter, patient_id))
    
    # Normalize procedures
    for procedure in fhir_data.get("procedures", []):
        chunks.extend(normalize_procedure(procedure, patient_id))
    
    # Normalize coverage (insurance)
    for coverage in fhir_data.get("coverage", []):
        chunks.extend(normalize_coverage(coverage, patient_id))
    
    print(f"Normalized {len(chunks)} chunks from FHIR data")
    
    return chunks


# Test function
if __name__ == "__main__":
    from dotenv import load_dotenv
    from fhir_client import FHIRClient
    
    load_dotenv()
    
    client = FHIRClient()
    patient_id = "example"
    
    print(f"Fetching and normalizing data for patient: {patient_id}\n")
    
    fhir_data = client.get_all_patient_data(patient_id)
    chunks = normalize_fhir_data(fhir_data)
    
    print(f"\n=== Sample Chunks ===\n")
    for i, chunk in enumerate(chunks[:5], 1):
        print(f"{i}. {chunk['resource_type']} ({chunk['timestamp']})")
        print(f"   {chunk['text'][:150]}...")
        print()
