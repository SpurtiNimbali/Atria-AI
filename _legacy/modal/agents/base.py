"""
Base Agent Class

All specialized agents inherit from this base.
"""
import os
from typing import Dict, Any, Optional
from openai import OpenAI
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()  # Try current directory


class BaseAgent:
    """
    Base class for all agents in the system.
    
    Each agent has:
    - name: Unique identifier
    - model: LLM model to use (gpt-4o for critical, gpt-4o-mini for others)
    - specialty: What this agent knows
    - system_prompt: Agent's personality and expertise
    """
    
    def __init__(self, name: str, model: str, specialty: str, system_prompt: str):
        self.name = name
        self.model = model
        self.specialty = specialty
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.execution_count = 0
    
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent's specific task.
        
        Args:
            task: The specific question/task for this agent
            context: Patient context, retrieved docs, other agent outputs
        
        Returns:
            {
                "agent_name": str,
                "output": str,
                "confidence": float,
                "reasoning": str,
                "key_points": list,
                "concerns": list,
                "timestamp": str
            }
        """
        self.execution_count += 1
        
        prompt = self._build_prompt(task, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "agent_name": self.name,
                "output": result.get("output", ""),
                "confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", ""),
                "key_points": result.get("key_points", []),
                "concerns": result.get("concerns", []),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "agent_name": self.name,
                "output": f"Error: {str(e)}",
                "confidence": 0.0,
                "reasoning": "Agent execution failed",
                "key_points": [],
                "concerns": [f"Execution error: {str(e)}"],
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """
        Build the prompt for this agent.
        Override in subclasses for agent-specific formatting.
        """
        patient_context = context.get("patient_context", "")
        retrieved_docs = context.get("retrieved_docs", [])
        other_agent_outputs = context.get("other_agent_outputs", [])
        
        prompt = f"""TASK: {task}

PATIENT CONTEXT:
{patient_context}

RETRIEVED DOCUMENTS:
{self._format_docs(retrieved_docs)}

OTHER AGENT INSIGHTS:
{self._format_agent_outputs(other_agent_outputs)}

Please analyze this and return JSON with:
{{
    "output": "your main response",
    "confidence": 0.0-1.0,
    "reasoning": "step-by-step reasoning",
    "key_points": ["point 1", "point 2"],
    "concerns": ["concern 1", "concern 2"]
}}
"""
        return prompt
    
    def _format_docs(self, docs: list) -> str:
        """Format retrieved documents."""
        if not docs:
            return "No documents retrieved."
        
        formatted = []
        for i, doc in enumerate(docs[:5], 1):
            formatted.append(f"[Doc {i}] {doc.get('resource_type', 'Unknown')}: {doc.get('text', '')[:200]}")
        return "\n\n".join(formatted)
    
    def _format_agent_outputs(self, outputs: list) -> str:
        """Format outputs from other agents."""
        if not outputs:
            return "No other agent insights yet."
        
        formatted = []
        for output in outputs:
            formatted.append(f"[{output['agent_name']}]: {output['output'][:150]}")
        return "\n\n".join(formatted)
    
    async def critique(self, other_agent_output: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Critique another agent's output (for debate mode).
        
        Returns:
            {
                "agrees_with": list,
                "disagrees_with": list,
                "concerns": list,
                "suggestions": list
            }
        """
        critique_prompt = f"""You are {self.name} with specialty in {self.specialty}.

Review this output from {other_agent_output['agent_name']}:

OUTPUT: {other_agent_output['output']}
REASONING: {other_agent_output['reasoning']}

From your expertise in {self.specialty}, provide:
1. What you AGREE with
2. What you DISAGREE with or find concerning
3. Specific concerns from your specialty
4. Suggestions for improvement

Return JSON:
{{
    "agrees_with": ["point 1", "point 2"],
    "disagrees_with": ["point 1", "point 2"],
    "concerns": ["concern 1"],
    "suggestions": ["suggestion 1"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": critique_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            return {
                "agrees_with": [],
                "disagrees_with": [],
                "concerns": [f"Critique failed: {str(e)}"],
                "suggestions": []
            }
    
    async def refine(self, original_output: Dict[str, Any], critiques: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine output based on critiques (for debate mode).
        """
        refine_prompt = f"""You are {self.name}.

Your original output: {original_output['output']}

You received these critiques:
{json.dumps(critiques, indent=2)}

Refine your position considering these critiques. Return JSON with same format as execute().
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": refine_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            result["agent_name"] = self.name
            result["timestamp"] = datetime.now().isoformat()
            return result
        
        except Exception as e:
            return original_output  # Return original if refinement fails
