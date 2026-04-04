"""
Route Simulator: Generate branching future trajectories for patient care paths.
"""
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class Route:
    """A possible future care trajectory."""
    route_id: str
    name: str
    probability: float  # 0.0-1.0
    timeline_days: int
    trigger_events: List[str]
    milestones: List[Dict]
    outcomes: Dict[str, float]  # outcome_type → probability
    interventions_needed: List[str]
    risk_factors: List[str]

def simulate_routes(
    patient_id: str,
    current_state: Dict,
    intervention_options: List[str]
) -> List[Route]:
    """
    Simulate possible future care trajectories based on:
    - Current patient state
    - Intervention options
    - Clinical guidelines
    - Risk factors
    
    Returns ranked list of possible routes with probabilities.
    
    Example routes:
    - "Optimal adherence" (70% prob) → controlled BP/glucose in 3mo
    - "Medication non-adherence" (20% prob) → ER visit in 6mo
    - "Lifestyle intervention" (10% prob) → improved outcomes in 6mo
    """
    
    # Rule-based route generation (could be ML model in production)
    routes = []
    
    # Route 1: Optimal adherence path
    routes.append(Route(
        route_id=f"{patient_id}-route-optimal",
        name="Optimal Adherence Path",
        probability=_calculate_adherence_probability(current_state),
        timeline_days=90,
        trigger_events=[
            "Medication taken as prescribed",
            "Follow-up appointments attended",
            "Home BP monitoring compliant"
        ],
        milestones=[
            {
                "day": 7,
                "event": "First follow-up call",
                "expected_outcome": "Medication tolerance confirmed"
            },
            {
                "day": 30,
                "event": "BP recheck",
                "expected_outcome": "BP <130/80"
            },
            {
                "day": 90,
                "event": "HbA1c recheck",
                "expected_outcome": "HbA1c <7.0%"
            }
        ],
        outcomes={
            "bp_controlled": 0.85,
            "hba1c_improved": 0.75,
            "no_complications": 0.95
        },
        interventions_needed=[
            "Continue current meds",
            "Weekly BP monitoring",
            "Dietary counseling"
        ],
        risk_factors=[]
    ))
    
    # Route 2: Non-adherence risk path
    routes.append(Route(
        route_id=f"{patient_id}-route-nonadherence",
        name="Non-Adherence Risk Path",
        probability=_calculate_nonadherence_risk(current_state),
        timeline_days=180,
        trigger_events=[
            "Missed medication doses",
            "Missed follow-up appointment",
            "No home monitoring"
        ],
        milestones=[
            {
                "day": 30,
                "event": "Missed follow-up",
                "expected_outcome": "No BP/glucose monitoring"
            },
            {
                "day": 90,
                "event": "Symptoms develop",
                "expected_outcome": "Headaches, fatigue"
            },
            {
                "day": 180,
                "event": "ER visit likely",
                "expected_outcome": "Hypertensive crisis or DKA"
            }
        ],
        outcomes={
            "bp_uncontrolled": 0.70,
            "er_visit": 0.40,
            "hospitalization": 0.15
        },
        interventions_needed=[
            "Adherence support program",
            "Simplify medication regimen",
            "Home health visits",
            "Medication reminders"
        ],
        risk_factors=[
            "Complex medication regimen",
            "No family support",
            "Financial barriers"
        ]
    ))
    
    # Route 3: Escalation path (if current treatment fails)
    routes.append(Route(
        route_id=f"{patient_id}-route-escalation",
        name="Treatment Escalation Path",
        probability=0.25,
        timeline_days=120,
        trigger_events=[
            "BP remains >140/90 despite adherence",
            "HbA1c >7.5% at 3 months"
        ],
        milestones=[
            {
                "day": 30,
                "event": "Treatment not effective",
                "expected_outcome": "BP still elevated"
            },
            {
                "day": 60,
                "event": "Medication adjustment",
                "expected_outcome": "Add second antihypertensive"
            },
            {
                "day": 120,
                "event": "Specialist referral",
                "expected_outcome": "Endocrinology consult for diabetes"
            }
        ],
        outcomes={
            "medication_escalation": 1.0,
            "specialist_needed": 0.60,
            "bp_controlled_eventually": 0.80
        },
        interventions_needed=[
            "Add CCB or thiazide diuretic",
            "Increase Metformin or add GLP-1",
            "Cardiology consult",
            "Dietitian referral"
        ],
        risk_factors=[
            "Resistant hypertension",
            "Poor diabetes control",
            "Family history of CVD"
        ]
    ))
    
    return sorted(routes, key=lambda r: r.probability, reverse=True)


def _calculate_adherence_probability(state: Dict) -> float:
    """Calculate probability of optimal adherence based on risk factors."""
    base_prob = 0.70
    
    # Adjust based on factors
    if state.get("support_system") == "strong":
        base_prob += 0.10
    if state.get("medication_complexity") == "simple":
        base_prob += 0.10
    if state.get("previous_adherence") == "good":
        base_prob += 0.10
    
    return min(base_prob, 0.95)


def _calculate_nonadherence_risk(state: Dict) -> float:
    """Calculate risk of non-adherence."""
    return 1.0 - _calculate_adherence_probability(state)


if __name__ == "__main__":
    # Example usage
    current_state = {
        "conditions": ["Hypertension", "Type 2 Diabetes"],
        "medications": ["Metformin 500mg BID", "Lisinopril 10mg QD"],
        "recent_vitals": {"bp": "135/85", "hba1c": 7.2},
        "support_system": "moderate",
        "medication_complexity": "moderate",
        "previous_adherence": "unknown"
    }
    
    routes = simulate_routes("synthetic-001", current_state, ["current_meds", "escalation"])
    
    print("SIMULATED CARE ROUTES:")
    for route in routes:
        print(f"\n📍 {route.name} (probability: {route.probability*100:.0f}%)")
        print(f"   Timeline: {route.timeline_days} days")
        print(f"   Key milestones:")
        for milestone in route.milestones[:2]:
            print(f"     - Day {milestone['day']}: {milestone['event']}")
        print(f"   Outcomes: {route.outcomes}")
        if route.risk_factors:
            print(f"   Risk factors: {', '.join(route.risk_factors)}")
