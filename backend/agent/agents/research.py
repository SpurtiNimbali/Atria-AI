"""
Research Agent

Clinical trials, recent studies, experimental treatments.
Uses GPT-4o-mini (cost-effective).
"""
from .base import BaseAgent


class ResearchAgent(BaseAgent):
    """Research Agent provides evidence from clinical trials and studies."""
    
    def __init__(self):
        system_prompt = """You are the Research Agent.

Your expertise: Clinical research, trials, evidence-based medicine, experimental treatments.

Your role:
- Reference relevant clinical trials
- Cite recent research findings
- Discuss experimental or emerging treatments
- Provide evidence quality assessment
- Mention limitations of current evidence

Always include:
- Level of evidence (strong/moderate/weak)
- Study types (RCT, observational, case studies)
- Any contradictory findings

Return JSON with output, confidence, reasoning, key_points, concerns.
"""
        
        super().__init__(
            name="research",
            model="gpt-4o-mini",
            specialty="Clinical research and evidence",
            system_prompt=system_prompt
        )
