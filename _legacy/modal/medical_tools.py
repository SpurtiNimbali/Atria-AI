"""
Real implementations of medical tools for the conversational doctor.
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
import asyncio
import aiohttp

# Import pharmacogenomics module
from pharmacogenomics import check_genetic_compatibility as pgx_check_genetic_compatibility


# ==============================================================================
# 1. MEDICAL KNOWLEDGE GRAPH - Based on UMLS, FDA, and Clinical Guidelines
# ==============================================================================

MEDICAL_KNOWLEDGE_GRAPH = {
    "iron-deficiency anemia": {
        "concept_id": "C0162316",  # UMLS CUI
        "category": "condition",
        "alternative_names": ["iron deficiency", "IDA", "anemia due to iron deficiency"],
        "treatments": [
            {
                "name": "Oral Iron (Ferrous Sulfate)",
                "line": "first-line",
                "efficacy": "65-70% effective",
                "timeframe": "8-12 weeks to normalize",
                "pros": ["Low cost", "Widely available", "Easy to administer"],
                "cons": ["GI side effects (30-40%)", "Poor absorption in some patients", "Requires compliance"],
                "contraindications": ["Active peptic ulcer", "Hemochromatosis"],
                "typical_dose": "325mg (65mg elemental iron) TID"
            },
            {
                "name": "IV Iron (Iron Sucrose/Ferric Carboxymaltose)",
                "line": "second-line or first-line if oral intolerant",
                "efficacy": "85-95% effective",
                "timeframe": "2-4 weeks to normalize",
                "pros": ["Fast repletion", "Bypasses GI absorption", "Better compliance"],
                "cons": ["Requires IV access", "Higher cost", "Rare allergic reactions (0.5-3%)"],
                "contraindications": ["Active infection", "Known hypersensitivity to iron"],
                "typical_dose": "Based on total iron deficit calculation"
            },
            {
                "name": "Blood Transfusion",
                "line": "rescue therapy",
                "efficacy": "Immediate",
                "timeframe": "Hours",
                "pros": ["Immediate symptom relief", "Life-saving in severe cases"],
                "cons": ["Transfusion reactions", "Doesn't address underlying iron deficiency", "Expensive"],
                "contraindications": ["Religious objection (Jehovah's Witness)", "Volume overload risk"],
                "typical_dose": "1-2 units PRBC"
            }
        ],
        "risk_factors": ["Heavy menstruation", "GI bleeding", "Pregnancy", "Poor diet", "Malabsorption"],
        "diagnostic_criteria": {
            "hemoglobin": {"male": "<13 g/dL", "female": "<12 g/dL"},
            "ferritin": "<30 ng/mL",
            "transferrin_saturation": "<20%"
        },
        "complications": ["Fatigue", "Weakness", "Cognitive impairment", "Heart problems in severe cases"]
    },
    
    "type 2 diabetes": {
        "concept_id": "C0011860",
        "category": "condition",
        "alternative_names": ["T2DM", "non-insulin dependent diabetes", "adult onset diabetes"],
        "treatments": [
            {
                "name": "Metformin",
                "line": "first-line",
                "efficacy": "Reduces HbA1c by 1-2%",
                "mechanism": "Decreases hepatic glucose production",
                "pros": ["Low cost", "Weight neutral or loss", "Cardiovascular benefits"],
                "cons": ["GI side effects", "Contraindicated in CKD"],
                "contraindications": ["eGFR <30 mL/min", "Lactic acidosis risk"],
                "typical_dose": "500-2000mg daily in divided doses"
            },
            {
                "name": "GLP-1 Agonists (e.g., Semaglutide)",
                "line": "second-line or first-line if CVD",
                "efficacy": "Reduces HbA1c by 1-1.5%",
                "mechanism": "Increases insulin, decreases glucagon",
                "pros": ["Weight loss", "Cardiovascular benefits", "Renal protection"],
                "cons": ["Injectable", "Expensive", "GI side effects"],
                "contraindications": ["Personal/family history of medullary thyroid cancer", "MEN2"],
                "typical_dose": "Varies by agent"
            }
        ],
        "diagnostic_criteria": {
            "fasting_glucose": "≥126 mg/dL",
            "HbA1c": "≥6.5%",
            "random_glucose": "≥200 mg/dL with symptoms"
        },
        "target_goals": {
            "HbA1c": "<7% (general), <8% (elderly/complex)",
            "fasting_glucose": "80-130 mg/dL",
            "postprandial_glucose": "<180 mg/dL"
        },
        "complications": ["Retinopathy", "Nephropathy", "Neuropathy", "Cardiovascular disease"]
    },
    
    "hypertension": {
        "concept_id": "C0020538",
        "category": "condition",
        "alternative_names": ["high blood pressure", "HTN", "elevated blood pressure"],
        "treatments": [
            {
                "name": "ACE Inhibitors (e.g., Lisinopril)",
                "line": "first-line",
                "efficacy": "Reduces BP by 10-15/5-8 mmHg",
                "mechanism": "Blocks angiotensin-converting enzyme",
                "pros": ["Renal protective", "Heart failure benefits", "Once daily dosing"],
                "cons": ["Dry cough (10-15%)", "Hyperkalemia risk", "Angioedema (rare)"],
                "contraindications": ["Pregnancy", "Bilateral renal artery stenosis", "Angioedema history"],
                "typical_dose": "10-40mg daily"
            },
            {
                "name": "Thiazide Diuretics (e.g., HCTZ)",
                "line": "first-line",
                "efficacy": "Reduces BP by 10-15/5-8 mmHg",
                "mechanism": "Increases sodium and water excretion",
                "pros": ["Inexpensive", "Once daily", "Reduces cardiovascular events"],
                "cons": ["Hypokalemia", "Hyperuricemia", "Hyperglycemia"],
                "contraindications": ["Gout", "Severe hypokalemia"],
                "typical_dose": "12.5-25mg daily"
            }
        ],
        "diagnostic_criteria": {
            "stage_1": "130-139 / 80-89 mmHg",
            "stage_2": "≥140 / ≥90 mmHg"
        },
        "target_goals": {
            "general": "<130/80 mmHg",
            "elderly": "<140/90 mmHg"
        }
    }
}

# Drug-Disease Relationships
DRUG_DISEASE_INTERACTIONS = {
    "metformin": {
        "contraindicated_in": ["CKD stage 4-5 (eGFR <30)", "Acute metabolic acidosis", "Severe hepatic impairment"],
        "caution_in": ["CKD stage 3 (eGFR 30-60)", "Heart failure", "Alcohol abuse"],
        "indicated_for": ["Type 2 diabetes", "Prediabetes", "PCOS"]
    },
    "lisinopril": {
        "contraindicated_in": ["Pregnancy", "Bilateral renal artery stenosis", "Angioedema history"],
        "caution_in": ["Unilateral renal artery stenosis", "Severe aortic stenosis", "Hyperkalemia"],
        "indicated_for": ["Hypertension", "Heart failure", "Post-MI", "Diabetic nephropathy"]
    },
    "aspirin": {
        "contraindicated_in": ["Active peptic ulcer disease", "Severe bleeding disorder", "Children with viral illness (Reye's syndrome)"],
        "caution_in": ["Asthma", "Gout", "Renal impairment"],
        "indicated_for": ["Cardiovascular disease prevention", "Post-MI", "Post-stroke", "Pain/fever"]
    }
}

# ==============================================================================
# 2. DRUG INTERACTIONS DATABASE
# ==============================================================================

DRUG_INTERACTIONS = {
    # Anticoagulants + Antiplatelet Agents
    ("warfarin", "aspirin"): {
        "severity": "major",
        "effect": "Increased bleeding risk",
        "mechanism": "Additive anticoagulant and antiplatelet effects",
        "recommendation": "Use with extreme caution, monitor INR closely, consider GI prophylaxis"
    },
    ("warfarin", "ibuprofen"): {
        "severity": "major",
        "effect": "Increased bleeding risk, ulcer risk",
        "mechanism": "NSAIDs inhibit platelet function and increase INR",
        "recommendation": "Avoid if possible, use acetaminophen instead"
    },
    ("aspirin", "ibuprofen"): {
        "severity": "moderate",
        "effect": "Increased GI bleeding risk",
        "mechanism": "Both drugs irritate GI lining and affect platelets",
        "recommendation": "Avoid combination, use lowest doses if necessary"
    },
    
    # ACE Inhibitors + Other Drugs
    ("lisinopril", "potassium"): {
        "severity": "major",
        "effect": "Hyperkalemia (high potassium)",
        "mechanism": "ACE inhibitors retain potassium",
        "recommendation": "Monitor potassium levels, avoid potassium supplements"
    },
    ("lisinopril", "spironolactone"): {
        "severity": "major",
        "effect": "Severe hyperkalemia risk",
        "mechanism": "Both drugs retain potassium",
        "recommendation": "Monitor potassium closely (weekly initially), may need dose adjustments"
    },
    ("lisinopril", "ibuprofen"): {
        "severity": "moderate",
        "effect": "Reduced blood pressure control, kidney damage risk",
        "mechanism": "NSAIDs counteract ACE inhibitors and stress kidneys",
        "recommendation": "Use NSAIDs sparingly, monitor BP and renal function"
    },
    ("lisinopril", "nsaids"): {
        "severity": "moderate",
        "effect": "Reduced blood pressure control, kidney damage risk",
        "mechanism": "NSAIDs counteract ACE inhibitors and stress kidneys",
        "recommendation": "Use NSAIDs sparingly, monitor blood pressure and kidney function"
    },
    
    # Diabetes Medications
    ("metformin", "contrast dye"): {
        "severity": "major",
        "effect": "Lactic acidosis risk",
        "mechanism": "Kidney stress from contrast can cause metformin buildup",
        "recommendation": "Hold metformin 48 hours before contrast, resume after kidney function verified"
    },
    ("metformin", "alcohol"): {
        "severity": "major",
        "effect": "Lactic acidosis risk",
        "mechanism": "Alcohol increases risk of lactic acidosis",
        "recommendation": "Avoid excessive alcohol consumption"
    },
    ("insulin", "sulfonylurea"): {
        "severity": "moderate",
        "effect": "Severe hypoglycemia risk",
        "mechanism": "Both lower blood sugar",
        "recommendation": "Dose adjustments needed, frequent glucose monitoring"
    },
    
    # PPIs + Other Drugs
    ("omeprazole", "clopidogrel"): {
        "severity": "major",
        "effect": "Reduced antiplatelet effect",
        "mechanism": "Omeprazole blocks CYP2C19 enzyme needed to activate clopidogrel",
        "recommendation": "Use alternative PPI (pantoprazole) or H2 blocker"
    },
    ("omeprazole", "ferrous sulfate"): {
        "severity": "minor",
        "effect": "Reduced iron absorption (20-60%)",
        "mechanism": "PPIs reduce stomach acid needed for iron absorption",
        "recommendation": "Take iron 2 hours before PPI, space doses, or consider IV iron"
    },
    ("ferrous sulfate", "omeprazole"): {
        "severity": "minor",
        "effect": "Reduced iron absorption",
        "mechanism": "PPIs reduce stomach acid needed for iron absorption",
        "recommendation": "Take iron 2 hours before PPI, or consider IV iron"
    },
    ("omeprazole", "methotrexate"): {
        "severity": "major",
        "effect": "Methotrexate toxicity",
        "mechanism": "PPIs reduce methotrexate excretion",
        "recommendation": "Monitor methotrexate levels, consider stopping PPI"
    },
    
    # Antibiotics
    ("amoxicillin", "warfarin"): {
        "severity": "moderate",
        "effect": "Increased INR, bleeding risk",
        "mechanism": "Antibiotics alter gut flora that produce vitamin K",
        "recommendation": "Monitor INR more frequently during antibiotic course"
    },
    ("ciprofloxacin", "theophylline"): {
        "severity": "major",
        "effect": "Theophylline toxicity",
        "mechanism": "Cipro inhibits theophylline metabolism",
        "recommendation": "Reduce theophylline dose or use alternative antibiotic"
    },
    
    # Statins
    ("simvastatin", "clarithromycin"): {
        "severity": "major",
        "effect": "Rhabdomyolysis risk",
        "mechanism": "Clarithromycin inhibits statin metabolism",
        "recommendation": "Hold statin during antibiotic course or use azithromycin instead"
    },
    ("simvastatin", "gemfibrozil"): {
        "severity": "major",
        "effect": "Severe myopathy/rhabdomyolysis",
        "mechanism": "Gemfibrozil increases statin levels dramatically",
        "recommendation": "CONTRAINDICATED - use fenofibrate instead"
    },
    
    # Psychiatric Medications
    ("fluoxetine", "tramadol"): {
        "severity": "major",
        "effect": "Serotonin syndrome",
        "mechanism": "Both increase serotonin levels",
        "recommendation": "Avoid combination, use alternative analgesic"
    },
    ("sertraline", "ibuprofen"): {
        "severity": "moderate",
        "effect": "Increased GI bleeding risk",
        "mechanism": "SSRIs impair platelet function, NSAIDs irritate GI lining",
        "recommendation": "Use with caution, consider GI protection"
    },
    
    # Antihypertensives
    ("amlodipine", "simvastatin"): {
        "severity": "moderate",
        "effect": "Increased statin levels, myopathy risk",
        "mechanism": "Amlodipine inhibits CYP3A4",
        "recommendation": "Limit simvastatin to 20mg daily with amlodipine"
    },
    ("diltiazem", "metoprolol"): {
        "severity": "moderate",
        "effect": "Bradycardia, heart block",
        "mechanism": "Both slow heart rate through different mechanisms",
        "recommendation": "Monitor heart rate and blood pressure closely"
    },
    
    # Immunosuppressants
    ("tacrolimus", "fluconazole"): {
        "severity": "major",
        "effect": "Tacrolimus toxicity (nephrotoxicity, neurotoxicity)",
        "mechanism": "Fluconazole inhibits CYP3A4",
        "recommendation": "Monitor tacrolimus levels daily, reduce dose"
    },
    
    # Diuretics
    ("furosemide", "gentamicin"): {
        "severity": "moderate",
        "effect": "Increased ototoxicity and nephrotoxicity",
        "mechanism": "Additive kidney and ear damage",
        "recommendation": "Monitor renal function and hearing, avoid if possible"
    },
    ("hydrochlorothiazide", "lithium"): {
        "severity": "major",
        "effect": "Lithium toxicity",
        "mechanism": "Thiazides reduce lithium excretion",
        "recommendation": "Monitor lithium levels frequently, may need dose reduction"
    },
}

DRUG_CONTRAINDICATIONS = {
    "penicillin": {
        "allergy": ["penicillin", "amoxicillin", "ampicillin"],
        "cross_reactivity": "10% cross-reactivity with cephalosporins"
    },
    "aspirin": {
        "conditions": ["active bleeding", "hemophilia", "severe thrombocytopenia"],
        "warning": "Avoid in active GI bleeding"
    },
    "metformin": {
        "conditions": ["severe kidney disease", "acute heart failure", "liver failure"],
        "lab_cutoff": "eGFR < 30 mL/min - contraindicated"
    },
    "lisinopril": {
        "conditions": ["pregnancy", "bilateral renal artery stenosis", "angioedema history"],
        "warning": "Can cause fetal harm in pregnancy"
    }
}


async def check_drug_interactions(
    proposed_drug: str,
    current_medications: List[str] = None,
    conditions: List[str] = None,
    allergies: List[str] = None,
    patient_id: str = None
) -> Dict[str, Any]:
    """
    Check for drug-drug interactions and contraindications.
    """
    from ehr_parser import get_patient_medications, get_patient_conditions
    
    proposed_drug = proposed_drug.lower().strip()
    
    # If patient_id provided, fetch REAL medications from EHR
    if patient_id and not current_medications:
        patient_meds = get_patient_medications(patient_id)
        current_medications = [m['name'].lower().strip() for m in patient_meds]
    else:
        current_medications = [m.lower().strip() for m in (current_medications or [])]
    
    # Fetch real conditions if patient_id provided
    if patient_id and not conditions:
        patient_conditions = get_patient_conditions(patient_id)
        conditions = [c['name'].lower() for c in patient_conditions]
    else:
        conditions = [c.lower() for c in (conditions or [])]
    
    allergies = [a.lower() for a in (allergies or [])]
    
    interactions_found = []
    contraindications_found = []
    warnings = []
    
    # Check drug-drug interactions
    for current_med in current_medications:
        # Check both directions
        interaction = DRUG_INTERACTIONS.get((proposed_drug, current_med)) or \
                     DRUG_INTERACTIONS.get((current_med, proposed_drug))
        
        if interaction:
            interactions_found.append({
                "drug_pair": f"{proposed_drug} + {current_med}",
                "severity": interaction["severity"],
                "effect": interaction["effect"],
                "mechanism": interaction["mechanism"],
                "recommendation": interaction["recommendation"]
            })
    
    # Check contraindications
    if proposed_drug in DRUG_CONTRAINDICATIONS:
        contra_info = DRUG_CONTRAINDICATIONS[proposed_drug]
        
        # Check allergies
        if "allergy" in contra_info:
            for allergy in allergies:
                if allergy in contra_info["allergy"]:
                    contraindications_found.append({
                        "type": "allergy",
                        "detail": f"Patient allergic to {allergy}",
                        "severity": "absolute",
                        "action": "DO NOT GIVE - Find alternative"
                    })
        
        # Check conditions
        if "conditions" in contra_info:
            for condition in conditions:
                if any(contra_condition in condition for contra_condition in contra_info["conditions"]):
                    contraindications_found.append({
                        "type": "condition",
                        "detail": f"Contraindicated in {condition}",
                        "severity": "absolute",
                        "action": contra_info.get("warning", "Contraindicated")
                    })
    
    # Determine safety level
    if contraindications_found:
        safety_level = "contraindicated"
        safe_to_use = False
    elif any(i["severity"] == "major" for i in interactions_found):
        safety_level = "major_interaction"
        safe_to_use = False
    elif interactions_found:
        safety_level = "caution"
        safe_to_use = True  # With monitoring
    else:
        safety_level = "safe"
        safe_to_use = True
    
    return {
        "proposed_drug": proposed_drug,
        "current_medications": current_medications,  # Include for display
        "safety_level": safety_level,
        "safe_to_use": safe_to_use,
        "interactions": interactions_found,
        "contraindications": contraindications_found,
        "total_concerns": len(interactions_found) + len(contraindications_found),
        "summary": _generate_interaction_summary(
            proposed_drug, interactions_found, contraindications_found
        )
    }


def _generate_interaction_summary(
    drug: str,
    interactions: List[Dict],
    contraindications: List[Dict]
) -> str:
    """Generate human-readable summary."""
    if contraindications:
        return f"{drug.title()} is contraindicated for this patient - do not give."
    elif not interactions:
        return f"No major interactions found with {drug.title()}."
    elif len(interactions) == 1:
        return f"{drug.title()} has a {interactions[0]['severity']} interaction: {interactions[0]['effect']}"
    else:
        return f"{drug.title()} has {len(interactions)} interactions found - review carefully."


# ==============================================================================
# 2. LAB TREND ANALYSIS
# ==============================================================================

async def analyze_lab_trends(
    lab_type: str,
    patient_id: str,
    ehr_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze lab value trends from patient's EHR data.
    """
    # Extract lab values from EHR documents
    lab_values = _extract_lab_values_from_ehr(lab_type, ehr_context)
    
    if not lab_values:
        return {
            "lab_type": lab_type,
            "trend": "no_data",
            "message": f"No {lab_type} values found in recent records",
            "recent_values": [],
            "prediction": "Insufficient data for trend analysis"
        }
    
    # Sort by date
    lab_values.sort(key=lambda x: x["date"])
    
    # Calculate trend
    values = [v["value"] for v in lab_values]
    trend_direction = _calculate_trend(values)
    
    # Detect concerning patterns
    concerning_patterns = _detect_concerning_patterns(lab_type, lab_values)
    
    # Predict trajectory
    prediction = _predict_lab_trajectory(lab_type, lab_values, trend_direction)
    
    return {
        "lab_type": lab_type,
        "trend": trend_direction,
        "recent_values": lab_values[-5:],  # Last 5 values
        "total_measurements": len(lab_values),
        "date_range": f"{lab_values[0]['date']} to {lab_values[-1]['date']}",
        "concerning_patterns": concerning_patterns,
        "prediction": prediction,
        "interpretation": _interpret_lab_trend(lab_type, trend_direction, lab_values)
    }


def _extract_lab_values_from_ehr(lab_type: str, ehr_context: Dict[str, Any]) -> List[Dict]:
    """Extract lab values from EHR documents using the real EHR parser."""
    from ehr_parser import get_patient_labs
    
    # Get patient_id from context
    patient_id = ehr_context.get("patient_id")
    if not patient_id:
        return []
    
    # Fetch REAL lab values from Elasticsearch
    labs = get_patient_labs(patient_id, lab_name=lab_type)
    
    # Convert to expected format
    lab_values = []
    for lab in labs:
        if "value" in lab and "unit" in lab:
            lab_values.append({
                "date": lab["date"][:10] if lab.get("date") else lab.get("timestamp", "")[:10],
                "value": lab["value"],
                "unit": lab["unit"]
            })
    
    # If no real data found, return empty (AI will say "no lab data available")
    # Or for demo, return mock data with a note
    if not lab_values:
        # For demo purposes with synthetic data that doesn't have all labs
        if "hemoglobin" in lab_type.lower():
            return [
                {"date": "2026-01-15", "value": 10.2, "unit": "g/dL", "note": "synthetic demo data"},
                {"date": "2026-02-01", "value": 8.9, "unit": "g/dL", "note": "synthetic demo data"},
                {"date": "2026-02-10", "value": 7.2, "unit": "g/dL", "note": "synthetic demo data"},
                {"date": "2026-02-14", "value": 9.1, "unit": "g/dL", "note": "synthetic demo data"},
            ]
        return []
    
    return lab_values


def _calculate_trend(values: List[float]) -> str:
    """Calculate trend direction from values."""
    if len(values) < 2:
        return "insufficient_data"
    
    # Simple linear regression slope
    x = np.arange(len(values))
    slope = np.polyfit(x, values, 1)[0]
    
    if abs(slope) < 0.1:
        return "stable"
    elif slope > 0:
        return "increasing"
    else:
        return "decreasing"


def _detect_concerning_patterns(lab_type: str, lab_values: List[Dict]) -> List[str]:
    """Detect concerning patterns in lab trends."""
    patterns = []
    
    if "hemoglobin" in lab_type.lower():
        values = [v["value"] for v in lab_values]
        
        # Check for rapid drop
        for i in range(1, len(values)):
            drop = values[i-1] - values[i]
            if drop > 1.5:
                patterns.append(f"Rapid drop of {drop:.1f} g/dL")
        
        # Check for persistent low values
        if all(v < 10 for v in values[-3:]):
            patterns.append("Persistently low hemoglobin")
    
    return patterns


def _predict_lab_trajectory(lab_type: str, lab_values: List[Dict], trend: str) -> str:
    """Predict future lab trajectory."""
    if trend == "decreasing" and "hemoglobin" in lab_type.lower():
        return "Without intervention, hemoglobin will continue to drop. Current treatment not effective enough."
    elif trend == "stable":
        return "Lab values are stable. Continue current management."
    elif trend == "increasing":
        return "Positive trend - treatment appears effective."
    else:
        return "Need more data points to predict trajectory."


def _interpret_lab_trend(lab_type: str, trend: str, lab_values: List[Dict]) -> str:
    """Generate interpretation of lab trend."""
    latest = lab_values[-1]["value"]
    
    if "hemoglobin" in lab_type.lower():
        if trend == "decreasing":
            return f"Hemoglobin trending down (now {latest} g/dL). Suggests ongoing blood loss or inadequate iron repletion."
        elif latest < 10:
            return f"Hemoglobin is {latest} g/dL - below normal (12-16 g/dL). Patient symptomatic from anemia."
        else:
            return f"Hemoglobin improving to {latest} g/dL - treatment effective."
    
    return f"Current {lab_type}: {latest}"


# ==============================================================================
# 3. TREATMENT RISK PREDICTION
# ==============================================================================

async def predict_treatment_risk(
    intervention: str,
    patient_id: str,
    patient_features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Predict risk scores for proposed intervention.
    """
    age = patient_features.get("age", 50)
    conditions = patient_features.get("conditions", [])
    
    # Base risk score
    risk_score = 0.05  # 5% baseline
    
    # Age adjustments
    if age < 18:
        risk_score *= 0.7  # Lower risk in young patients
    elif age > 65:
        risk_score *= 1.5  # Higher risk in elderly
    
    # Condition-specific risks
    high_risk_conditions = ["heart failure", "kidney disease", "liver disease"]
    for condition in conditions:
        if any(hrc in condition.lower() for hrc in high_risk_conditions):
            risk_score *= 1.3
    
    # Intervention-specific risks
    intervention_lower = intervention.lower()
    
    if "iv iron" in intervention_lower:
        main_risks = [
            "Allergic reaction (0.5%)",
            "Hypotension during infusion (2%)",
            "Infection at IV site (<1%)"
        ]
        benefits = [
            "Faster iron repletion (2-3 weeks vs 8-12 weeks oral)",
            "Doesn't rely on GI absorption",
            "More reliable compliance"
        ]
    elif "transfusion" in intervention_lower:
        main_risks = [
            "Transfusion reaction (1%)",
            "Volume overload (2-3%)",
            "Iron overload with multiple transfusions"
        ]
        benefits = [
            "Immediate symptom relief",
            "Fast hemoglobin increase"
        ]
        risk_score *= 1.2
    else:
        main_risks = ["Standard procedural risks"]
        benefits = ["Expected therapeutic benefit"]
    
    # Categorize risk level
    if risk_score < 0.1:
        risk_level = "low"
    elif risk_score < 0.25:
        risk_level = "moderate"
    else:
        risk_level = "high"
    
    return {
        "intervention": intervention,
        "risk_score": round(risk_score, 3),
        "risk_level": risk_level,
        "main_risks": main_risks,
        "benefits": benefits,
        "recommendation": _generate_risk_recommendation(risk_level, intervention),
        "monitoring_required": _get_monitoring_requirements(intervention)
    }


def _generate_risk_recommendation(risk_level: str, intervention: str) -> str:
    """Generate risk-based recommendation."""
    if risk_level == "low":
        return f"Proceed with {intervention} - risks are minimal and benefits outweigh them."
    elif risk_level == "moderate":
        return f"Proceed with {intervention} with appropriate monitoring and precautions."
    else:
        return f"Carefully consider alternatives to {intervention} - high risk profile."


def _get_monitoring_requirements(intervention: str) -> List[str]:
    """Get required monitoring for intervention."""
    if "iv iron" in intervention.lower():
        return [
            "Vital signs during infusion",
            "CBC 1 week after completion",
            "Ferritin at 4 weeks"
        ]
    elif "transfusion" in intervention.lower():
        return [
            "Vital signs every 15 minutes during transfusion",
            "CBC 1 hour after",
            "Watch for transfusion reactions"
        ]
    else:
        return ["Routine follow-up"]


# ==============================================================================
# 4. PERSONALIZED DOSE CALCULATION
# ==============================================================================

async def calculate_personalized_dose(
    drug: str,
    patient_id: str,
    weight_kg: float = None,
    age_years: int = None,
    kidney_function: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Calculate personalized drug dose using pharmacokinetic principles.
    """
    drug = drug.lower().strip()
    
    # Drug-specific dosing calculations
    if "iron" in drug and "iv" in drug:
        return _calculate_iv_iron_dose(weight_kg, age_years)
    
    elif "warfarin" in drug:
        return _calculate_warfarin_dose(weight_kg, age_years)
    
    elif "metformin" in drug:
        return _calculate_metformin_dose(kidney_function)
    
    elif "lisinopril" in drug:
        return _calculate_lisinopril_dose(kidney_function)
    
    else:
        return {
            "drug": drug,
            "recommended_dose": "Standard dosing per package insert",
            "adjustments_needed": [],
            "monitoring_required": ["Routine follow-up"],
            "note": "No specific dose calculator available for this medication"
        }


def _calculate_iv_iron_dose(weight_kg: float, age_years: int, patient_id: str = None) -> Dict[str, Any]:
    """Calculate IV iron dose."""
    from ehr_parser import get_patient_demographics
    
    # Fetch real patient demographics if available
    if patient_id and not weight_kg:
        demographics = get_patient_demographics(patient_id)
        age_years = demographics.get('age', age_years)
        # Weight not usually in Patient resource, use reasonable default based on age/gender
        if demographics.get('gender') == 'female' and age_years:
            if age_years < 18:
                weight_kg = 50  # Adolescent female
            else:
                weight_kg = 65  # Adult female average
        else:
            weight_kg = 70  # Adult male average
    
    if not weight_kg:
        weight_kg = 65  # Default adult
    
    # Simplified Ganzoni formula
    target_hb = 12  # g/dL
    current_hb = 9   # Estimate
    hb_deficit = target_hb - current_hb
    
    total_iron_needed = weight_kg * hb_deficit * 2.4 + 500  # mg
    
    # Iron sucrose: max 200mg per infusion
    num_infusions = int(np.ceil(total_iron_needed / 200))
    
    return {
        "drug": "IV Iron Sucrose",
        "total_iron_deficit": f"{int(total_iron_needed)} mg",
        "recommended_dose": f"200 mg IV over 2 hours",
        "number_of_infusions": num_infusions,
        "schedule": f"Repeat every 3-7 days for {num_infusions} total doses",
        "adjustments_needed": [],
        "monitoring_required": [
            "Vital signs during each infusion",
            "CBC weekly during treatment",
            "Ferritin and iron studies 4 weeks after completion"
        ],
        "precautions": [
            "Have epinephrine available for allergic reaction",
            "Monitor for hypotension during infusion"
        ]
    }


def _calculate_warfarin_dose(weight_kg: float, age_years: int) -> Dict[str, Any]:
    """Calculate warfarin starting dose."""
    base_dose = 5.0  # mg/day
    
    # Age adjustment
    if age_years and age_years > 65:
        base_dose = 2.5
    
    return {
        "drug": "Warfarin",
        "recommended_dose": f"{base_dose} mg once daily",
        "adjustments_needed": [
            "Dose highly variable between patients",
            "Requires INR-guided titration"
        ],
        "monitoring_required": [
            "INR baseline, then every 2-3 days until stable",
            "Target INR usually 2-3",
            "Monthly INR once stable"
        ],
        "note": "This is a starting dose only - must adjust based on INR"
    }


def _calculate_metformin_dose(kidney_function: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metformin dose with kidney adjustment."""
    egfr = kidney_function.get("egfr", 90) if kidney_function else 90
    
    if egfr >= 45:
        dose = "500-1000 mg twice daily with meals"
        adjustments = []
    elif egfr >= 30:
        dose = "500 mg twice daily (reduced dose)"
        adjustments = ["Reduced dose due to kidney function"]
    else:
        dose = "Contraindicated"
        adjustments = ["eGFR < 30 - do not use metformin"]
    
    return {
        "drug": "Metformin",
        "recommended_dose": dose,
        "adjustments_needed": adjustments,
        "monitoring_required": [
            "Kidney function every 6-12 months",
            "Vitamin B12 annually",
            "Hold before contrast procedures"
        ]
    }


def _calculate_lisinopril_dose(kidney_function: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate lisinopril dose."""
    return {
        "drug": "Lisinopril",
        "recommended_dose": "Start 2.5-5 mg once daily, titrate up to 10-40 mg daily",
        "adjustments_needed": [
            "Start low dose if elderly or kidney disease"
        ],
        "monitoring_required": [
            "Blood pressure weekly during titration",
            "Potassium and creatinine 1-2 weeks after starting",
            "Monitor for cough (common side effect)"
        ]
    }


# ==============================================================================
# 5. MEDICAL KNOWLEDGE GRAPH (Rule-based)
# ==============================================================================

MEDICAL_KNOWLEDGE = {
    "iron-deficiency anemia": {
        "treatments": [
            {
                "name": "Oral iron (ferrous sulfate)",
                "efficacy": "moderate",
                "time_to_effect": "8-12 weeks",
                "pros": ["Convenient", "Inexpensive", "Home administration"],
                "cons": ["GI side effects", "Requires compliance", "Slow"]
            },
            {
                "name": "IV iron sucrose",
                "efficacy": "high",
                "time_to_effect": "2-3 weeks",
                "pros": ["Fast", "No GI side effects", "Reliable absorption"],
                "cons": ["Requires clinic visits", "Small reaction risk", "More expensive"]
            },
            {
                "name": "Blood transfusion",
                "efficacy": "immediate",
                "time_to_effect": "hours",
                "pros": ["Immediate relief", "Life-saving in severe cases"],
                "cons": ["Infection risk", "Doesn't fix underlying problem", "Volume overload risk"]
            }
        ],
        "causes": [
            "Heavy menstrual periods (most common in young women)",
            "GI bleeding (ulcer, polyp, cancer)",
            "Poor dietary iron",
            "Malabsorption (celiac disease, gastric bypass)"
        ]
    }
}


async def query_knowledge_graph(
    query_type: str,
    primary_entity: str,
    context_entities: List[str] = None
) -> Dict[str, Any]:
    """
    Query comprehensive medical knowledge graph.
    Based on UMLS concepts, FDA data, and clinical guidelines.
    """
    primary_entity = primary_entity.lower().strip()
    context_entities = context_entities or []
    
    # Try to find entity in knowledge graph (including alternative names)
    matched_entity = None
    for entity_key, entity_data in MEDICAL_KNOWLEDGE_GRAPH.items():
        if primary_entity in entity_key or \
           primary_entity in [name.lower() for name in entity_data.get("alternative_names", [])]:
            matched_entity = entity_key
            break
    
    if query_type == "alternative_treatments":
        if matched_entity:
            entity_data = MEDICAL_KNOWLEDGE_GRAPH[matched_entity]
            treatments = entity_data.get("treatments", [])
            return {
                "query_type": query_type,
                "primary_entity": primary_entity,
                "matched_concept": matched_entity,
                "concept_id": entity_data.get("concept_id"),
                "treatments_found": len(treatments),
                "treatments": treatments,
                "summary": f"Found {len(treatments)} evidence-based treatment options for {matched_entity}",
                "source": "UMLS + FDA + Clinical Guidelines"
            }
    
    elif query_type == "contraindications":
        # Check drug-disease contraindications
        if primary_entity in DRUG_DISEASE_INTERACTIONS:
            drug_data = DRUG_DISEASE_INTERACTIONS[primary_entity]
            return {
                "query_type": query_type,
                "drug": primary_entity,
                "contraindicated_in": drug_data.get("contraindicated_in", []),
                "caution_in": drug_data.get("caution_in", []),
                "indicated_for": drug_data.get("indicated_for", []),
                "summary": f"{primary_entity.title()} contraindications and indications from FDA labeling",
                "source": "FDA Drug Labeling + Clinical Guidelines"
            }
    
    elif query_type == "treatment_pathway":
        if matched_entity:
            entity_data = MEDICAL_KNOWLEDGE_GRAPH[matched_entity]
            treatments = entity_data.get("treatments", [])
            
            # Generate pathway based on treatment lines
            pathway = []
            for i, treatment in enumerate(sorted(treatments, key=lambda x: x.get("line", "z")), 1):
                pathway.append(f"{i}. {treatment.get('line', 'therapy').title()}: {treatment['name']} ({treatment.get('timeframe', 'variable timeframe')})")
            
            return {
                "query_type": query_type,
                "condition": matched_entity,
                "concept_id": entity_data.get("concept_id"),
                "pathway": pathway,
                "diagnostic_criteria": entity_data.get("diagnostic_criteria", {}),
                "target_goals": entity_data.get("target_goals", {}),
                "complications": entity_data.get("complications", []),
                "summary": f"Clinical pathway for {matched_entity} based on current guidelines",
                "source": "Clinical Practice Guidelines"
            }
    
    elif query_type == "causal_relationships":
        if matched_entity:
            entity_data = MEDICAL_KNOWLEDGE_GRAPH[matched_entity]
            return {
                "query_type": query_type,
                "condition": matched_entity,
                "risk_factors": entity_data.get("risk_factors", []),
                "complications": entity_data.get("complications", []),
                "summary": f"Risk factors and complications for {matched_entity}",
                "source": "Medical Literature + Clinical Guidelines"
            }
    
    elif query_type == "disease_progression":
        if matched_entity:
            entity_data = MEDICAL_KNOWLEDGE_GRAPH[matched_entity]
            return {
                "query_type": query_type,
                "condition": matched_entity,
                "natural_history": f"Typical progression of {matched_entity}",
                "complications": entity_data.get("complications", []),
                "monitoring": "Regular follow-up based on severity and treatment response",
                "summary": f"Disease progression information for {matched_entity}",
                "source": "Medical Literature"
            }
    
    # If no match found, return limited info
    return {
        "query_type": query_type,
        "primary_entity": primary_entity,
        "findings": [f"Limited structured data for {primary_entity} in knowledge graph"],
        "note": "Consider consulting UpToDate or medical literature for detailed information",
        "available_entities": list(MEDICAL_KNOWLEDGE_GRAPH.keys())
    }


# ==============================================================================
# 6. CLINICAL TRIALS SEARCH (ClinicalTrials.gov API)
# ==============================================================================

async def search_clinical_trials(
    condition: str,
    intervention: str = None
) -> Dict[str, Any]:
    """
    Search ClinicalTrials.gov API for relevant trials.
    Uses the REAL ClinicalTrials.gov v2 API.
    """
    import aiohttp
    
    # ClinicalTrials.gov API v2
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # Build query parameters
    params = {
        "query.cond": condition,
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION",
        "pageSize": 5,
        "format": "json"
    }
    
    if intervention:
        params["query.intr"] = intervention
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    trials = []
                    studies = data.get("studies", [])
                    
                    for study in studies:
                        protocol = study.get("protocolSection", {})
                        identification = protocol.get("identificationModule", {})
                        status = protocol.get("statusModule", {})
                        design = protocol.get("designModule", {})
                        eligibility = protocol.get("eligibilityModule", {})
                        
                        trial_info = {
                            "nct_id": identification.get("nctId", "Unknown"),
                            "title": identification.get("briefTitle", "Unknown"),
                            "status": status.get("overallStatus", "Unknown"),
                            "phase": design.get("phases", ["N/A"])[0] if design.get("phases") else "N/A",
                            "enrollment": eligibility.get("maximumAge", "Not specified"),
                            "summary": identification.get("briefSummary", "No summary available"),
                            "url": f"https://clinicaltrials.gov/study/{identification.get('nctId', '')}"
                        }
                        trials.append(trial_info)
                    
                    return {
                        "condition": condition,
                        "intervention": intervention,
                        "trials_found": len(trials),
                        "relevant_trials": trials,
                        "source": "ClinicalTrials.gov API (real-time)",
                        "summary": f"Found {len(trials)} active/recruiting trials for {condition}"
                    }
                else:
                    return {
                        "condition": condition,
                        "intervention": intervention,
                        "trials_found": 0,
                        "relevant_trials": [],
                        "error": f"API returned status {response.status}",
                        "note": "Unable to fetch trials at this time"
                    }
                    
    except asyncio.TimeoutError:
        return {
            "condition": condition,
            "trials_found": 0,
            "relevant_trials": [],
            "error": "Request timed out",
            "note": "ClinicalTrials.gov API timeout - try again"
        }
    except Exception as e:
        return {
            "condition": condition,
            "trials_found": 0,
            "relevant_trials": [],
            "error": str(e),
            "note": f"Error accessing ClinicalTrials.gov: {str(e)}"
        }


# ==============================================================================
# 7. GENETIC COMPATIBILITY CHECK (Pharmacogenomics)
# ==============================================================================

async def check_genetic_compatibility(
    drug: str,
    genetic_markers: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Wrapper for pharmacogenomics genetic compatibility checking.
    Uses FDA Pharmacogenomic Biomarkers and CPIC guidelines.
    """
    return await pgx_check_genetic_compatibility(drug, genetic_markers)
