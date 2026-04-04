"""
EHR Document Parser - Extracts structured data from FHIR documents in Elasticsearch
"""

import re
from typing import Dict, Any, List
from datetime import datetime
from elastic_client import get_elastic_client


def get_patient_medications(patient_id: str) -> List[Dict[str, Any]]:
    """Extract all medications for a patient from EHR."""
    es = get_elastic_client()
    
    results = es.search(
        index="ehr_chunks",
        body={
            "query": {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_id}},
                        {"term": {"resource_type": "MedicationRequest"}}
                    ]
                }
            },
            "size": 50
        }
    )
    
    medications = []
    for hit in results['hits']['hits']:
        text = hit['_source']['text']
        
        # Parse medication name
        med_match = re.search(r'Medication:\s*([^\n]+)', text)
        if med_match:
            med_name = med_match.group(1).strip()
            
            # Parse dosage
            dosage_match = re.search(r'Dosage:\s*([^\n]+)', text)
            dosage = dosage_match.group(1).strip() if dosage_match else "Unknown"
            
            # Parse status
            status_match = re.search(r'Status:\s*([^\n]+)', text)
            status = status_match.group(1).strip() if status_match else "unknown"
            
            if status == "active":
                medications.append({
                    "name": med_name,
                    "dosage": dosage,
                    "status": status
                })
    
    return medications


def get_patient_conditions(patient_id: str) -> List[Dict[str, Any]]:
    """Extract all conditions/diagnoses for a patient."""
    es = get_elastic_client()
    
    results = es.search(
        index="ehr_chunks",
        body={
            "query": {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_id}},
                        {"term": {"resource_type": "Condition"}}
                    ]
                }
            },
            "size": 50
        }
    )
    
    conditions = []
    for hit in results['hits']['hits']:
        text = hit['_source']['text']
        
        # Parse condition name
        cond_match = re.search(r'Condition:\s*([^\n]+)', text)
        if cond_match:
            condition_name = cond_match.group(1).strip()
            
            # Parse status
            status_match = re.search(r'Status:\s*([^\n]+)', text)
            status = status_match.group(1).strip() if status_match else "unknown"
            
            # Parse onset date
            onset_match = re.search(r'Onset:\s*([^\n]+)', text)
            onset = onset_match.group(1).strip() if onset_match else "Unknown"
            
            if status == "active":
                conditions.append({
                    "name": condition_name,
                    "status": status,
                    "onset": onset
                })
    
    return conditions


def get_patient_labs(patient_id: str, lab_name: str = None) -> List[Dict[str, Any]]:
    """Extract lab results (Observations) for a patient."""
    es = get_elastic_client()
    
    results = es.search(
        index="ehr_chunks",
        body={
            "query": {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_id}},
                        {"term": {"resource_type": "Observation"}}
                    ]
                }
            },
            "size": 100,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
    )
    
    labs = []
    for hit in results['hits']['hits']:
        text = hit['_source']['text']
        timestamp = hit['_source'].get('timestamp', '')
        
        # Parse observation name
        obs_match = re.search(r'Observation:\s*([^\n]+)', text)
        if not obs_match:
            continue
        
        obs_name = obs_match.group(1).strip()
        
        # If filtering by lab name, skip if doesn't match
        if lab_name and lab_name.lower() not in obs_name.lower():
            continue
        
        # Parse value
        value_match = re.search(r'Value:\s*([^\n]+)', text)
        value_text = value_match.group(1).strip() if value_match else "Unknown"
        
        # Parse date
        date_match = re.search(r'Date:\s*([^\n]+)', text)
        date_str = date_match.group(1).strip() if date_match else timestamp
        
        # Try to extract numeric value
        numeric_match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z/%]+)', value_text)
        
        lab_entry = {
            "name": obs_name,
            "value_text": value_text,
            "date": date_str,
            "timestamp": timestamp
        }
        
        if numeric_match:
            lab_entry["value"] = float(numeric_match.group(1))
            lab_entry["unit"] = numeric_match.group(2)
        
        labs.append(lab_entry)
    
    return labs


def get_patient_demographics(patient_id: str) -> Dict[str, Any]:
    """Extract patient demographics."""
    es = get_elastic_client()
    
    results = es.search(
        index="ehr_chunks",
        body={
            "query": {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_id}},
                        {"term": {"resource_type": "Patient"}}
                    ]
                }
            },
            "size": 1
        }
    )
    
    if not results['hits']['hits']:
        return {}
    
    text = results['hits']['hits'][0]['_source']['text']
    
    # Parse name
    name_match = re.search(r'Patient:\s*([^\n]+)', text)
    name = name_match.group(1).strip() if name_match else "Unknown"
    
    # Parse gender
    gender_match = re.search(r'Gender:\s*([^\n]+)', text)
    gender = gender_match.group(1).strip() if gender_match else "unknown"
    
    # Parse DOB
    dob_match = re.search(r'Date of Birth:\s*([^\n]+)', text)
    dob = dob_match.group(1).strip() if dob_match else "Unknown"
    
    # Calculate age
    age = None
    if dob != "Unknown":
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            age = (datetime.now() - dob_date).days // 365
        except:
            pass
    
    return {
        "name": name,
        "gender": gender,
        "date_of_birth": dob,
        "age": age
    }


def get_comprehensive_patient_summary(patient_id: str) -> Dict[str, Any]:
    """Get a comprehensive summary of all patient data."""
    return {
        "demographics": get_patient_demographics(patient_id),
        "medications": get_patient_medications(patient_id),
        "conditions": get_patient_conditions(patient_id),
        "recent_labs": get_patient_labs(patient_id)
    }


def get_dashboard_data(patient_id: str) -> Dict[str, Any]:
    """
    Get comprehensive dashboard data from Elasticsearch.
    Extracts all patient information needed for the dashboard.
    """
    es = get_elastic_client()
    
    # Get all chunks for this patient
    results = es.search(
        index="ehr_chunks",
        body={
            "query": {"term": {"patient_id": patient_id}},
            "size": 1000,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
    )
    
    chunks = [hit["_source"] for hit in results["hits"]["hits"]]
    
    # Initialize dashboard structure
    dashboard = {
        "patient": {},
        "encounter": {},
        "timeline": [],
        "vitals": [],
        "labs": [],
        "medications": [],
        "transfusion": [],
        "allergies": [],
        "problems": [],
        "discharge_instructions": {},
        "education": [],
        "risk_factors": [],
        "confidence": {},
        "citations": []
    }
    
    # Parse chunks by resource type
    for chunk in chunks:
        resource_type = chunk.get("resource_type", "")
        text = chunk.get("text", "")
        timestamp = chunk.get("timestamp", "")
        
        # PATIENT
        if resource_type == "Patient":
            name_match = re.search(r'Patient:\s*([^\n]+)', text)
            gender_match = re.search(r'Gender:\s*([^\n]+)', text)
            dob_match = re.search(r'Date of Birth:\s*([^\n]+)', text)
            
            dashboard["patient"] = {
                "name": name_match.group(1).strip() if name_match else "Unknown",
                "mrn": patient_id,
                "dob": dob_match.group(1).strip() if dob_match else "Unknown",
                "sex": gender_match.group(1).strip() if gender_match else "Unknown",
                "language_pref": "English"  # Default, can be extracted if in data
            }
        
        # ENCOUNTER
        elif resource_type == "Encounter":
            admit_match = re.search(r'Admission|Start[:\s]+([^\n]+)', text, re.IGNORECASE)
            discharge_match = re.search(r'Discharge|End[:\s]+([^\n]+)', text, re.IGNORECASE)
            status_match = re.search(r'Status[:\s]+([^\n]+)', text, re.IGNORECASE)
            
            if not dashboard["encounter"]:
                dashboard["encounter"] = {
                    "admit_at": admit_match.group(1).strip() if admit_match else timestamp,
                    "discharge_at": discharge_match.group(1).strip() if discharge_match else None,
                    "unit": "Medical Unit",  # Extract if available
                    "attending": "Dr. Smith",  # Extract if available
                    "status": status_match.group(1).strip() if status_match else "active"
                }
        
        # VITALS (Observations with vital-signs category)
        elif resource_type == "Observation" and ("vital" in text.lower() or "blood pressure" in text.lower() or "heart rate" in text.lower() or "temperature" in text.lower() or "spo2" in text.lower()):
            # Heart Rate
            hr_match = re.search(r'Heart Rate|HR[:\s]+(\d+)', text, re.IGNORECASE)
            if hr_match:
                dashboard["vitals"].append({
                    "type": "HR",
                    "value": hr_match.group(1),
                    "unit": "bpm",
                    "taken_at": timestamp,
                    "device_id": "monitor-001",
                    "quality_flags": "good"
                })
            
            # Blood Pressure
            if re.search(r'Blood [Pp]ressure|BP', text, re.IGNORECASE):
                # Try to extract from "Systolic blood pressure: 88 mmHg, Diastolic blood pressure: 54 mmHg"
                systolic_match = re.search(r'[Ss]ystolic.*?:\s*(\d+)', text)
                diastolic_match = re.search(r'[Dd]iastolic.*?:\s*(\d+)', text)
                
                if systolic_match and diastolic_match:
                    systolic = systolic_match.group(1)
                    diastolic = diastolic_match.group(1)
                    dashboard["vitals"].append({
                        "type": "BP",
                        "value": f"{systolic}/{diastolic}",
                        "unit": "mmHg",
                        "taken_at": timestamp,
                        "device_id": "monitor-001",
                        "quality_flags": "good"
                    })
            
            # SpO2
            spo2_match = re.search(r'SpO2|Oxygen[:\s]+(\d+)', text, re.IGNORECASE)
            if spo2_match:
                dashboard["vitals"].append({
                    "type": "SpO2",
                    "value": spo2_match.group(1),
                    "unit": "%",
                    "taken_at": timestamp,
                    "device_id": "monitor-001",
                    "quality_flags": "good"
                })
            
            # Temperature
            temp_match = re.search(r'Temperature|Temp[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
            if temp_match:
                dashboard["vitals"].append({
                    "type": "Temp",
                    "value": temp_match.group(1),
                    "unit": "°F",
                    "taken_at": timestamp,
                    "device_id": "thermometer-001",
                    "quality_flags": "good"
                })
        
        # LABS (Observations with laboratory category)
        elif resource_type == "Observation" and ("lab" in text.lower() or "hemoglobin" in text.lower() or "hgb" in text.lower() or "hematocrit" in text.lower() or "hct" in text.lower() or "platelet" in text.lower() or "wbc" in text.lower() or "ferritin" in text.lower() or "inr" in text.lower() or "pt" in text.lower() or "aptt" in text.lower()):
            obs_match = re.search(r'Observation:\s*([^\n]+)', text)
            value_match = re.search(r'Value:\s*([^\n]+)', text)
            
            if obs_match:
                test_name = obs_match.group(1).strip()
                value_text = value_match.group(1).strip() if value_match else "Unknown"
                
                # Extract numeric value and unit
                numeric_match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z/%]+)?', value_text)
                
                lab_entry = {
                    "test_name": test_name,
                    "value": numeric_match.group(1) if numeric_match else value_text,
                    "unit": numeric_match.group(2) if numeric_match and numeric_match.group(2) else "",
                    "collected_at": timestamp
                }
                
                dashboard["labs"].append(lab_entry)
        
        # MEDICATIONS
        elif resource_type in ["MedicationRequest", "MedicationStatement"]:
            med_match = re.search(r'Medication:\s*([^\n]+)', text)
            dosage_match = re.search(r'Dosage|Dose[:\s]+([^\n]+)', text, re.IGNORECASE)
            status_match = re.search(r'Status[:\s]+([^\n]+)', text, re.IGNORECASE)
            
            if med_match and med_match.group(1):
                status = status_match.group(1).strip().lower() if status_match and status_match.group(1) else "unknown"
                if status == "active":
                    dashboard["medications"].append({
                        "name": med_match.group(1).strip(),
                        "dose": dosage_match.group(1).strip() if dosage_match and dosage_match.group(1) else "Unknown",
                        "frequency": "BID",  # Extract if available
                        "start_at": timestamp,
                        "end_at": None,
                        "active_flag": True
                    })
        
        # ALLERGIES
        elif resource_type == "AllergyIntolerance":
            substance_match = re.search(r'Allergy|Substance[:\s]+([^\n]+)', text, re.IGNORECASE)
            reaction_match = re.search(r'Reaction|Manifestation[:\s]+([^\n]+)', text, re.IGNORECASE)
            severity_match = re.search(r'Severity|Criticality[:\s]+([^\n]+)', text, re.IGNORECASE)
            
            if substance_match and substance_match.group(1):
                dashboard["allergies"].append({
                    "substance": substance_match.group(1).strip(),
                    "reaction": reaction_match.group(1).strip() if reaction_match and reaction_match.group(1) else "Unknown",
                    "severity": severity_match.group(1).strip() if severity_match and severity_match.group(1) else "Unknown"
                })
        
        # CONDITIONS/PROBLEMS
        elif resource_type == "Condition":
            cond_match = re.search(r'Condition:\s*([^\n]+)', text)
            status_match = re.search(r'Status[:\s]+([^\n]+)', text)
            
            if cond_match and cond_match.group(1):
                status = status_match.group(1).strip().lower() if status_match and status_match.group(1) else "unknown"
                if status == "active":
                    dashboard["problems"].append({
                        "description": cond_match.group(1).strip()
                    })
        
        # TIMELINE EVENTS (from various resource types)
        if resource_type == "Encounter":
            encounter_type = re.search(r'Encounter[:\s]+([^\n]+)', text, re.IGNORECASE)
            status = re.search(r'Status[:\s]+([^\n]+)', text, re.IGNORECASE)
            summary = encounter_type.group(1).strip() if encounter_type and encounter_type.group(1) else "Encounter"
            if status and status.group(1):
                summary += f"\nStatus: {status.group(1).strip()}"
            
            dashboard["timeline"].append({
                "category": "encounter",
                "action": "admitted",
                "timestamp": timestamp,
                "title": "Encounter",
                "summary": summary[:200]
            })
        
        elif resource_type == "Procedure":
            proc_match = re.search(r'Procedure[:\s]+([^\n]+)', text, re.IGNORECASE)
            date_match = re.search(r'Performed|Date[:\s]+([^\n]+)', text, re.IGNORECASE)
            summary = proc_match.group(1).strip() if proc_match and proc_match.group(1) else "Procedure Completed"
            if date_match and date_match.group(1):
                summary += f"\nDate: {date_match.group(1).strip()}"
            
            dashboard["timeline"].append({
                "category": "procedure",
                "action": "completed",
                "timestamp": timestamp,
                "title": "Procedure",
                "summary": summary[:200]
            })
        
        elif resource_type == "MedicationRequest":
            med_match = re.search(r'Medication[:\s]+([^\n]+)', text, re.IGNORECASE)
            dose_match = re.search(r'Dosage|Dose[:\s]+([^\n]+)', text, re.IGNORECASE)
            status_match = re.search(r'Status[:\s]+([^\n]+)', text, re.IGNORECASE)
            
            if med_match and med_match.group(1):
                summary = med_match.group(1).strip()
                if dose_match and dose_match.group(1):
                    summary += f"\nDose: {dose_match.group(1).strip()}"
                if status_match and status_match.group(1):
                    summary += f"\nStatus: {status_match.group(1).strip()}"
                
                dashboard["timeline"].append({
                    "category": "medication",
                    "action": "prescribed",
                    "timestamp": timestamp,
                    "title": "Medication Prescribed",
                    "summary": summary[:200]
                })
        
        elif resource_type == "Condition":
            cond_match = re.search(r'Condition[:\s]+([^\n]+)', text, re.IGNORECASE)
            status_match = re.search(r'Status[:\s]+([^\n]+)', text, re.IGNORECASE)
            onset_match = re.search(r'Onset[:\s]+([^\n]+)', text, re.IGNORECASE)
            
            if cond_match and cond_match.group(1):
                summary = cond_match.group(1).strip()
                if status_match and status_match.group(1):
                    summary += f"\nStatus: {status_match.group(1).strip()}"
                if onset_match and onset_match.group(1):
                    summary += f"\nOnset: {onset_match.group(1).strip()}"
                
                dashboard["timeline"].append({
                    "category": "diagnosis",
                    "action": "diagnosed",
                    "timestamp": timestamp,
                    "title": "Diagnosis",
                    "summary": summary[:200]
                })
        
        elif resource_type == "Coverage":
            payor_match = re.search(r'(Insurance|Coverage|Payor)[:\s]+([^\n]+)', text, re.IGNORECASE)
            type_match = re.search(r'(Coverage Type|Type)[:\s]+([^\n]+)', text, re.IGNORECASE)
            
            if payor_match and payor_match.group(2):
                summary = payor_match.group(2).strip()
                if type_match and type_match.group(2):
                    summary += f"\nType: {type_match.group(2).strip()}"
                
                dashboard["timeline"].append({
                    "category": "administrative",
                    "action": "coverage_verified",
                    "timestamp": timestamp,
                    "title": "Insurance Verified",
                    "summary": summary[:200]
                })
        
        elif resource_type == "Observation":
            obs_match = re.search(r'Observation[:\s]+([^\n]+)', text, re.IGNORECASE)
            value_match = re.search(r'Value[:\s]+([^\n]+)', text, re.IGNORECASE)
            
            if obs_match and obs_match.group(1):
                summary = obs_match.group(1).strip()
                if value_match and value_match.group(1):
                    summary += f"\nValue: {value_match.group(1).strip()}"
                
                dashboard["timeline"].append({
                    "category": "observation",
                    "action": "recorded",
                    "timestamp": timestamp,
                    "title": "Observation",
                    "summary": summary[:200]
                })
    
    # Get most recent vitals (limit to latest of each type)
    vitals_by_type = {}
    for vital in sorted(dashboard["vitals"], key=lambda x: x.get("taken_at", ""), reverse=True):
        vtype = vital["type"]
        if vtype not in vitals_by_type:
            vitals_by_type[vtype] = vital
    dashboard["vitals"] = list(vitals_by_type.values())
    
    # Get most recent labs (limit to latest of each test)
    labs_by_name = {}
    for lab in sorted(dashboard["labs"], key=lambda x: x.get("collected_at", ""), reverse=True):
        test_name = lab["test_name"]
        if test_name not in labs_by_name:
            labs_by_name[test_name] = lab
    dashboard["labs"] = list(labs_by_name.values())
    
    # Sort timeline by timestamp
    dashboard["timeline"] = sorted(dashboard["timeline"], key=lambda x: x.get("timestamp", ""), reverse=True)[:20]
    
    return dashboard
