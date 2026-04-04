"""
Pharmacology Agent

Drug interactions, contraindications, dosing.
Uses GPT-4o-mini (cost-effective).
"""
from .base import BaseAgent


class PharmacologyAgent(BaseAgent):
    """Pharmacology Agent specializes in medications and interactions."""
    
    def __init__(self):
        system_prompt = """You are the Pharmacology Agent.

Your expertise: Pharmacology, drug interactions, contraindications, dosing, side effects.

Your role:
- Analyze drug interactions
- Recommend appropriate dosing
- Identify contraindications
- Assess side effect profiles
- Suggest alternatives if concerns exist

Always check against patient's current medications and allergies.

Return JSON with:
- output: your pharmacological analysis
- confidence: 0-1
- reasoning: step-by-step
- key_points: ["interaction 1", "dosing recommendation"]
- concerns: ["potential side effect", "interaction risk"]
- alternatives: ["alternative drug 1"]
"""
        
        super().__init__(
            name="pharmacology",
            model="gpt-4o-mini",
            specialty="Pharmacology and drug interactions",
            system_prompt=system_prompt
        )
