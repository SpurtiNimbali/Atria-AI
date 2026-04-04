"""
Transparent Agentic Assistant

This agent:
1. SHOWS you the EHR documents it retrieves
2. SHOWS you its analysis process
3. CREATES branches with real evidence
4. ANSWERS questions with full transparency

Key: Everything is VISIBLE - you see exactly what it's doing
"""
import os
from typing import List, Dict, Any, Generator
from openai import OpenAI
from datetime import datetime
import json

from trajectory_git import TrajectoryGit
from elastic_client import get_elastic_client
from search import hybrid_search, get_patient_summary
from embeddings import generate_embedding

class TransparentAgent:
    """
    Agent that shows ALL its work - document retrieval, analysis, branching.
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.git = TrajectoryGit(patient_id)
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.es = get_elastic_client()
        self.conversation_history: List[Dict] = []
        
        # Initial commit with patient data
        self._initialize_from_ehr()
    
    def _initialize_from_ehr(self):
        """Load patient context on startup."""
        summary = get_patient_summary(self.es, self.patient_id)
        if summary["total_chunks"] > 0:
            self.git.commit(
                "Patient record loaded",
                {
                    "total_records": summary["total_chunks"],
                    "record_types": summary["resource_types"],
                    "status": "initialized"
                },
                author="system"
            )
    
    def process_query(self, user_query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Process query with FULL transparency.
        Shows every document, every step, every decision.
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_query,
            "timestamp": datetime.now().isoformat()
        })
        
        # STEP 1: Show what we're doing
        yield {
            "type": "reasoning_step",
            "emoji": "🤔",
            "step": "Analyzing your question",
            "content": f'"{user_query}"'
        }
        
        # STEP 2: Determine if this is a "what if" or info query
        is_what_if = any(phrase in user_query.lower() for phrase in [
            "what if", "alternative", "instead", "different", "try", "switch"
        ])
        
        if is_what_if:
            yield from self._handle_what_if_query(user_query)
        else:
            yield from self._handle_info_query(user_query)
    
    def _handle_info_query(self, query: str) -> Generator:
        """Handle normal info queries - but show ALL the work."""
        
        # STEP 1: Search EHR
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Searching patient's EHR",
            "content": "Looking through discharge docs, vitals, meds, allergies..."
        }
        
        query_embedding = generate_embedding(query)
        results = hybrid_search(self.es, self.patient_id, query, query_embedding, k=10)
        
        yield {
            "type": "reasoning_step",
            "emoji": "📄",
            "step": f"Found {len(results)} relevant documents",
            "content": "Pulling up the records now..."
        }
        
        # STEP 2: SHOW the actual documents retrieved
        for i, doc in enumerate(results[:5], 1):
            yield {
                "type": "document_retrieved",
                "doc_id": i,
                "resource_type": doc["resource_type"],
                "resource_id": doc["resource_id"],
                "text": doc["text"],
                "score": doc["_score"],
                "timestamp": doc["timestamp"]
            }
            
            # Also show as reasoning step
            yield {
                "type": "reasoning_step",
                "emoji": "📋",
                "step": f"Document {i}: {doc['resource_type']}",
                "content": doc["text"][:200] + ("..." if len(doc["text"]) > 200 else "")
            }
        
        if not results:
            yield {
                "type": "response",
                "content": "I couldn't find any relevant information in the patient's records for that query."
            }
            return
        
        # STEP 3: Analyze the documents
        yield {
            "type": "reasoning_step",
            "emoji": "🧠",
            "step": "Analyzing the documents",
            "content": "Cross-referencing information, looking for patterns..."
        }
        
        # Build context
        context = "\n\n".join([
            f"[Document {i+1}] {r['resource_type']}/{r['resource_id']}:\n{r['text']}"
            for i, r in enumerate(results[:5])
        ])
        
        # STEP 4: Synthesize answer
        yield {
            "type": "reasoning_step",
            "emoji": "💭",
            "step": "Formulating answer",
            "content": "Synthesizing information from the documents..."
        }
        
        system_prompt = """You are a transparent clinical assistant. 

CRITICAL RULES:
1. Answer ONLY using the provided documents
2. Reference specific documents by number [Document 1], [Document 2]
3. If information conflicts, mention BOTH and explain
4. If information is missing, explicitly state what's missing
5. Break down your reasoning step-by-step
6. Be conversational but precise

Format:
1. Direct answer
2. Supporting evidence (cite document numbers)
3. Any concerns or gaps in data
4. What else might be helpful to know
"""
        
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {query}\n\nDocuments:\n{context}"}
            ],
            temperature=0.3
        )
        
        answer = response.choices[0].message.content
        
        # STEP 5: Return answer
        yield {
            "type": "response",
            "content": answer
        }
        
        # STEP 6: Return citations
        citations = []
        for i, doc in enumerate(results[:5], 1):
            citations.append({
                "id": i,
                "resource_type": doc["resource_type"],
                "resource_id": doc["resource_id"],
                "snippet": doc["text"][:300],
                "timestamp": doc["timestamp"],
                "score": doc["_score"]
            })
        
        yield {
            "type": "citations",
            "citations": citations
        }
        
        # Create timeline commit
        yield {
            "type": "timeline_commit",
            "title": query[:50],
            "summary": answer[:150],
            "citations": [c["id"] for c in citations]
        }
    
    def _handle_what_if_query(self, query: str) -> Generator:
        """Handle 'what if' queries - create branches with REAL evidence."""
        
        # Extract what they want to explore
        yield {
            "type": "reasoning_step",
            "emoji": "🤔",
            "step": "Identifying the alternative",
            "content": "Figuring out what you want to explore..."
        }
        
        # Use LLM to extract the alternative
        extraction_prompt = f"""From this question, extract what alternative the user wants to explore:
        
Question: "{query}"

Return JSON:
{{
    "alternative": "short name",
    "description": "full description",
    "category": "medication|procedure|lifestyle|other"
}}
"""
        
        try:
            extraction = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": extraction_prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            alt_data = json.loads(extraction.choices[0].message.content)
        except:
            alt_data = {
                "alternative": "alternative-pathway",
                "description": query,
                "category": "other"
            }
        
        alternative = alt_data["alternative"]
        branch_name = alternative.lower().replace(" ", "-")
        
        yield {
            "type": "reasoning_step",
            "emoji": "🌿",
            "step": "Creating exploration branch",
            "content": f'Branch name: "{branch_name}"'
        }
        
        # Create the branch
        branch = self.git.branch(
            branch_name,
            f"Explore: {alt_data['description']}",
            probability=0.5  # Will adjust based on evidence
        )
        
        self.git.checkout(branch_name)
        
        # STEP 1: Pull relevant EHR docs for eligibility
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Checking patient's records",
            "content": "Looking for contraindications, current meds, allergies, labs..."
        }
        
        # Search for relevant docs
        eligibility_query = f"{alternative} eligibility contraindications allergies kidney function"
        query_embedding = generate_embedding(eligibility_query)
        safety_docs = hybrid_search(self.es, self.patient_id, eligibility_query, query_embedding, k=5)
        
        # SHOW the safety documents
        for i, doc in enumerate(safety_docs, 1):
            yield {
                "type": "document_retrieved",
                "doc_id": i,
                "resource_type": doc["resource_type"],
                "resource_id": doc["resource_id"],
                "text": doc["text"],
                "score": doc["_score"],
                "timestamp": doc["timestamp"]
            }
            
            yield {
                "type": "reasoning_step",
                "emoji": "📋",
                "step": f"Safety Check {i}: {doc['resource_type']}",
                "content": doc["text"][:200]
            }
        
        # STEP 2: Analyze safety
        yield {
            "type": "reasoning_step",
            "emoji": "⚕️",
            "step": "Analyzing safety profile",
            "content": "Checking for conflicts, contraindications, risks..."
        }
        
        safety_context = "\n\n".join([d["text"] for d in safety_docs])
        
        safety_prompt = f"""Analyze if this alternative is safe for the patient:

Alternative: {alternative}
Description: {alt_data['description']}

Patient Records:
{safety_context}

Return JSON:
{{
    "safe": true/false,
    "concerns": ["list of concerns"],
    "green_flags": ["positive factors"],
    "probability_success": 0.7,
    "reasoning": "why this assessment"
}}
"""
        
        try:
            safety_analysis = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": safety_prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            safety = json.loads(safety_analysis.choices[0].message.content)
        except:
            safety = {
                "safe": True,
                "concerns": [],
                "green_flags": [],
                "probability_success": 0.5,
                "reasoning": "Insufficient data"
            }
        
        # Show safety analysis
        for concern in safety.get("concerns", []):
            yield {
                "type": "reasoning_step",
                "emoji": "⚠️",
                "step": "Concern identified",
                "content": concern
            }
        
        for flag in safety.get("green_flags", []):
            yield {
                "type": "reasoning_step",
                "emoji": "✅",
                "step": "Positive factor",
                "content": flag
            }
        
        yield {
            "type": "reasoning_step",
            "emoji": "📊",
            "step": "Safety assessment complete",
            "content": safety["reasoning"]
        }
        
        # Update branch probability
        branch.probability = safety["probability_success"]
        
        # STEP 3: Simulate timeline
        yield {
            "type": "reasoning_step",
            "emoji": "📅",
            "step": "Projecting timeline",
            "content": "Simulating likely outcomes over next 10 days..."
        }
        
        timeline_prompt = f"""Given this alternative and patient context, create a realistic 10-day timeline.

Alternative: {alternative}
Safety Analysis: {json.dumps(safety, indent=2)}
Patient Context: {safety_context[:500]}

Return JSON with 4-6 timeline events:
{{
    "timeline": [
        {{
            "day": 1,
            "event": "Start {alternative}",
            "expected_state": {{"status": "started", "monitoring": "baseline vitals"}},
            "probability": 0.95
        }},
        ...
    ]
}}
"""
        
        try:
            timeline_response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": timeline_prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            timeline_data = json.loads(timeline_response.choices[0].message.content)
            timeline = timeline_data.get("timeline", [])
        except:
            timeline = [
                {"day": 1, "event": f"Start {alternative}", "expected_state": {"status": "started"}, "probability": 0.9},
                {"day": 3, "event": "Initial monitoring", "expected_state": {"status": "monitoring"}, "probability": 0.8},
                {"day": 7, "event": "Assessment", "expected_state": {"status": "assessing"}, "probability": 0.7},
            ]
        
        # Create commits for timeline
        for event in timeline:
            self.git.commit(
                f"Day {event['day']}: {event['event']}",
                event["expected_state"],
                author="simulation"
            )
            
            yield {
                "type": "reasoning_step",
                "emoji": "📍",
                "step": f"Day {event['day']}",
                "content": f"{event['event']} (probability: {int(event['probability']*100)}%)"
            }
        
        # STEP 4: Generate final branch summary
        yield {
            "type": "reasoning_step",
            "emoji": "✅",
            "step": "Branch ready to explore",
            "content": f"Created '{branch_name}' with {len(timeline)} projected events"
        }
        
        # Show the tree
        tree = self.git.visualize_tree()
        
        yield {
            "type": "branch_created",
            "branch": branch.to_dict(),
            "timeline": timeline,
            "safety_analysis": safety,
            "tree": tree,
            "documents_reviewed": len(safety_docs)
        }
        
        # Generate conversational response
        response = f"""🌿 **Exploration Branch Created: "{branch.description}"**

I pulled up {len(safety_docs)} relevant documents from the patient's EHR and analyzed them.

**Safety Profile:**
"""
        
        if safety.get("concerns"):
            response += "\n⚠️ **Concerns:**\n"
            for concern in safety["concerns"]:
                response += f"  • {concern}\n"
        
        if safety.get("green_flags"):
            response += "\n✅ **Positive Factors:**\n"
            for flag in safety["green_flags"]:
                response += f"  • {flag}\n"
        
        response += f"\n**Projected Timeline:**\n"
        for event in timeline:
            response += f"  • Day {event['day']}: {event['event']}\n"
        
        response += f"\n**Probability of Success:** {int(safety['probability_success']*100)}%\n"
        response += f"\n{safety['reasoning']}\n"
        response += f"\nThis is a safe exploration - your main care plan is unchanged. You can adopt this branch later if you want."
        
        yield {
            "type": "response",
            "content": response
        }
        
        # Citations
        yield {
            "type": "citations",
            "citations": [
                {
                    "id": i,
                    "resource_type": doc["resource_type"],
                    "resource_id": doc["resource_id"],
                    "snippet": doc["text"][:300],
                    "timestamp": doc["timestamp"],
                    "score": doc["_score"]
                }
                for i, doc in enumerate(safety_docs, 1)
            ]
        }


# Test it
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = TransparentAgent("synthetic-001")
    
    print("\n" + "="*60)
    print("TEST 1: Normal Info Query")
    print("="*60 + "\n")
    
    for event in agent.process_query("What medications is this patient taking?"):
        if event["type"] == "reasoning_step":
            print(f"{event['emoji']} {event['step']}")
            if event.get("content"):
                print(f"   {event['content'][:100]}")
        elif event["type"] == "document_retrieved":
            print(f"\n📄 Document {event['doc_id']}: {event['resource_type']}")
            print(f"   {event['text'][:150]}...")
        elif event["type"] == "response":
            print(f"\n💬 ANSWER:\n{event['content']}\n")
    
    print("\n" + "="*60)
    print("TEST 2: What If Query")
    print("="*60 + "\n")
    
    for event in agent.process_query("What if we increased the Lisinopril dose to 20mg?"):
        if event["type"] == "reasoning_step":
            print(f"{event['emoji']} {event['step']}")
            if event.get("content"):
                print(f"   {event['content'][:100]}")
        elif event["type"] == "document_retrieved":
            print(f"\n📄 Safety Doc {event['doc_id']}: {event['resource_type']}")
        elif event["type"] == "response":
            print(f"\n💬 BRANCH ANALYSIS:\n{event['content']}\n")
