"""
Orchestrator Agent

Analyzes user query and decides execution strategy.
Uses GPT-4o (critical decision-making).
"""
from typing import Dict, Any
from .base import BaseAgent
import json


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator decides:
    - Which agents to invoke
    - Execution strategy (parallel/sequential/debate/consensus)
    - Task breakdown for each agent
    """
    
    def __init__(self):
        system_prompt = """You are the Orchestrator Agent.

Your role: Analyze user queries and design the optimal execution strategy.

**Execution Strategies:**
1. PARALLEL (3-5s): Simple queries, all agents work simultaneously
   - Example: "What does hemoglobin do?"
   
2. SEQUENTIAL (10-15s): Complex queries needing ordered execution
   - Example: "What if we tried medication B?"
   - Flow: Medical Expert → Pharmacology → Risk → Logistics
   
3. DEBATE (20-30s): Controversial decisions, agents present & critique
   - Example: "Should we transfer to Stanford?"
   - 2 rounds of positions + critiques
   
4. CONSENSUS (15-25s): Safety-critical, all agents must agree
   - Example: "Is it safe to skip dialysis?"
   - Risk agent can veto

**Your output:**
Return JSON with:
{
    "strategy": "parallel|sequential|debate|consensus",
    "agents_to_invoke": ["medical_expert", "pharmacology", ...],
    "agent_tasks": {
        "medical_expert": "Analyze clinical implications...",
        "pharmacology": "Check drug interactions..."
    },
    "reasoning": "why this strategy",
    "complexity": "low|medium|high|critical",
    "estimated_time": "5s"
}

**Agent Capabilities:**
- medical_expert: Clinical knowledge, procedures, protocols
- pharmacology: Drug interactions, dosing, side effects
- logistics: Transfer feasibility, scheduling, insurance
- empathy: Plain language, emotional support
- risk_assessment: Safety gatekeeper, can VETO
- research: Clinical trials, recent studies
- synthesis: (invoked automatically at end)
"""
        
        super().__init__(
            name="orchestrator",
            model="gpt-4o",  # Critical decision-making
            specialty="Query analysis and execution planning",
            system_prompt=system_prompt
        )
    
    async def plan(self, user_query: str, patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze query and create execution plan.
        """
        prompt = f"""USER QUERY: "{user_query}"

PATIENT CONTEXT: {json.dumps(patient_context, indent=2)}

Analyze this query and design the optimal execution plan.

Consider:
- Is this a simple fact lookup? → parallel
- Is this exploring an alternative? → sequential
- Is this a controversial decision? → debate
- Is this safety-critical? → consensus

Return your execution plan as JSON.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temp for consistent planning
                response_format={"type": "json_object"}
            )
            
            plan = json.loads(response.choices[0].message.content)
            
            # Ensure required fields
            plan.setdefault("strategy", "parallel")
            plan.setdefault("agents_to_invoke", ["medical_expert", "empathy"])
            plan.setdefault("agent_tasks", {})
            plan.setdefault("reasoning", "Default execution plan")
            plan.setdefault("complexity", "medium")
            plan.setdefault("estimated_time", "10s")
            
            return plan
        
        except Exception as e:
            # Fallback plan if orchestrator fails
            return {
                "strategy": "parallel",
                "agents_to_invoke": ["medical_expert", "empathy"],
                "agent_tasks": {
                    "medical_expert": user_query,
                    "empathy": "Translate medical information to plain language"
                },
                "reasoning": f"Fallback plan due to orchestrator error: {str(e)}",
                "complexity": "medium",
                "estimated_time": "10s"
            }
