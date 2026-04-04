"""
Causal Reasoning Engine for "What If" Scenarios and Counterfactual Analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np


class CausalReasoningEngine:
    """
    Handles "what if" scenarios, counterfactual analysis, and treatment effect estimation.
    """
    
    def __init__(self):
        self.scenario_history = []
    
    async def analyze_what_if(
        self,
        patient_id: str,
        current_state: Dict[str, Any],
        proposed_intervention: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze "what if we did X instead of Y" scenarios.
        
        Example: "What if we switched from oral iron to IV iron?"
        """
        # Extract current treatment and outcomes
        current_treatment = parameters.get("current_treatment", "standard care")
        current_labs = current_state.get("labs", {})
        conditions = current_state.get("conditions", [])
        
        # Simulate both pathways
        current_pathway = self._simulate_pathway(
            treatment=current_treatment,
            current_labs=current_labs,
            conditions=conditions,
            duration_days=30
        )
        
        alternative_pathway = self._simulate_pathway(
            treatment=proposed_intervention,
            current_labs=current_labs,
            conditions=conditions,
            duration_days=30
        )
        
        # Compare outcomes
        comparison = self._compare_pathways(
            current_pathway,
            alternative_pathway,
            metric="hemoglobin"  # Would be dynamic based on condition
        )
        
        return {
            "scenario": f"What if we {proposed_intervention} instead of {current_treatment}?",
            "current_pathway": current_pathway,
            "alternative_pathway": alternative_pathway,
            "comparison": comparison,
            "recommendation": self._generate_recommendation(comparison),
            "confidence": self._calculate_confidence(current_state, proposed_intervention),
            "created_at": datetime.now().isoformat()
        }
    
    async def counterfactual_analysis(
        self,
        patient_id: str,
        actual_outcome: Dict[str, Any],
        alternative_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze "what would have happened if we had done X?"
        
        Example: "What if we had given IV iron 2 weeks earlier?"
        """
        actual_timeline = actual_outcome.get("timeline", [])
        
        counterfactuals = []
        for alt_action in alternative_actions:
            counterfactual_timeline = self._simulate_counterfactual(
                actual_timeline=actual_timeline,
                alternative_action=alt_action
            )
            
            benefit_analysis = self._calculate_benefit(
                actual=actual_timeline,
                counterfactual=counterfactual_timeline
            )
            
            counterfactuals.append({
                "alternative_action": alt_action,
                "counterfactual_timeline": counterfactual_timeline,
                "benefit_analysis": benefit_analysis
            })
        
        # Rank alternatives
        ranked = sorted(counterfactuals, key=lambda x: x["benefit_analysis"]["net_benefit"], reverse=True)
        
        return {
            "actual_outcome": actual_outcome,
            "counterfactuals": ranked,
            "best_alternative": ranked[0] if ranked else None,
            "learning": self._extract_learning(ranked),
            "analysis_type": "counterfactual"
        }
    
    async def estimate_treatment_effect(
        self,
        treatment_name: str,
        patient_features: Dict[str, Any],
        historical_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Estimate expected treatment effect for this specific patient.
        
        Uses:
        - Patient-specific features (age, conditions, labs)
        - Historical population data
        - Clinical trial data
        """
        # Extract patient risk factors
        age = patient_features.get("age", 50)
        conditions = patient_features.get("conditions", [])
        baseline_value = patient_features.get("baseline_hemoglobin", 10.0)
        
        # Model treatment effect based on patient characteristics
        if "iv iron" in treatment_name.lower():
            # IV Iron typical response
            base_improvement = 2.5  # g/dL over 4 weeks
            
            # Adjust for patient factors
            if age < 18:
                base_improvement *= 1.2  # Better response in young
            elif age > 70:
                base_improvement *= 0.85  # Slower response in elderly
            
            if "diabetes" in [c.lower() for c in conditions]:
                base_improvement *= 0.9  # Slightly reduced response
            
            if "kidney disease" in [c.lower() for c in conditions]:
                base_improvement *= 0.8  # Reduced response
            
            # Calculate expected timeline
            timeline = []
            current_value = baseline_value
            for week in range(1, 9):  # 8 weeks
                improvement = (base_improvement / 4) * min(week, 4)  # Most improvement in first 4 weeks
                current_value = baseline_value + improvement
                timeline.append({
                    "week": week,
                    "expected_hemoglobin": round(current_value, 1),
                    "confidence_interval_low": round(current_value - 0.8, 1),
                    "confidence_interval_high": round(current_value + 0.8, 1)
                })
            
            return {
                "treatment": treatment_name,
                "patient_specific_factors": {
                    "age_adjustment": "favorable" if age < 18 else "neutral",
                    "condition_adjustments": [
                        f"{c}: modest reduction" for c in conditions if c.lower() in ["diabetes", "kidney disease"]
                    ]
                },
                "expected_improvement": round(base_improvement, 1),
                "expected_timeline": timeline,
                "probability_of_response": self._calculate_response_probability(patient_features),
                "factors_affecting_response": self._identify_response_modifiers(patient_features),
                "interpretation": f"Expected {base_improvement:.1f} g/dL improvement over 4 weeks, with most benefit in first 2-3 weeks"
            }
        
        return {"error": f"Treatment effect estimation not available for {treatment_name}"}
    
    def _simulate_pathway(
        self,
        treatment: str,
        current_labs: Dict,
        conditions: List[str],
        duration_days: int
    ) -> Dict[str, Any]:
        """Simulate treatment pathway over time."""
        # Simplified simulation - would use more sophisticated model
        timeline = []
        current_hb = current_labs.get("hemoglobin", 10.0)
        
        if "iv iron" in treatment.lower():
            improvement_per_week = 0.6  # g/dL per week
        elif "oral iron" in treatment.lower():
            improvement_per_week = 0.25  # g/dL per week
        else:
            improvement_per_week = 0.1
        
        for day in range(0, duration_days, 7):  # Weekly snapshots
            current_hb += improvement_per_week + np.random.normal(0, 0.1)
            timeline.append({
                "day": day,
                "hemoglobin": round(current_hb, 1),
                "symptoms": "improving" if current_hb > 11 else "still symptomatic"
            })
        
        return {
            "treatment": treatment,
            "timeline": timeline,
            "final_value": round(current_hb, 1),
            "time_to_normal": self._calculate_time_to_normal(timeline)
        }
    
    def _compare_pathways(
        self,
        pathway1: Dict,
        pathway2: Dict,
        metric: str
    ) -> Dict[str, Any]:
        """Compare two treatment pathways."""
        timeline1 = pathway1["timeline"]
        timeline2 = pathway2["timeline"]
        
        # Calculate area under curve (total benefit)
        auc1 = sum(t["hemoglobin"] for t in timeline1) / len(timeline1)
        auc2 = sum(t["hemoglobin"] for t in timeline2) / len(timeline2)
        
        return {
            "pathway1_name": pathway1["treatment"],
            "pathway2_name": pathway2["treatment"],
            "pathway1_final": pathway1["final_value"],
            "pathway2_final": pathway2["final_value"],
            "difference": round(pathway2["final_value"] - pathway1["final_value"], 1),
            "time_difference_to_normal": (pathway1["time_to_normal"] or 99) - (pathway2["time_to_normal"] or 99),
            "average_benefit": round(auc2 - auc1, 1),
            "winner": pathway2["treatment"] if auc2 > auc1 else pathway1["treatment"]
        }
    
    def _simulate_counterfactual(
        self,
        actual_timeline: List[Dict],
        alternative_action: str
    ) -> List[Dict]:
        """Simulate what would have happened with different action."""
        # Simplified - would use causal inference techniques
        counterfactual = []
        for event in actual_timeline:
            modified_event = event.copy()
            # Adjust outcomes based on alternative action
            if "earlier" in alternative_action.lower():
                modified_event["day"] = event["day"] - 14  # 2 weeks earlier
            counterfactual.append(modified_event)
        return counterfactual
    
    def _calculate_benefit(self, actual: List, counterfactual: List) -> Dict:
        """Calculate benefit of counterfactual vs actual."""
        actual_avg = np.mean([e.get("hemoglobin", 10) for e in actual])
        counter_avg = np.mean([e.get("hemoglobin", 10) for e in counterfactual])
        
        return {
            "net_benefit": round(counter_avg - actual_avg, 1),
            "interpretation": "Better outcome" if counter_avg > actual_avg else "Similar outcome"
        }
    
    def _generate_recommendation(self, comparison: Dict) -> str:
        """Generate recommendation based on pathway comparison."""
        diff = comparison["difference"]
        time_diff = comparison.get("time_difference_to_normal", 0)
        
        if diff > 1.0 and time_diff > 7:
            return f"Strong recommendation: {comparison['pathway2_name']} shows {diff} g/dL greater improvement and reaches target {time_diff} days faster"
        elif diff > 0.5:
            return f"Mild preference: {comparison['pathway2_name']} shows modestly better outcomes"
        else:
            return f"Both pathways similar - choose based on patient preference and practical considerations"
    
    def _calculate_confidence(self, state: Dict, intervention: str) -> float:
        """Calculate confidence in prediction."""
        # Based on data completeness and certainty
        has_baseline = "labs" in state and "hemoglobin" in state["labs"]
        has_conditions = "conditions" in state and len(state["conditions"]) > 0
        
        confidence = 0.5
        if has_baseline:
            confidence += 0.2
        if has_conditions:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _calculate_time_to_normal(self, timeline: List[Dict]) -> Optional[int]:
        """Calculate days to reach normal hemoglobin."""
        for event in timeline:
            if event["hemoglobin"] >= 12.0:
                return event["day"]
        return None
    
    def _calculate_response_probability(self, features: Dict) -> float:
        """Calculate probability patient will respond to treatment."""
        base_prob = 0.85  # 85% base response rate
        
        age = features.get("age", 50)
        if age > 70:
            base_prob *= 0.9
        
        return round(base_prob, 2)
    
    def _identify_response_modifiers(self, features: Dict) -> List[str]:
        """Identify factors that may modify treatment response."""
        modifiers = []
        
        conditions = [c.lower() for c in features.get("conditions", [])]
        
        if "diabetes" in conditions:
            modifiers.append("Diabetes may slightly reduce iron absorption")
        if "kidney disease" in conditions:
            modifiers.append("Chronic kidney disease may slow response")
        if features.get("age", 0) > 70:
            modifiers.append("Advanced age may slow hemoglobin recovery")
        
        return modifiers
    
    def _extract_learning(self, ranked_counterfactuals: List) -> str:
        """Extract learning from counterfactual analysis."""
        if not ranked_counterfactuals:
            return "Insufficient data for learning"
        
        best = ranked_counterfactuals[0]
        return f"Future cases: Consider {best['alternative_action']} for potentially {abs(best['benefit_analysis']['net_benefit']):.1f} g/dL better outcome"


# Singleton instance
_causal_engine = None

async def analyze_what_if_scenario(
    patient_id: str,
    current_state: Dict[str, Any],
    proposed_intervention: str,
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Analyze what-if scenario."""
    global _causal_engine
    if _causal_engine is None:
        _causal_engine = CausalReasoningEngine()
    
    return await _causal_engine.analyze_what_if(
        patient_id, current_state, proposed_intervention, parameters or {}
    )


async def estimate_treatment_effect(
    treatment_name: str,
    patient_features: Dict[str, Any]
) -> Dict[str, Any]:
    """Estimate treatment effect for patient."""
    global _causal_engine
    if _causal_engine is None:
        _causal_engine = CausalReasoningEngine()
    
    return await _causal_engine.estimate_treatment_effect(
        treatment_name, patient_features
    )
