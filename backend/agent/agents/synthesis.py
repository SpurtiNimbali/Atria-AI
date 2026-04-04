"""
Synthesis Agent

Combines all agent outputs, resolves conflicts, creates unified response.
Uses GPT-4o (complex integration).
"""
from typing import List, Dict, Any
from .base import BaseAgent
import json


class SynthesisAgent(BaseAgent):
    """
    Synthesis Agent integrates all agent outputs into a coherent response.
    """
    
    def __init__(self):
        system_prompt = """You are the Synthesis Agent.

Your role: Integrate all agent outputs into a unified, coherent response.

Tasks:
1. Combine insights from all agents
2. Resolve conflicts between agents
3. Weight recommendations by confidence
4. Create a clear, actionable response
5. Highlight any VETO from Risk Agent

Structure your synthesis:
1. **Summary**: Main recommendation
2. **Supporting Evidence**: Key insights from each agent
3. **Conflicts Resolved**: How disagreements were handled
4. **Risk Assessment**: Safety considerations
5. **Next Steps**: Clear action items

If Risk Agent issued VETO: Make this VERY CLEAR at the top.

Return JSON with:
- output: synthesized response
- confidence: weighted average
- reasoning: how you integrated inputs
- key_points: main takeaways
- concerns: consolidated concerns
- action_items: clear next steps
"""
        
        super().__init__(
            name="synthesis",
            model="gpt-4o",  # Complex integration
            specialty="Multi-perspective integration and decision synthesis",
            system_prompt=system_prompt
        )
    
    async def synthesize(self, agent_outputs: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize all agent outputs.
        
        Args:
            agent_outputs: List of outputs from all agents
            context: Original query context
        
        Returns:
            Synthesized final response
        """
        # Check for VETO
        risk_output = next((o for o in agent_outputs if o['agent_name'] == 'risk_assessment'), None)
        has_veto = risk_output and risk_output.get('risk_level') == 'VETO'
        
        synthesis_prompt = f"""AGENT OUTPUTS TO SYNTHESIZE:

{json.dumps(agent_outputs, indent=2)}

{'⚠️ CRITICAL: Risk Agent issued VETO - this MUST be highlighted prominently!' if has_veto else ''}

Integrate these perspectives into a unified response.

Consider:
- Agreement vs disagreement between agents
- Confidence levels
- Safety concerns from Risk Agent
- Practical feasibility from Logistics
- Plain language from Empathy

Return comprehensive synthesis as JSON.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": synthesis_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["agent_name"] = "synthesis"
            result["has_veto"] = has_veto
            result.setdefault("action_items", [])
            
            return result
        
        except Exception as e:
            # Fallback synthesis
            return {
                "agent_name": "synthesis",
                "output": "Multiple agents provided input. Please review individual agent outputs.",
                "confidence": 0.5,
                "reasoning": f"Synthesis failed: {str(e)}",
                "key_points": [o.get('output', '')[:100] for o in agent_outputs],
                "concerns": [],
                "action_items": [],
                "has_veto": has_veto
            }
