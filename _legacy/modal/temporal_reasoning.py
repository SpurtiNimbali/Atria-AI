"""
Temporal Reasoning Engine for disease progression and timeline optimization.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np


class TemporalReasoningEngine:
    """
    Models disease progression, optimizes treatment timelines, predicts future states.
    """
    
    def __init__(self):
        self.progression_models = self._load_progression_models()
    
    async def model_disease_progression(
        self,
        condition: str,
        current_state: Dict[str, Any],
        patient_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Model how disease will progress over time without intervention.
        """
        if "diabetes" in condition.lower():
            return await self._model_diabetes_progression(current_state, patient_factors)
        elif "anemia" in condition.lower():
            return await self._model_anemia_progression(current_state, patient_factors)
        else:
            return await self._generic_progression_model(condition, current_state)
    
    async def optimize_treatment_timeline(
        self,
        treatments: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize timing of multiple treatments/interventions.
        
        Example: When to give iron, when to recheck labs, when to escalate care
        """
        optimal_schedule = []
        current_date = datetime.now()
        
        # Sort treatments by urgency and dependencies
        prioritized = self._prioritize_treatments(treatments, constraints)
        
        for treatment in prioritized:
            # Calculate optimal timing
            optimal_day = self._calculate_optimal_timing(
                treatment,
                current_date,
                constraints
            )
            
            optimal_schedule.append({
                "treatment": treatment["name"],
                "optimal_date": optimal_day.isoformat()[:10],
                "rationale": treatment.get("rationale", ""),
                "dependencies": treatment.get("dependencies", []),
                "flexibility": treatment.get("flexibility_days", 0)
            })
            
            current_date = optimal_day
        
        return {
            "optimized_schedule": optimal_schedule,
            "total_duration_days": (optimal_schedule[-1]["optimal_date"] if optimal_schedule else 0),
            "critical_path": [s["treatment"] for s in optimal_schedule if s.get("flexibility", 1) < 2],
            "optimization_criteria": "Minimize time to target while respecting clinical constraints"
        }
    
    async def predict_future_state(
        self,
        patient_id: str,
        current_state: Dict[str, Any],
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Predict patient's state N days in the future.
        """
        predictions = []
        
        current_hb = current_state.get("labs", {}).get("hemoglobin", 10.0)
        treatment = current_state.get("treatment", "none")
        
        # Simulate day by day
        for day in range(1, days_ahead + 1):
            # Apply treatment effect
            if "iv iron" in treatment.lower():
                daily_change = 0.085  # ~0.6 g/dL per week
            elif "oral iron" in treatment.lower():
                daily_change = 0.035  # ~0.25 g/dL per week
            else:
                daily_change = -0.02  # Declining without treatment
            
            current_hb += daily_change + np.random.normal(0, 0.05)
            current_hb = max(5.0, min(18.0, current_hb))  # Physiological bounds
            
            # Predict symptoms
            if current_hb < 8:
                symptoms = "severe_anemia_symptoms"
            elif current_hb < 10:
                symptoms = "moderate_fatigue"
            elif current_hb < 12:
                symptoms = "mild_fatigue"
            else:
                symptoms = "minimal_symptoms"
            
            if day % 7 == 0:  # Weekly snapshots
                predictions.append({
                    "day": day,
                    "date": (datetime.now() + timedelta(days=day)).isoformat()[:10],
                    "predicted_hemoglobin": round(current_hb, 1),
                    "predicted_symptoms": symptoms,
                    "confidence": 0.8 - (day / days_ahead) * 0.3  # Confidence decreases over time
                })
        
        return {
            "patient_id": patient_id,
            "prediction_horizon": days_ahead,
            "predictions": predictions,
            "key_events": self._identify_key_events(predictions),
            "recommendations": self._generate_timeline_recommendations(predictions)
        }
    
    async def _model_diabetes_progression(
        self,
        current_state: Dict[str, Any],
        patient_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Model Type 2 Diabetes progression."""
        current_hba1c = current_state.get("labs", {}).get("hba1c", 7.0)
        age = patient_factors.get("age", 50)
        bmi = patient_factors.get("bmi", 28)
        
        # Natural progression rate (simplified)
        annual_increase = 0.1  # HbA1c increases ~0.1% per year without intervention
        
        # Adjust for risk factors
        if bmi > 30:
            annual_increase *= 1.2
        if age > 65:
            annual_increase *= 0.9
        
        progression_timeline = []
        for year in range(1, 11):  # 10-year projection
            projected_hba1c = current_hba1c + (annual_increase * year)
            
            # Predict complications
            complication_risk = self._calculate_complication_risk(projected_hba1c, year)
            
            progression_timeline.append({
                "year": year,
                "projected_hba1c": round(projected_hba1c, 1),
                "control_status": "poor" if projected_hba1c > 8 else "fair" if projected_hba1c > 7 else "good",
                "complication_risk": complication_risk,
                "intervention_needed": projected_hba1c > 8.0
            })
        
        return {
            "condition": "Type 2 Diabetes",
            "current_hba1c": current_hba1c,
            "progression_timeline": progression_timeline,
            "key_milestones": self._identify_diabetes_milestones(progression_timeline),
            "prevention_strategies": self._suggest_prevention_strategies(current_hba1c)
        }
    
    async def _model_anemia_progression(
        self,
        current_state: Dict[str, Any],
        patient_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Model anemia progression."""
        current_hb = current_state.get("labs", {}).get("hemoglobin", 10.0)
        cause = current_state.get("cause", "unknown")
        
        # Without treatment, anemia typically worsens
        weekly_decline = 0.2  # g/dL per week
        
        if "bleeding" in cause.lower():
            weekly_decline = 0.4  # Faster decline with bleeding
        
        progression_timeline = []
        for week in range(1, 13):  # 12-week projection
            projected_hb = current_hb - (weekly_decline * week)
            projected_hb = max(4.0, projected_hb)  # Don't go below critical level
            
            symptoms = self._assess_anemia_symptoms(projected_hb)
            transfusion_needed = projected_hb < 7.0
            
            progression_timeline.append({
                "week": week,
                "projected_hemoglobin": round(projected_hb, 1),
                "symptoms": symptoms,
                "transfusion_needed": transfusion_needed,
                "intervention_urgency": "critical" if transfusion_needed else "high" if projected_hb < 8 else "moderate"
            })
        
        return {
            "condition": "Iron-Deficiency Anemia",
            "current_hemoglobin": current_hb,
            "progression_timeline": progression_timeline,
            "time_to_critical": self._calculate_time_to_critical(progression_timeline),
            "intervention_recommendations": "Start iron supplementation immediately to prevent progression"
        }
    
    async def _generic_progression_model(
        self,
        condition: str,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generic disease progression model."""
        return {
            "condition": condition,
            "progression": "generic_model",
            "message": f"Specific progression model for {condition} not yet implemented",
            "general_principle": "Most chronic conditions progress without intervention"
        }
    
    def _load_progression_models(self) -> Dict:
        """Load disease progression models."""
        return {
            "diabetes": {"annual_hba1c_increase": 0.1},
            "anemia": {"weekly_hb_decline": 0.2}
        }
    
    def _prioritize_treatments(
        self,
        treatments: List[Dict],
        constraints: Dict
    ) -> List[Dict]:
        """Prioritize treatments based on urgency and dependencies."""
        return sorted(treatments, key=lambda x: x.get("urgency", 5), reverse=True)
    
    def _calculate_optimal_timing(
        self,
        treatment: Dict,
        current_date: datetime,
        constraints: Dict
    ) -> datetime:
        """Calculate optimal date for treatment."""
        min_delay = treatment.get("min_delay_days", 0)
        return current_date + timedelta(days=min_delay)
    
    def _identify_key_events(self, predictions: List) -> List[str]:
        """Identify key milestones in prediction timeline."""
        events = []
        for p in predictions:
            if p["predicted_hemoglobin"] >= 12.0 and events.count("normal") == 0:
                events.append(f"Day {p['day']}: Hemoglobin reaches normal range")
        return events
    
    def _generate_timeline_recommendations(self, predictions: List) -> List[str]:
        """Generate timeline-based recommendations."""
        recs = []
        if predictions and predictions[0]["predicted_hemoglobin"] < 8:
            recs.append("Continue close monitoring - check labs weekly")
        if predictions and predictions[-1]["predicted_hemoglobin"] >= 12:
            recs.append("Expected to reach target in projected timeframe")
        return recs
    
    def _calculate_complication_risk(self, hba1c: float, years: int) -> str:
        """Calculate diabetes complication risk."""
        if hba1c > 9:
            return "very_high"
        elif hba1c > 8:
            return "high"
        elif hba1c > 7:
            return "moderate"
        else:
            return "low"
    
    def _identify_diabetes_milestones(self, timeline: List) -> List[str]:
        """Identify key diabetes progression milestones."""
        milestones = []
        for entry in timeline:
            if entry["projected_hba1c"] > 8.0 and "Medication intensification needed" not in milestones:
                milestones.append(f"Year {entry['year']}: Medication intensification needed")
        return milestones
    
    def _suggest_prevention_strategies(self, current_hba1c: float) -> List[str]:
        """Suggest strategies to prevent progression."""
        strategies = ["Regular exercise", "Dietary modifications", "Weight loss if BMI >25"]
        if current_hba1c > 7:
            strategies.append("Medication optimization")
        return strategies
    
    def _assess_anemia_symptoms(self, hb: float) -> str:
        """Assess anemia symptom severity."""
        if hb < 7:
            return "severe"
        elif hb < 10:
            return "moderate"
        elif hb < 12:
            return "mild"
        else:
            return "minimal"
    
    def _calculate_time_to_critical(self, timeline: List) -> Optional[int]:
        """Calculate weeks until critical threshold."""
        for entry in timeline:
            if entry["transfusion_needed"]:
                return entry["week"]
        return None


# Export functions
async def model_disease_progression(
    condition: str,
    current_state: Dict[str, Any],
    patient_factors: Dict[str, Any]
) -> Dict[str, Any]:
    """Model disease progression over time."""
    engine = TemporalReasoningEngine()
    return await engine.model_disease_progression(condition, current_state, patient_factors)


async def optimize_treatment_timeline(
    treatments: List[Dict[str, Any]],
    constraints: Dict[str, Any]
) -> Dict[str, Any]:
    """Optimize treatment timing."""
    engine = TemporalReasoningEngine()
    return await engine.optimize_treatment_timeline(treatments, constraints)


async def predict_future_state(
    patient_id: str,
    current_state: Dict[str, Any],
    days_ahead: int = 30
) -> Dict[str, Any]:
    """Predict patient state in the future."""
    engine = TemporalReasoningEngine()
    return await engine.predict_future_state(patient_id, current_state, days_ahead)
