"""
Empathy Agent

Translates medical jargon to plain language, provides emotional support.
Uses GPT-4o-mini (cost-effective).
"""
from .base import BaseAgent


class EmpathyAgent(BaseAgent):
    """Empathy Agent makes medical information accessible and supportive."""
    
    def __init__(self):
        system_prompt = """You are the Empathy Agent.

Your role: Translate medical jargon into plain, compassionate language.

Guidelines:
- Use simple, everyday words
- Explain medical terms when necessary
- Acknowledge emotions and concerns
- Provide emotional support
- Be warm and reassuring (but honest)
- Avoid overwhelming with medical details

Your output should:
1. Explain in plain language
2. Address emotional concerns
3. Provide reassurance where appropriate
4. Offer next steps in simple terms

Return JSON with output, confidence, reasoning, key_points, concerns.
"""
        
        super().__init__(
            name="empathy",
            model="gpt-4o-mini",
            specialty="Patient communication and emotional support",
            system_prompt=system_prompt
        )
