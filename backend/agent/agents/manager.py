"""
Agent Manager

Orchestrates multi-agent execution with 4 strategies:
- Parallel: All agents simultaneously (fast)
- Sequential: Agents in order (thorough)
- Debate: Agents critique each other (robust)
- Consensus: All must agree (safety-critical)
"""
import asyncio
from typing import Dict, Any, AsyncIterator, List
from datetime import datetime
import json

from .orchestrator import OrchestratorAgent
from .medical_expert import MedicalExpertAgent
from .pharmacology import PharmacologyAgent
from .logistics import LogisticsAgent
from .empathy import EmpathyAgent
from .risk_assessment import RiskAssessmentAgent
from .research import ResearchAgent
from .synthesis import SynthesisAgent

# For EHR retrieval
from elastic_client import get_elastic_client
from search import hybrid_search
from embeddings import generate_embedding


class AgentManager:
    """
    Manages multi-agent orchestration.
    
    Flow:
    1. Orchestrator analyzes query
    2. Execute strategy (parallel/sequential/debate/consensus)
    3. Synthesis agent combines outputs
    4. Stream everything to frontend
    """
    
    def __init__(self):
        self.agents = {
            'orchestrator': OrchestratorAgent(),
            'medical_expert': MedicalExpertAgent(),
            'pharmacology': PharmacologyAgent(),
            'logistics': LogisticsAgent(),
            'empathy': EmpathyAgent(),
            'risk_assessment': RiskAssessmentAgent(),
            'research': ResearchAgent(),
            'synthesis': SynthesisAgent()
        }
        self.es = get_elastic_client()
    
    async def process_query(self, patient_id: str, user_query: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Main entry point - processes query and streams updates.
        
        Yields events:
        - orchestrator_thinking
        - execution_plan
        - agent_started
        - agent_complete
        - debate_round (if debate)
        - final_response
        """
        # Step 1: Get patient context from EHR
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Loading patient context",
            "content": f"Retrieving EHR for patient {patient_id}..."
        }
        
        patient_context = await self._get_patient_context(patient_id, user_query)
        
        yield {
            "type": "reasoning_step",
            "emoji": "📄",
            "step": "Patient context loaded",
            "content": f"Retrieved {len(patient_context.get('retrieved_docs', []))} documents"
        }
        
        # Step 2: Orchestrator plans execution
        yield {
            "type": "reasoning_step",
            "emoji": "🤔",
            "step": "Orchestrator analyzing query",
            "content": "Determining optimal execution strategy..."
        }
        
        execution_plan = await self.agents['orchestrator'].plan(user_query, patient_context)
        
        yield {
            "type": "execution_plan",
            "plan": execution_plan
        }
        
        yield {
            "type": "reasoning_step",
            "emoji": "📋",
            "step": f"Strategy: {execution_plan['strategy'].upper()}",
            "content": execution_plan['reasoning']
        }
        
        # Step 3: Execute strategy
        strategy = execution_plan['strategy']
        agent_outputs = []
        
        if strategy == 'parallel':
            async for event in self._parallel_execution(execution_plan, patient_context):
                if event['type'] == 'agent_complete':
                    agent_outputs.append(event['output'])
                yield event
        
        elif strategy == 'sequential':
            async for event in self._sequential_execution(execution_plan, patient_context):
                if event['type'] == 'agent_complete':
                    agent_outputs.append(event['output'])
                yield event
        
        elif strategy == 'debate':
            async for event in self._debate_execution(execution_plan, patient_context):
                if event['type'] == 'agent_complete':
                    agent_outputs.append(event['output'])
                yield event
        
        elif strategy == 'consensus':
            async for event in self._consensus_execution(execution_plan, patient_context):
                if event['type'] == 'agent_complete':
                    agent_outputs.append(event['output'])
                yield event
        
        # Step 4: Synthesis
        yield {
            "type": "reasoning_step",
            "emoji": "🧩",
            "step": "Synthesizing agent outputs",
            "content": f"Integrating insights from {len(agent_outputs)} agents..."
        }
        
        final_output = await self.agents['synthesis'].synthesize(agent_outputs, patient_context)
        
        yield {
            "type": "final_response",
            "output": final_output
        }
        
        # Also send as regular response for frontend compatibility
        yield {
            "type": "response",
            "content": final_output['output']
        }
        
        # Send citations
        if patient_context.get('citations'):
            yield {
                "type": "citations",
                "citations": patient_context['citations']
            }
    
    async def _get_patient_context(self, patient_id: str, query: str) -> Dict[str, Any]:
        """Retrieve patient context from EHR."""
        # Generate embedding
        query_embedding = generate_embedding(query)
        
        # Search EHR
        results = hybrid_search(self.es, patient_id, query, query_embedding, k=10)
        
        # Format context
        context = {
            "patient_id": patient_id,
            "query": query,
            "retrieved_docs": results,
            "citations": [
                {
                    "id": i,
                    "resource_type": r["resource_type"],
                    "resource_id": r["resource_id"],
                    "snippet": r["text"][:300],
                    "timestamp": r["timestamp"],
                    "score": r["_score"]
                }
                for i, r in enumerate(results, 1)
            ],
            "patient_context": "\n\n".join([r["text"] for r in results[:5]])
        }
        
        return context
    
    async def _parallel_execution(self, plan: Dict, context: Dict) -> AsyncIterator[Dict]:
        """Execute all agents simultaneously."""
        agents_to_invoke = plan['agents_to_invoke']
        agent_tasks = plan.get('agent_tasks', {})
        
        # Start all agents
        for agent_name in agents_to_invoke:
            yield {
                "type": "agent_started",
                "agent": agent_name,
                "task": agent_tasks.get(agent_name, context['query'])
            }
        
        # Run in parallel
        tasks = []
        for agent_name in agents_to_invoke:
            agent = self.agents.get(agent_name)
            if agent:
                task = agent_tasks.get(agent_name, context['query'])
                tasks.append(agent.execute(task, context))
        
        # Gather results as they complete
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield {
                "type": "agent_complete",
                "agent": result['agent_name'],
                "output": result
            }
            
            # Safely extract output preview
            try:
                output_val = result.get('output', '')
                if isinstance(output_val, str):
                    preview = output_val[:200]
                else:
                    preview = str(output_val)[:200]
            except:
                preview = "Output complete"
            
            yield {
                "type": "reasoning_step",
                "emoji": "✅",
                "step": f"{result['agent_name']} complete",
                "content": preview
            }
    
    async def _sequential_execution(self, plan: Dict, context: Dict) -> AsyncIterator[Dict]:
        """Execute agents in order, each seeing previous outputs."""
        agents_to_invoke = plan['agents_to_invoke']
        agent_tasks = plan.get('agent_tasks', {})
        
        previous_outputs = []
        
        for agent_name in agents_to_invoke:
            agent = self.agents.get(agent_name)
            if not agent:
                continue
            
            yield {
                "type": "agent_started",
                "agent": agent_name,
                "task": agent_tasks.get(agent_name, context['query'])
            }
            
            # Add previous outputs to context
            context_with_history = {**context, "other_agent_outputs": previous_outputs}
            
            # Execute
            task = agent_tasks.get(agent_name, context['query'])
            result = await agent.execute(task, context_with_history)
            
            previous_outputs.append(result)
            
            yield {
                "type": "agent_complete",
                "agent": result['agent_name'],
                "output": result
            }
            
            # Safely extract output preview
            try:
                output_val = result.get('output', '')
                if isinstance(output_val, str):
                    preview = output_val[:200]
                else:
                    preview = str(output_val)[:200]
            except:
                preview = "Output complete"
            
            yield {
                "type": "reasoning_step",
                "emoji": "✅",
                "step": f"{result['agent_name']} complete",
                "content": preview
            }
    
    async def _debate_execution(self, plan: Dict, context: Dict, rounds: int = 2) -> AsyncIterator[Dict]:
        """Agents debate through multiple rounds."""
        agents_to_invoke = plan['agents_to_invoke']
        agent_tasks = plan.get('agent_tasks', {})
        
        # Round 1: Initial positions
        yield {
            "type": "reasoning_step",
            "emoji": "💬",
            "step": "Debate Round 1: Initial Positions",
            "content": "Agents present their positions..."
        }
        
        positions = []
        for agent_name in agents_to_invoke:
            agent = self.agents.get(agent_name)
            if not agent:
                continue
            
            task = agent_tasks.get(agent_name, context['query'])
            position = await agent.execute(task, context)
            positions.append(position)
            
            yield {
                "type": "agent_complete",
                "agent": agent_name,
                "output": position
            }
        
        # Round 2: Critiques
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Debate Round 2: Critiques",
            "content": "Agents critique each other's positions..."
        }
        
        critiques = []
        for i, position in enumerate(positions):
            agent = self.agents[position['agent_name']]
            
            # Get critiques from other agents
            agent_critiques = []
            for other_position in positions:
                if other_position['agent_name'] != position['agent_name']:
                    other_agent = self.agents[other_position['agent_name']]
                    critique = await other_agent.critique(position, context)
                    agent_critiques.append({
                        "from": other_agent.name,
                        "critique": critique
                    })
            
            critiques.append({
                "agent": position['agent_name'],
                "received_critiques": agent_critiques
            })
        
        # Round 3: Refinement
        yield {
            "type": "reasoning_step",
            "emoji": "🔄",
            "step": "Debate Round 3: Refinement",
            "content": "Agents refine their positions..."
        }
        
        refined_positions = []
        for i, position in enumerate(positions):
            agent = self.agents[position['agent_name']]
            agent_critiques = critiques[i]['received_critiques']
            
            refined = await agent.refine(position, agent_critiques, context)
            refined_positions.append(refined)
            
            yield {
                "type": "agent_complete",
                "agent": refined['agent_name'],
                "output": refined
            }
    
    async def _consensus_execution(self, plan: Dict, context: Dict) -> AsyncIterator[Dict]:
        """All agents must agree, risk agent can veto."""
        yield {
            "type": "reasoning_step",
            "emoji": "🤝",
            "step": "Consensus Mode: All agents must agree",
            "content": "Executing safety-critical consensus..."
        }
        
        # Execute all agents (like parallel)
        async for event in self._parallel_execution(plan, context):
            yield event
        
        # Check for veto
        # (This will be handled in synthesis)
        yield {
            "type": "reasoning_step",
            "emoji": "⚖️",
            "step": "Checking for consensus",
            "content": "Verifying all agents agree..."
        }
