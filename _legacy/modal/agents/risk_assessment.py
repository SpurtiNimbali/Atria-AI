"""
Risk Assessment Agent

Safety gatekeeper - can VETO unsafe recommendations.
Uses GPT-4o (safety-critical).
"""
from typing import Dict, Any
from .base import BaseAgent


class RiskAssessmentAgent(BaseAgent):
    """
    Risk Assessment Agent is the safety gatekeeper.
    
    Can return:
    - SAFE: No concerns, proceed
    - CAUTION: Monitor closely
    - ESCALATE: Doctor consultation required
    - VETO: UNSAFE - do not proceed
    """
    
    def __init__(self):
        system_prompt = """You are the Risk Assessment Agent - the SAFETY GATEKEEPER.

Your role: Identify risks and VETO unsafe recommendations.

**Risk Levels:**
- SAFE: No significant concerns, proceed
- CAUTION: Monitor closely, document concerns
- ESCALATE: Doctor consultation REQUIRED
- VETO: UNSAFE - DO NOT PROCEED

**You MUST VETO if:**
- Recommendations contradict patient's documented allergies
- Drug interactions could cause serious harm
- Missing critical information for safe decision
- Recommendation outside scope of care setting
- Any life-threatening risk

**Your output:**
Return JSON:
{
    "risk_level": "SAFE|CAUTION|ESCALATE|VETO",
    "output": "explanation of risk assessment",
    "confidence": 0.9,
    "reasoning": "why this risk level",
    "key_points": ["specific safety factors"],
    "concerns": ["specific risks identified"],
    "required_monitoring": ["what to monitor"],
    "veto_reason": "if VETO, why",
    "doctor_consultation_needed": true/false
}

**Remember:** It's better to be cautious than sorry. When in doubt, ESCALATE.
"""
        
        super().__init__(
            name="risk_assessment",
            model="gpt-4o",  # Safety-critical
            specialty="Clinical safety and risk management",
            system_prompt=system_prompt
        )
    
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk assessment."""
        result = await super().execute(task, context)
        
        # Ensure risk_level is present
        if "risk_level" not in result:
            result["risk_level"] = "CAUTION"  # Default to cautious
        
        # Add risk-specific fields
        result.setdefault("required_monitoring", [])
        result.setdefault("veto_reason", "")
        result.setdefault("doctor_consultation_needed", False)
        
        return result
    
    def _build_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """Build risk-specific prompt."""
        patient_context = context.get("patient_context", "")
        retrieved_docs = context.get("retrieved_docs", [])
        other_agent_outputs = context.get("other_agent_outputs", [])
        
        prompt = f"""RISK ASSESSMENT TASK: {task}

PATIENT CONTEXT:
{patient_context}

PATIENT DOCUMENTS (Check for allergies, contraindications, current meds):
{self._format_docs(retrieved_docs)}

OTHER AGENT RECOMMENDATIONS:
{self._format_agent_outputs(other_agent_outputs)}

Perform a thorough safety assessment. Check:
1. Allergies and contraindications
2. Drug interactions
3. Missing critical information
4. Appropriateness for care setting
5. Any life-threatening risks

Return JSON with risk_level (SAFE/CAUTION/ESCALATE/VETO) and detailed reasoning.
"""
        return prompt
