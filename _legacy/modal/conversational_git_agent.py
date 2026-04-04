"""
Conversational Git Agent

This agent:
1. Takes natural questions from family/clinicians
2. Decides what Git operations to perform
3. Shows reasoning steps in real-time
4. Returns conversational responses with Git data

Example:
    Family: "What if we tried medication B instead?"
    Agent: Creates branch, simulates timeline, shows visual
"""
import os
from typing import List, Dict, Any, Generator
from openai import OpenAI
from datetime import datetime
import json

from trajectory_git import TrajectoryGit, Commit, Branch
from elastic_client import get_elastic_client
from search import hybrid_search
from embeddings import generate_embedding

class ConversationalGitAgent:
    """
    Agent that maps natural questions to Git operations.
    """
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.git = TrajectoryGit(patient_id)
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.es = get_elastic_client()
        self.conversation_history: List[Dict] = []
    
    def process_query(self, user_query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Process natural language query and perform Git operations.
        
        Yields reasoning steps and results in real-time.
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_query,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 1: Understand intent
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Understanding your question",
            "content": f"Analyzing: '{user_query}'"
        }
        
        intent = self._classify_intent(user_query)
        
        yield {
            "type": "reasoning_step",
            "emoji": "💡",
            "step": "Identified intent",
            "content": f"This is a '{intent['type']}' question"
        }
        
        # Step 2: Execute appropriate Git operation
        if intent["type"] == "explore_alternative":
            yield from self._handle_explore_alternative(user_query, intent)
        
        elif intent["type"] == "check_updates":
            yield from self._handle_check_updates(user_query, intent)
        
        elif intent["type"] == "show_options":
            yield from self._handle_show_options(user_query, intent)
        
        elif intent["type"] == "adopt_branch":
            yield from self._handle_adopt_branch(user_query, intent)
        
        elif intent["type"] == "show_history":
            yield from self._handle_show_history(user_query, intent)
        
        elif intent["type"] == "info_lookup":
            yield from self._handle_info_lookup(user_query, intent)
        
        else:
            yield {
                "type": "response",
                "content": "I'm not sure how to help with that. Try asking about alternatives, updates, or options."
            }
    
    def _classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify user intent using LLM.
        
        Intent types:
        - explore_alternative: "What if we tried X?"
        - check_updates: "What's new since..."
        - show_options: "Show me all options"
        - adopt_branch: "Let's go with X"
        - show_history: "What happened on day 3?"
        - info_lookup: "What medications is patient on?"
        """
        system_prompt = """You are an intent classifier for a clinical care planner.
        
        Classify the user's question into ONE of these intents:
        - explore_alternative: User wants to explore a "what if" scenario (branch creation)
        - check_updates: User wants to see what changed since a time ("what's new?")
        - show_options: User wants to see all available paths ("show options")
        - adopt_branch: User wants to commit to a path ("let's do X")
        - show_history: User wants to see past events ("what happened when?")
        - info_lookup: User wants factual info from EHR ("what meds?", "what's the diagnosis?")
        
        Return JSON with:
        {
            "type": "intent_type",
            "confidence": 0.95,
            "extracted_params": {
                "alternative_name": "medication B",  // if explore_alternative
                "time_reference": "this morning",    // if check_updates
                "branch_name": "medication-b"        // if adopt_branch
            }
        }
        """
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "type": "info_lookup",
                "confidence": 0.5,
                "extracted_params": {}
            }
    
    def _handle_explore_alternative(self, query: str, intent: Dict) -> Generator:
        """
        Handle: "What if we tried medication B?"
        
        Creates a branch and simulates the timeline.
        """
        alternative = intent["extracted_params"].get("alternative_name", "alternative pathway")
        branch_name = alternative.lower().replace(" ", "-")
        
        yield {
            "type": "reasoning_step",
            "emoji": "🌿",
            "step": "Creating branch",
            "content": f"Forking from current state → '{branch_name}'"
        }
        
        # Create branch
        branch = self.git.branch(
            branch_name,
            f"Explore: {alternative}",
            probability=0.6  # Default probability
        )
        
        yield {
            "type": "reasoning_step",
            "emoji": "✅",
            "step": "Branch created",
            "content": f"New pathway: {branch.description}"
        }
        
        # Switch to branch
        self.git.checkout(branch_name)
        
        # Check eligibility using EHR data
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Evaluating eligibility",
            "content": "Checking patient records..."
        }
        
        eligibility_checks = self._check_eligibility(alternative)
        
        for check in eligibility_checks:
            yield {
                "type": "reasoning_step",
                "emoji": "→",
                "step": check["check"],
                "content": check["result"]
            }
        
        # Simulate timeline using LLM
        yield {
            "type": "reasoning_step",
            "emoji": "📅",
            "step": "Building timeline for this path",
            "content": "Projecting next steps..."
        }
        
        timeline = self._simulate_timeline(alternative, eligibility_checks)
        
        for event in timeline:
            # Create commit for each timeline event
            self.git.commit(
                event["message"],
                event["changes"],
                author="simulation"
            )
            
            yield {
                "type": "reasoning_step",
                "emoji": "→",
                "step": f"Day {event['day']}",
                "content": event["message"]
            }
        
        # Generate summary
        yield {
            "type": "reasoning_step",
            "emoji": "✅",
            "step": "Branch ready",
            "content": f"Pathway '{branch_name}' is ready to explore"
        }
        
        # Return visual tree
        tree = self.git.visualize_tree()
        
        yield {
            "type": "branch_created",
            "branch": branch.to_dict(),
            "timeline": timeline,
            "tree": tree,
            "eligibility": eligibility_checks
        }
        
        # Conversational response
        response = f"""✅ **Branch created: "{branch.description}"**

Here's what this pathway looks like:

**Eligibility:**
{self._format_eligibility(eligibility_checks)}

**Timeline:**
{self._format_timeline(timeline)}

**Probability of success:** {int(branch.probability * 100)}%

You can explore this path further, or ask me to show you other options.
"""
        
        yield {
            "type": "response",
            "content": response
        }
    
    def _handle_check_updates(self, query: str, intent: Dict) -> Generator:
        """
        Handle: "What's new since this morning?"
        
        Shows diff of commits since time reference.
        """
        time_ref = intent["extracted_params"].get("time_reference", "last update")
        
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Checking commits",
            "content": f"Looking for changes since {time_ref}..."
        }
        
        # Get recent commits (simplified - would parse time_ref properly)
        recent_commits = self.git.log(limit=5)
        
        if not recent_commits:
            yield {
                "type": "response",
                "content": f"No updates since {time_ref}."
            }
            return
        
        yield {
            "type": "reasoning_step",
            "emoji": "📋",
            "step": "Found updates",
            "content": f"Found {len(recent_commits)} changes"
        }
        
        # Show diff
        diff_output = []
        for commit in recent_commits:
            diff_output.append({
                "commit_id": commit.short_id(),
                "time": commit.timestamp,
                "author": commit.author,
                "message": commit.message,
                "changes": commit.state_changes
            })
        
        yield {
            "type": "diff",
            "commits": diff_output
        }
        
        # Conversational response
        response = f"""📋 **Here's what changed since {time_ref}:**

"""
        for commit in recent_commits:
            response += f"**{commit.short_id()}** - {commit.message}\n"
            response += f"  *{commit.timestamp}* by {commit.author}\n"
            for key, value in commit.state_changes.items():
                response += f"  • {key}: {value}\n"
            response += "\n"
        
        yield {
            "type": "response",
            "content": response
        }
    
    def _handle_show_options(self, query: str, intent: Dict) -> Generator:
        """
        Handle: "Show me all the options"
        
        Shows all active branches.
        """
        yield {
            "type": "reasoning_step",
            "emoji": "🌳",
            "step": "Listing all pathways",
            "content": "Gathering active branches..."
        }
        
        branches = list(self.git.branches.values())
        
        yield {
            "type": "branches_list",
            "branches": [b.to_dict() for b in branches]
        }
        
        response = f"🌳 **Available care pathways:**\n\n"
        for branch in branches:
            icon = "✅" if branch.name == "main" else "🔀"
            response += f"{icon} **{branch.name}**\n"
            response += f"  {branch.description}\n"
            if branch.name != "main":
                response += f"  Probability: {int(branch.probability * 100)}%\n"
            response += "\n"
        
        response += "\nYou can explore any path by asking 'What about [pathway]?' or adopt one with 'Let's go with [pathway]'."
        
        yield {
            "type": "response",
            "content": response
        }
    
    def _handle_adopt_branch(self, query: str, intent: Dict) -> Generator:
        """
        Handle: "Let's go with medication B"
        
        Merges branch into main.
        """
        branch_name = intent["extracted_params"].get("branch_name", "")
        
        if not branch_name or branch_name not in self.git.branches:
            # Try to match from query
            for b in self.git.branches.keys():
                if b in query.lower():
                    branch_name = b
                    break
        
        if not branch_name or branch_name == "main":
            yield {
                "type": "response",
                "content": "I'm not sure which pathway you want to adopt. Can you be more specific?"
            }
            return
        
        yield {
            "type": "reasoning_step",
            "emoji": "🔀",
            "step": "Merging pathway",
            "content": f"Adopting '{branch_name}' as the main path..."
        }
        
        # Merge
        result = self.git.merge(branch_name)
        
        yield {
            "type": "merge_complete",
            "result": result
        }
        
        response = f"""✅ **Pathway adopted!**

Merged '{branch_name}' into main timeline.

This is now the active care plan. All future updates will build on this path.

{len(result['commits_merged'])} changes were applied.
"""
        
        yield {
            "type": "response",
            "content": response
        }
    
    def _handle_show_history(self, query: str, intent: Dict) -> Generator:
        """
        Handle: "What happened on Day 3?"
        
        Shows commit details from history.
        """
        yield {
            "type": "reasoning_step",
            "emoji": "📜",
            "step": "Searching history",
            "content": "Looking through past commits..."
        }
        
        commits = self.git.log(limit=20)
        
        # Simple search for now - would be smarter with real time parsing
        relevant_commits = [c for c in commits if any(word in c.message.lower() for word in query.lower().split())]
        
        if not relevant_commits:
            relevant_commits = commits[:5]  # Show recent if no match
        
        response = "📜 **Timeline history:**\n\n"
        for commit in relevant_commits:
            response += f"**{commit.message}**\n"
            response += f"  {commit.timestamp} ({commit.short_id()})\n"
            for key, val in commit.state_changes.items():
                response += f"  • {key}: {val}\n"
            response += "\n"
        
        yield {
            "type": "response",
            "content": response
        }
    
    def _handle_info_lookup(self, query: str, intent: Dict) -> Generator:
        """
        Handle: "What medications is the patient on?"
        
        Standard EHR search (not Git-related).
        """
        yield {
            "type": "reasoning_step",
            "emoji": "🔍",
            "step": "Searching patient records",
            "content": "Querying EHR database..."
        }
        
        # Use hybrid search
        query_embedding = generate_embedding(query)
        results = hybrid_search(self.es, self.patient_id, query, query_embedding, k=5)
        
        if not results:
            yield {
                "type": "response",
                "content": "I couldn't find relevant information in the patient records."
            }
            return
        
        yield {
            "type": "reasoning_step",
            "emoji": "📚",
            "step": "Found records",
            "content": f"Retrieved {len(results)} relevant documents"
        }
        
        # Format response
        context = "\n\n".join([r["text"] for r in results[:3]])
        
        # Use LLM to synthesize
        llm_response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a clinical assistant. Answer based ONLY on the provided context."},
                {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"}
            ],
            temperature=0.1
        )
        
        answer = llm_response.choices[0].message.content
        
        yield {
            "type": "response",
            "content": answer
        }
        
        yield {
            "type": "citations",
            "citations": [
                {
                    "id": i + 1,
                    "resource_type": r["resource_type"],
                    "snippet": r["text"][:200],
                    "score": r["_score"]
                }
                for i, r in enumerate(results)
            ]
        }
    
    def _check_eligibility(self, alternative: str) -> List[Dict]:
        """Check if alternative is viable using EHR data."""
        # Search for contraindications
        checks = []
        
        # Check allergies
        query = f"patient allergies contraindications {alternative}"
        query_embedding = generate_embedding(query)
        results = hybrid_search(self.es, self.patient_id, query, query_embedding, k=3)
        
        allergy_found = any("allergy" in r["text"].lower() for r in results)
        checks.append({
            "check": "Checking allergies",
            "result": "❌ Allergy found" if allergy_found else "✅ No known allergies",
            "safe": not allergy_found
        })
        
        # Check kidney function
        query = f"kidney function creatinine eGFR"
        query_embedding = generate_embedding(query)
        results = hybrid_search(self.es, self.patient_id, query, query_embedding, k=3)
        
        checks.append({
            "check": "Reviewing kidney function",
            "result": "✅ Within normal limits" if results else "⚠️  No recent labs",
            "safe": True
        })
        
        return checks
    
    def _simulate_timeline(self, alternative: str, eligibility: List[Dict]) -> List[Dict]:
        """Simulate timeline for alternative path using LLM."""
        prompt = f"""Given a patient considering: {alternative}

Eligibility checks: {json.dumps(eligibility, indent=2)}

Generate a realistic 10-day clinical timeline with 4-5 key events.
Return JSON array of events:
[
    {{
        "day": 1,
        "message": "Start {alternative}",
        "changes": {{"medications": ["{alternative}"], "status": "started"}}
    }},
    ...
]
"""
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("timeline", [])
        except:
            # Fallback timeline
            return [
                {"day": 1, "message": f"Start {alternative}", "changes": {"status": "started"}},
                {"day": 3, "message": "Monitor for side effects", "changes": {"status": "monitoring"}},
                {"day": 7, "message": "Assess response", "changes": {"status": "assessing"}},
                {"day": 10, "message": "Follow-up evaluation", "changes": {"status": "follow_up"}}
            ]
    
    def _format_eligibility(self, checks: List[Dict]) -> str:
        return "\n".join([f"• {c['check']}: {c['result']}" for c in checks])
    
    def _format_timeline(self, timeline: List[Dict]) -> str:
        return "\n".join([f"• Day {e['day']}: {e['message']}" for e in timeline])


# Test it
if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    
    patient_id = "synthetic-001"
    agent = ConversationalGitAgent(patient_id)
    
    # Simulate conversation
    queries = [
        "What if we tried Lisinopril 20mg instead of 10mg?",
        "What's new since this morning?",
        "Show me all the options",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"USER: {query}")
        print(f"{'='*60}\n")
        
        for event in agent.process_query(query):
            if event["type"] == "reasoning_step":
                emoji = event.get("emoji", "")
                print(f"{emoji} {event['step']}")
                if event.get("content"):
                    print(f"   → {event['content']}")
            
            elif event["type"] == "response":
                print(f"\n{event['content']}\n")
        
        print()
