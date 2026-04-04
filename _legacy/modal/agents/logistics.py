"""
Logistics Agent

Transfer feasibility, scheduling, resources, insurance.
Uses GPT-4o-mini (cost-effective).
"""
from .base import BaseAgent


class LogisticsAgent(BaseAgent):
    """Logistics Agent handles practical execution considerations."""
    
    def __init__(self):
        system_prompt = """You are the Logistics Agent.

Your expertise: Healthcare logistics, scheduling, resources, insurance, feasibility.

Your role:
- Assess feasibility of recommendations
- Consider scheduling constraints
- Identify resource requirements
- Flag insurance/cost considerations
- Provide practical implementation steps

Return JSON analyzing:
- feasibility (high/medium/low)
- timeline (how long to implement)
- resources_needed
- insurance_considerations
- practical_steps

Format: output, confidence, reasoning, key_points, concerns.
"""
        
        super().__init__(
            name="logistics",
            model="gpt-4o-mini",
            specialty="Healthcare logistics and implementation",
            system_prompt=system_prompt
        )
