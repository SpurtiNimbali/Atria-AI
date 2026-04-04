"""
Medical Expert Agent

Clinical knowledge, procedures, protocols.
Uses GPT-4o-mini (cost-effective).
"""
from .base import BaseAgent


class MedicalExpertAgent(BaseAgent):
    """Medical Expert provides clinical reasoning and recommendations."""
    
    def __init__(self):
        system_prompt = """You are the Medical Expert Agent.

Your expertise: Clinical medicine, procedures, protocols, evidence-based practice.

Your role:
- Provide clinical analysis
- Explain medical concepts
- Recommend evidence-based approaches
- Cite clinical guidelines when relevant
- Identify alternatives

Always structure your response with:
1. Clinical Assessment
2. Recommendation
3. Alternatives
4. Rationale (evidence-based)

Return JSON with output, confidence (0-1), reasoning, key_points, concerns.
"""
        
        super().__init__(
            name="medical_expert",
            model="gpt-4o-mini",
            specialty="Clinical medicine and evidence-based practice",
            system_prompt=system_prompt
        )
