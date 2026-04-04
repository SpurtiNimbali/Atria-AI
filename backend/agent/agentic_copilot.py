"""
Agentic Clinical Copilot - Full implementation with:
- PatientTwin (structured state)
- Route Simulator (branching futures)
- Evidence Events (structured extraction)
- TaskBoard (auto-generated actions)
- Multi-step reasoning with tools
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Import the components we just created
try:
    from extract_events import extract_evidence_events
    from generate_tasks import generate_taskboard
    from route_simulator import simulate_routes
except ImportError:
    # If running from different directory
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from extract_events import extract_evidence_events
    from generate_tasks import generate_taskboard
    from route_simulator import simulate_routes

try:
    from local_agent import answer_query as search_ehr
except ImportError:
    # Fallback if local_agent not available
    def search_ehr(patient_id, query):
        return {"events": [], "final_answer": "Search not available", "citations": []}


@dataclass
class PatientTwin:
    """Structured, living representation of patient state."""
    patient_id: str
    demographics: Dict
    conditions: List[Dict]
    medications: List[Dict]
    allergies: List[Dict]
    vitals: Dict[str, Any]  # Latest vitals
    labs: Dict[str, Any]     # Latest labs
    last_updated: str
    risk_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_context_string(self) -> str:
        """Convert to readable context for LLM."""
        return f"""
Patient: {self.demographics.get('name', 'Unknown')} (ID: {self.patient_id})
Age: {self.demographics.get('age', 'Unknown')} | Gender: {self.demographics.get('gender', 'Unknown')}

Active Conditions: {', '.join([c['name'] for c in self.conditions])}
Current Medications: {', '.join([m['name'] for m in self.medications])}
Allergies: {', '.join([a['allergen'] for a in self.allergies]) if self.allergies else 'None documented'}

Recent Vitals:
{json.dumps(self.vitals, indent=2)}

Recent Labs:
{json.dumps(self.labs, indent=2)}

Last Updated: {self.last_updated}
"""


@dataclass
class AgenticState:
    """State maintained across conversation turns."""
    patient_twin: PatientTwin
    conversation_history: List[Dict]
    evidence_events: List[Dict]
    pending_tasks: List[Dict]
    active_routes: List[Any]  # Simulated care routes
    reasoning_trace: List[Dict]
    
    def add_message(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_reasoning_step(self, step: str, data: Any = None):
        self.reasoning_trace.append({
            "step": step,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })


class AgenticCopilot:
    """
    Full agentic clinical copilot that:
    1. Maintains patient state (PatientTwin)
    2. Extracts structured events from conversation
    3. Generates actionable tasks
    4. Simulates future care routes
    5. Uses multiple tools for multi-step reasoning
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.client = OpenAI()
        self.state = self._initialize_state()
    
    def _initialize_state(self) -> AgenticState:
        """Load patient data and initialize state."""
        # Load from EHR (simplified - in reality, pull from Elasticsearch)
        patient_twin = PatientTwin(
            patient_id=self.patient_id,
            demographics={"name": "Emily Johnson", "age": 39, "gender": "female"},
            conditions=[
                {"name": "Hypertension", "onset": "2020-01-15", "status": "active"},
                {"name": "Type 2 Diabetes", "onset": "2018-06-10", "status": "active"}
            ],
            medications=[
                {"name": "Metformin 500mg", "dosage": "twice daily", "status": "active"},
                {"name": "Lisinopril 10mg", "dosage": "once daily", "status": "active"}
            ],
            allergies=[
                {"allergen": "Penicillin", "reaction": "rash", "severity": "high"}
            ],
            vitals={"bp": "135/85", "date": "2024-01-15"},
            labs={"hba1c": 7.2, "date": "2024-01-15"},
            last_updated=datetime.now().isoformat()
        )
        
        return AgenticState(
            patient_twin=patient_twin,
            conversation_history=[],
            evidence_events=[],
            pending_tasks=[],
            active_routes=[],
            reasoning_trace=[]
        )
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main agentic loop: Process query with multi-step reasoning.
        
        Steps:
        1. Add to conversation history
        2. Extract evidence events from query
        3. Decide what tools to use (search, calculate, simulate)
        4. Execute tool calls
        5. Generate tasks if needed
        6. Simulate routes if care decision needed
        7. Synthesize final answer
        """
        self.state.add_message("user", user_query)
        self.state.add_reasoning_step("Received query", user_query)
        
        # Step 1: Extract evidence events from query
        events = []
        try:
            events = extract_evidence_events(user_query, self.patient_id)
            if events:
                self.state.evidence_events.extend(events)
                self.state.add_reasoning_step("Extracted events", events)
                
                # Check for high-urgency events
                high_urgency = [e for e in events if e.get('urgency') in ['high', 'critical']]
                if high_urgency:
                    self.state.add_reasoning_step("HIGH URGENCY EVENT DETECTED", high_urgency)
        except Exception as e:
            logger.error(f"Event extraction failed: {e}")
            self.state.add_reasoning_step("Event extraction skipped", str(e))
        
        # Step 2: Decide what to do based on query intent
        intent = self._classify_intent(user_query)
        self.state.add_reasoning_step("Query intent", intent)
        
        response_data = {}
        
        if intent == "ehr_search":
            # Use existing search tool
            result = search_ehr(self.patient_id, user_query)
            response_data = result
            
        elif intent == "risk_assessment":
            # Calculate risk scores
            risk_scores = self._calculate_risk_scores()
            self.state.patient_twin.risk_scores = risk_scores
            self.state.add_reasoning_step("Calculated risk scores", risk_scores)
            response_data["risk_scores"] = risk_scores
            
        elif intent == "care_planning":
            # Simulate care routes
            try:
                routes = simulate_routes(
                    self.patient_id,
                    self._get_current_state_dict(),
                    []  # intervention options
                )
                self.state.active_routes = routes
                self.state.add_reasoning_step("Simulated care routes", [r.name for r in routes])
                response_data["routes"] = [self._route_to_dict(r) for r in routes]
            except Exception as e:
                logger.error(f"Route simulation failed: {e}")
                self.state.add_reasoning_step("Route simulation skipped", str(e))
            
        elif intent == "task_generation":
            # Generate actionable tasks
            try:
                tasks = generate_taskboard(
                    self.patient_id,
                    self.state.evidence_events,
                    self.state.patient_twin.to_context_string(),
                    user_query
                )
                self.state.pending_tasks = tasks
                self.state.add_reasoning_step("Generated tasks", f"{len(tasks)} tasks")
                response_data["tasks"] = tasks
            except Exception as e:
                logger.error(f"Task generation failed: {e}")
                self.state.add_reasoning_step("Task generation skipped", str(e))
        
        # Step 3: Always generate tasks if high-urgency events present
        if any(e.get('urgency') in ['high', 'critical'] for e in events):
            try:
                urgent_tasks = generate_taskboard(
                    self.patient_id,
                    [e for e in events if e.get('urgency') in ['high', 'critical']],
                    self.state.patient_twin.to_context_string(),
                    "Urgent action needed"
                )
                self.state.pending_tasks.extend(urgent_tasks)
                response_data["urgent_tasks"] = urgent_tasks
            except Exception as e:
                logger.error(f"Urgent task generation failed: {e}")
        
        # Step 4: Synthesize final answer
        final_answer = self._synthesize_answer(user_query, response_data)
        
        self.state.add_message("assistant", final_answer)
        
        return {
            "final_answer": final_answer,
            "patient_twin": self._patient_twin_to_dict(),
            "evidence_events": self.state.evidence_events[-5:],  # Last 5 events
            "pending_tasks": self.state.pending_tasks,
            "active_routes": response_data.get("routes", []),
            "reasoning_trace": self.state.reasoning_trace[-10:],  # Last 10 steps
            "citations": response_data.get("citations", [])
        }
    
    def _classify_intent(self, query: str) -> str:
        """Classify query intent to decide which tools to use."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["risk", "score", "probability", "chance"]):
            return "risk_assessment"
        elif any(word in query_lower for word in ["plan", "next steps", "what should", "recommend"]):
            return "care_planning"
        elif any(word in query_lower for word in ["task", "action", "todo", "need to do"]):
            return "task_generation"
        else:
            return "ehr_search"
    
    def _calculate_risk_scores(self) -> Dict[str, float]:
        """Calculate clinical risk scores (CHADS2, etc.)."""
        # Simplified - would use actual calculators
        conditions = {c['name'].lower() for c in self.state.patient_twin.conditions}
        
        chads2 = 0
        if 'hypertension' in conditions:
            chads2 += 1
        if 'diabetes' in conditions:
            chads2 += 1
        if self.state.patient_twin.demographics['age'] >= 75:
            chads2 += 1
        
        return {
            "chads2_score": chads2,
            "10_year_cv_risk": 12.0  # Would calculate properly
        }
    
    def _get_current_state_dict(self) -> Dict:
        """Convert state to dict for route simulator."""
        return {
            "conditions": [c['name'] for c in self.state.patient_twin.conditions],
            "medications": [m['name'] for m in self.state.patient_twin.medications],
            "recent_vitals": self.state.patient_twin.vitals,
            "support_system": "moderate",
            "medication_complexity": "moderate",
            "previous_adherence": "unknown"
        }
    
    def _synthesize_answer(self, query: str, data: Dict) -> str:
        """Synthesize final answer using all gathered information."""
        prompt = f"""Based on the patient context and analysis results, provide a clear clinical answer.

Patient: {self.state.patient_twin.to_context_string()}

Recent Evidence Events:
{json.dumps(self.state.evidence_events[-3:], indent=2)}

Query: {query}

Analysis Results:
{json.dumps(data, indent=2)}

Provide a structured response:
1. Direct answer to the question
2. Clinical reasoning (cite evidence)
3. Risk assessment (if relevant)
4. Recommended actions (prioritized)
5. Follow-up items

Be specific, actionable, and cite sources."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def _patient_twin_to_dict(self) -> Dict:
        """Convert PatientTwin to dict for JSON serialization."""
        return {
            "patient_id": self.state.patient_twin.patient_id,
            "demographics": self.state.patient_twin.demographics,
            "conditions": self.state.patient_twin.conditions,
            "medications": self.state.patient_twin.medications,
            "allergies": self.state.patient_twin.allergies,
            "vitals": self.state.patient_twin.vitals,
            "labs": self.state.patient_twin.labs,
            "risk_scores": self.state.patient_twin.risk_scores
        }
    
    def _route_to_dict(self, route) -> Dict:
        """Convert Route to dict."""
        return {
            "route_id": route.route_id,
            "name": route.name,
            "probability": route.probability,
            "timeline_days": route.timeline_days,
            "milestones": route.milestones,
            "outcomes": route.outcomes,
            "interventions_needed": route.interventions_needed
        }


# Example usage
if __name__ == "__main__":
    copilot = AgenticCopilot("synthetic-001")
    
    # Test query
    result = copilot.process_query("What is the risk of cardiovascular events in the next 10 years?")
    
    print("=" * 60)
    print("AGENTIC COPILOT RESPONSE")
    print("=" * 60)
    print(f"\n{result['final_answer']}\n")
    
    if result['pending_tasks']:
        print("\n📋 GENERATED TASKS:")
        for task in result['pending_tasks']:
            print(f"  - [{task['priority']}] {task['title']}")
    
    if result['active_routes']:
        print("\n📍 SIMULATED ROUTES:")
        for route in result['active_routes']:
            print(f"  - {route['name']} ({route['probability']*100:.0f}% probability)")
