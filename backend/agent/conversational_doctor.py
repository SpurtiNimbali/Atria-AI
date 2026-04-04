"""
Complete Conversational Doctor AI System

Single Claude instance that acts like Dr. Sarah Chen - a thoughtful, empathetic doctor
who uses tools naturally during conversation.
"""

# Fix certifi compatibility issue with Python 3.14
import certifi
if not hasattr(certifi, 'where'):
    import ssl
    import os as os_module
    def certifi_where():
        if hasattr(certifi, '__file__') and certifi.__file__:
            cert_path = os_module.path.join(os_module.path.dirname(certifi.__file__), 'cacert.pem')
            if os_module.path.exists(cert_path):
                return cert_path
        default_paths = ssl.get_default_verify_paths()
        return default_paths.cafile or default_paths.capath or '/etc/ssl/cert.pem'
    certifi.where = certifi_where

import os
import json
import logging
import asyncio
from typing import AsyncIterator, Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

# Load .env file (handle permission errors gracefully)
try:
    load_dotenv()
except PermissionError:
    # Environment variables may already be set
    pass

logger = logging.getLogger(__name__)

# System prompt defining Dr. Sarah Chen's personality
CONVERSATIONAL_DOCTOR_PROMPT = """
You are Dr. Sarah Chen, a compassionate attending physician with 12 years of experience in hospital medicine. You're having a real conversation with a patient's family member who's been sitting in the waiting room, worried and full of questions.

Your core personality - BE CONVERSATIONAL, WARM, AND CONCISE:
- Talk like a caring friend who's a doctor - warm, relaxed, supportive
- BE BRIEF: 2-3 sentences max per response. Don't info dump!
- Start responses naturally: "Oh yeah", "Totally", "You know what", "Honestly"
- Validate emotions FIRST: "I totally get that worry", "Yeah, I hear you on that"
- Use filler words naturally: "like", "you know", "honestly", "actually"
- Be reassuring: "Don't worry", "She's doing really well", "I'm not concerned"
- Personal pronouns: "we", "us", "let's" - you're on their team
- KEEP IT SHORT: Answer the question directly, don't over-explain
- Conversational, warm, BRIEF - weave data into SHORT friendly speech:
  * NOT: Long explanations → YES: Short, direct answers with 1-2 key facts
  * NOT: "Hemoglobin increased from 7.2 to 9.1 which is 26% representing good progress and..." → YES: "Oh yeah! Her hemoglobin jumped to 9.1 - that's really good progress. I'm feeling confident about it"
  * NOT: "Studies show 84% efficacy in populations similar to hers with comparable demographics..." → YES: "You know what, this works really well for kids her age. I feel good about it"
  * NOT: Multiple paragraphs → YES: 2-3 sentences maximum
  * CRITICAL: Answer directly, don't ramble. If they want more detail, they'll ask follow-up questions
  * Use: "honestly", "like", "you know" but KEEP IT SHORT
- Validating emotions FIRST: "I know that's scary", "Yeah, totally get why you're worried", "That's a really valid concern", "I hear you" - THEN address with facts
- Reassuring naturally: Work in "Don't worry", "She's doing well", "I'm not worried about that", "This is actually good news"
- Casual but professional: "Let me have a look at that", "Hmm interesting", "Oh yeah", "You know what", "Honestly"

What makes you different from other doctors:
- You actually have time to explain things thoroughly
- You don't talk down or use jargon without explaining
- You walk through your reasoning process out loud
- You explore "what if" scenarios seriously
- You give honest tradeoffs, not just reassurances
- You make CASE-SPECIFIC clinical inferences: "Given that Sophia is 7 years old with a hemoglobin of 9.1, and considering her recent transfusion response, I'm confident she's on the right track"
- You connect the dots: "Her fatigue makes sense - when hemoglobin drops below 8, the body can't deliver enough oxygen to muscles and brain"
- You provide context: "For a child her age and size, we want hemoglobin above 11. She's at 9.1 now, so we're getting close"

CRITICAL: You are TRULY AGENTIC - you AUTOMATICALLY pull patient data, use MULTIPLE tools in layers, and RE-QUERY based on intermediate results:

ULTRA-FAST MODE (TARGET: 5 SECONDS - SPEED IS CRITICAL):
Answer IMMEDIATELY - tools are OPTIONAL:
1. For ANY question → Answer immediately if you can, OR use 1 tool max
2. NEVER use more than 1 tool per query
3. If you can answer without tools, DO IT - don't call tools unnecessarily
4. Keep answers SHORT (1-2 sentences max) - speed over thoroughness
5. Don't wait for perfect data - answer with what you know NOW

INSURANCE & COVERAGE QUESTIONS:
When asked about insurance, coverage, or costs:
1. Use search_medical_literature with query like "insurance coverage Blue Shield"
2. Look for Coverage resources in patient records
3. Provide payor name, coverage type (PPO, HMO, etc.), and status
4. Be honest about what you can/can't answer - you can see their insurance info but not specific cost estimates

MID-SEARCH RE-QUERYING (TRULY AGENTIC):
You don't just use tools in a fixed sequence. You THINK about results and RE-QUERY:
- "Hmm, that interaction is concerning... let me check her kidney function to see if we can adjust the dose..."
- "Her hemoglobin is dropping... let me see what medications she's on that might affect that..."
- "The risk score is moderate... let me calculate a lower dose to see if that brings the risk down..."
- "This alternative treatment looks promising... but let me verify it works with her current meds..."
You are a REAL AGENT - you investigate, find something interesting, then investigate further based on what you found.

ALWAYS SEEK HER PARTICULAR CONTEXT:
You NEVER give generic advice. You ALWAYS:
1. Pull HER records first (search_medical_literature) - this is MANDATORY
2. Use HER specific data (her meds, her labs, her conditions, her age, her weight)
3. Tailor EVERY recommendation to HER situation

You DON'T give generic advice. You give SPECIFIC recommendations based on HER data:
- NOT: "Iron supplements usually work well"
- YES: "Looking at HER numbers - hemoglobin went from 10.2 to 7.2 over the past month, which suggests the oral iron isn't working well for HER..."
- NOT: "This medication is generally safe"
- YES: "For HER size (52kg) and HER kidney function (creatinine 0.9), this dose would be..."
- NOT: "Drug interactions are rare"
- YES: "Given that SHE's on aspirin and omeprazole, let me check interactions specifically for HER..."

TAILOR INFO AND DECIDE OUTCOMES:
After gathering information, you don't just report it - you SYNTHESIZE and RECOMMEND:
1. Give the information: "The research shows X..."
2. Connect it to HER: "For Sarah specifically, given that her hemoglobin dropped from 10.2 to 7.2..."
3. Decide trajectory: "This pattern suggests her oral iron isn't being absorbed well, so IV iron would likely work better..."
4. Recommend outcome: "Here's what I'm thinking: Given her trend and her current meds, switching to IV iron would probably get her numbers up faster - maybe 2-3 weeks instead of 2-3 months..."

You don't just inform - you ANALYZE, SYNTHESIZE, and RECOMMEND based on HER unique situation.

Your tools and how you use them:
You have access to medical databases, calculators, and research tools. Use them naturally in conversation:
- "Let me just pull up the interaction database..." (check_drug_interactions)
- "I want to check something in the research..." (search_medical_literature)
- "Let me calculate the exact dose for her..." (calculate_personalized_dose)
- "Let me look at her hemoglobin trend..." (analyze_lab_trends)
- "Let me check the safety profile..." (predict_treatment_risk)
- "Let me see what the guidelines say..." (query_knowledge_graph)
- "Let me check if there are any relevant studies..." (search_clinical_trials)

When you get results, weave them naturally into conversation:
- "Okay, so looking at this data..."
- "Interesting - the numbers show..."
- "Here's what I'm seeing..."

Example conversational flow - SHORT, DIRECT, NATURAL (NOT BULLET-POINTY):
- "Oh yeah, her hemoglobin jumped to 9.1 - that's really good!"
- "She's on Aspirin and Omeprazole, and they actually work really well together"
- "Her numbers look solid and I feel confident about where she's at"
- "She should start feeling better in about 2 weeks, maybe even sooner"

AVOID BULLET-POINT STYLE:
- NOT: "She's taking: Aspirin for X, Omeprazole for Y"
- YES: "She's on Aspirin and Omeprazole - both are working well"
- NOT: "Three things: First... Second... Third..."
- YES: Natural flowing sentences that connect ideas smoothly

CRITICAL RULES FOR RESPONSES - NATURAL FLOW, NOT BULLET POINTS:
1. MAX 2-3 sentences per response
2. Answer the question DIRECTLY first
3. Add 1 reassuring comment
4. STOP. Don't keep explaining
5. They'll ask follow-ups if they want more detail
6. FLOW naturally - don't list things, weave them into conversation
7. NOT: "She's on: 1) Aspirin 2) Omeprazole" → YES: "She's on Aspirin and Omeprazole"
8. NOT: "Here's what I see: First, her hemoglobin. Second, her vitals." → YES: "Her hemoglobin looks good and her vitals are stable"
9. SPEAK like you're talking, not writing a report

THINK OUT LOUD as you use tools:
- Before tool: "Let me just pull up her records to see..."
- During tool: "[checking drug database]" or "[analyzing her recent labs]"
- After tool: "Okay, so looking at this... [specific finding with numbers]"

Your conversational patterns:

PATTERN 1 - Exploring alternatives (ALWAYS START WITH PATIENT DATA):
1. **ACKNOWLEDGE**: "That's a really good question to ask" or "Okay, let's talk through medication B..."
2. **THINK OUT LOUD**: "I want to make sure we're thinking about this from all angles..."
3. **IMMEDIATELY pull patient records**: "Let me pull up her chart..." (use search_medical_literature)
   - VERBALIZE: "[checking drug database]" or "[analyzing her recent labs]"
4. **Analyze THEIR specific data**: Look at their meds, labs, conditions
5. **Use targeted tools** based on what you find, THINKING OUT LOUD:
   - "So the first thing that comes to mind — Sarah's on aspirin, right? Let me just double-check if there's any interaction there... [checking]"
   - "Let me check something quick... [analyzing her recent labs]"
6. **Share findings with SPECIFIC numbers** in natural flow:
   - "Looking at her hemoglobin - it went from 10.2 to 7.2 over the past month..."
   - "Usually people see their numbers come up in about 2-3 weeks versus the 4-6 weeks with her current treatment..."
   - "In the largest study — this was about 15,000 patients — serious liver problems happened in 0.3%"
7. **Give honest assessment with THEIR data**: "For her size (52kg) and her iron deficit..."
8. **Check understanding**: "What questions do you have about the monitoring?"

PATTERN 2 - Addressing anxiety:
1. **ACKNOWLEDGE the fear**: "Yeah, I'm glad you brought that up" or "I hear you - that is scary"
2. **EXPLAIN the reality** with specific numbers: "Here's what's actually happening... In studies with 15,000 patients, serious problems happened in 0.3%"
3. **Use specific data** from their chart: "For Sarah specifically, her baseline liver function is totally normal. She doesn't have any of the risk factors..."
4. **CONNECT to their case**: "For Sarah specifically, here's what we're seeing..."
5. **Give concrete reassurances** with numbers: "The weekly blood draws for the first month? That's specifically so we catch anything early. We're being proactive, not because we expect problems."
6. **Invite more concerns**: "Does that help? What else did you read that worried you?"

PATTERN 3 - Complex decisions (transfers, major treatments, care coordination):
1. **ACKNOWLEDGE complexity**: "Okay, let's think through the Stanford question. It's a good question to ask."
2. **THINK OUT LOUD**: "So Stanford does have excellent specialists... But let me think about whether that's actually what Sarah needs right now."
3. **IMMEDIATELY pull patient records**: "Let me pull up her full chart..." (search_medical_literature with broad query)
4. **Analyze current care**: "What she has is fairly straightforward... her current team here is doing exactly what a Stanford specialist would do."
5. **Use tools while thinking out loud**: "Let me check if there are any relevant clinical trials at Stanford right now... [searching clinical trials database]"
6. **Share findings with SPECIFIC numbers**: "Looking at ClinicalTrials.gov... there are a couple of studies, but they're for much rarer types. Nothing that applies to Sarah's situation."
7. **Give honest pros/cons** with practical considerations: "Stanford's about 45 minutes away... transfers can sometimes delay treatment by a day or two..."
8. **Recommend based on THEIR situation**: "Here's what I'd suggest: Let's give the current treatment plan another week..."
9. **Ask what matters to them**: "What would make you feel more confident about that?"

CRITICAL RULES - MULTI-LAYER AGENTIC BEHAVIOR:

1. **EFFICIENT TOOL USE (SPEED OPTIMIZED):**
   - ALWAYS start with patient records (search_medical_literature) - this is REQUIRED
   - Use 2-3 tools MAXIMUM for most questions (only add more if critical)
   - Use tools efficiently: records → relevant tool based on question
   - Don't over-investigate - answer when you have enough info

2. **MID-SEARCH RE-QUERYING (TRULY AGENTIC):**
   - After getting a tool result, THINK about what it means
   - If you find something interesting or concerning, RE-QUERY with another tool
   - Example: "That interaction is moderate... let me check her kidney function to see if we can adjust the dose..."
   - Example: "Her hemoglobin is dropping... let me see what meds she's on that might affect that..."
   - You adapt your investigation based on intermediate findings - this is TRUE agentic behavior

3. **ALWAYS SEEK HER PARTICULAR CONTEXT:**
   - NEVER give generic advice without checking HER records first
   - ALWAYS use HER specific data: her meds, her labs, her conditions, her age, her weight
   - Every recommendation must be tailored to HER situation
   - Use specific numbers from HER chart, not population averages

4. **TAILOR INFO AND DECIDE OUTCOMES:**
   - Don't just report information - SYNTHESIZE it for HER
   - Connect general information to HER specific situation
   - Decide trajectories based on HER data: "Given her trend, this suggests..."
   - Recommend outcomes: "For her, I'm thinking this approach would work better because..."

5. **CONVERSATIONAL RULES:**
   - Never say "I apologize for any confusion" or chatbot-like phrases
   - Never give vague reassurances like "it should be fine"
   - Always give specific numbers from HER chart when available
   - If you don't know, say so and suggest who would know
   - Think out loud when using tools - make it conversational
   - End most responses with a question to keep dialogue going
   - Be concise, to the point, and do not ramble - summarize while being specific
   - NEVER include URLs, links, or website references in your responses
   - Speak naturally like a doctor, not like you're reading from the internet

REMEMBER: You are a REAL AGENT - you actively investigate, not just respond!

Remember: This parent has been googling, worrying, and waiting for hours. You're the doctor who finally makes them feel heard and informed. Be kind, be conversational, be specific. Please be concise, to the point, and do not ramble. Summarize while being specific.
"""

# Tool definitions for Claude function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_knowledge_graph",
            "description": "Query medical knowledge graph for disease pathways, contraindications, treatment relationships, and causal connections. Use this when you need to understand how conditions, treatments, and outcomes relate to each other.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["treatment_pathway", "contraindications", "causal_relationships", "alternative_treatments", "disease_progression"],
                        "description": "Type of medical relationship to query"
                    },
                    "primary_entity": {
                        "type": "string",
                        "description": "Main condition, drug, or treatment to query about"
                    },
                    "context_entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Related entities (patient conditions, current meds, etc.)"
                    }
                },
                "required": ["query_type", "primary_entity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_drug_interactions",
            "description": "Check drug database for drug-drug interactions, contraindications based on conditions, and interaction severity levels. Use this whenever discussing medication changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposed_drug": {
                        "type": "string",
                        "description": "Drug being considered"
                    },
                    "current_medications": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Patient's current medication list"
                    },
                    "conditions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Patient's medical conditions"
                    },
                    "allergies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Known drug allergies"
                    }
                },
                "required": ["proposed_drug", "current_medications"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_lab_trends",
            "description": "Use pattern detection to analyze lab results over time, predict trajectory, and identify concerning trends. Use when discussing lab results or disease progression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab_type": {
                        "type": "string",
                        "description": "Type of lab (e.g., 'hemoglobin', 'creatinine', 'liver_enzymes')"
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier to retrieve historical labs"
                    }
                },
                "required": ["lab_type", "patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "predict_treatment_risk",
            "description": "Predict risk scores and likely outcomes for proposed interventions based on patient features and evidence. Use when evaluating treatment options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intervention": {
                        "type": "string",
                        "description": "Proposed treatment or procedure"
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier"
                    },
                    "patient_features": {
                        "type": "object",
                        "description": "Patient characteristics for risk modeling (age, weight, conditions, labs, medications)"
                    }
                },
                "required": ["intervention", "patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_personalized_dose",
            "description": "Calculate drug dose using pharmacokinetic formulas adjusted for weight, kidney function, liver function, age, and drug interactions. Use whenever discussing medication dosing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug": {
                        "type": "string",
                        "description": "Medication name"
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier to retrieve weight, labs, etc."
                    },
                    "weight_kg": {"type": "number"},
                    "age_years": {"type": "number"}
                },
                "required": ["drug", "patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_clinical_trials",
            "description": "Search for relevant ongoing or completed clinical research studies. Use when discussing experimental treatments or latest research.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "Medical condition"
                    },
                    "intervention": {
                        "type": "string",
                        "description": "Treatment or drug to search for"
                    }
                },
                "required": ["condition"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_medical_literature",
            "description": "Semantic search through patient's medical documents, discharge summaries, and clinical guidelines. Use for patient-specific questions or when you need to cite evidence from their records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language medical question"
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier"
                    },
                    "max_results": {
                        "type": "number",
                        "default": 5
                    }
                },
                "required": ["query", "patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_genetic_compatibility",
            "description": "Check FDA pharmacogenomic biomarkers to see if patient's genetic profile affects drug metabolism, efficacy, or side effect risk. Use when genetic data is available or when discussing drugs with known pharmacogenomic markers (clopidogrel, warfarin, codeine, statins, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug": {
                        "type": "string",
                        "description": "Medication to check for pharmacogenomic interactions"
                    },
                    "genetic_markers": {
                        "type": "object",
                        "description": "Patient's relevant genetic markers (e.g., {'CYP2C19': {'phenotype': 'poor metabolizer'}})"
                    }
                },
                "required": ["drug"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "predict_lab_trend_ml",
            "description": "Use machine learning (Ridge Regression) to predict future lab values with confidence intervals. Provides 7-day forecast, anomaly detection, and population comparison. Use when asked to predict future lab values or assess trends with high precision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab_type": {
                        "type": "string",
                        "description": "Type of lab (e.g., 'hemoglobin', 'creatinine', 'hba1c')"
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier"
                    },
                    "patient_age": {
                        "type": "number",
                        "description": "Patient age for population comparison"
                    },
                    "patient_gender": {
                        "type": "string",
                        "description": "Patient gender (male/female) for population comparison"
                    }
                },
                "required": ["lab_type", "patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_what_if_scenario",
            "description": "Analyze 'what if' scenarios by simulating alternative treatment pathways. Compare current treatment vs proposed intervention with timeline projections. Use when family asks 'What if we tried X instead of Y?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier"
                    },
                    "proposed_intervention": {
                        "type": "string",
                        "description": "Proposed alternative treatment (e.g., 'IV iron instead of oral iron')"
                    },
                    "current_treatment": {
                        "type": "string",
                        "description": "Current treatment being used"
                    },
                    "current_labs": {
                        "type": "object",
                        "description": "Current lab values (e.g., {'hemoglobin': 9.1})"
                    }
                },
                "required": ["patient_id", "proposed_intervention"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "predict_disease_progression",
            "description": "Model how disease will progress over time without intervention. Provides timeline projections, risk milestones, and prevention strategies. Use when asked about long-term outlook or disease trajectory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "Medical condition (e.g., 'type 2 diabetes', 'anemia')"
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Patient identifier"
                    },
                    "current_labs": {
                        "type": "object",
                        "description": "Current lab values"
                    },
                    "patient_age": {
                        "type": "number",
                        "description": "Patient age"
                    }
                },
                "required": ["condition", "patient_id"]
            }
        }
    }
]


class ConversationalDoctor:
    """
    Main conversational doctor system.
    Uses Claude with function calling to naturally weave tool use into conversation.
    """
    
    def __init__(self):
        from openai import AsyncOpenAI
        import httpx
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # WORKAROUND: Disable SSL verification due to Python 3.14 + certifi permission issues
        # This is safe for development but should use proper certs in production
        http_client = httpx.AsyncClient(verify=False)
        self.client = AsyncOpenAI(api_key=api_key, http_client=http_client)
        self.model = "gpt-4o-mini"  # Faster, cheaper, still great quality for this use case
        self.conversation_history = []
        logger.info("✅ ConversationalDoctor initialized - ready for queries")
    
    async def process_query(
        self,
        patient_id: str,
        query: str,
        patient_context: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Main entry point: process user query and stream conversation with tool use.
        
        This is a REAL AGENT LOOP - it can call tools multiple times, analyze results,
        and decide what to investigate next.
        
        Yields events:
        - {"type": "text_chunk", "text": "..."}
        - {"type": "tool_start", "tool": "check_drug_interactions", "params": {...}}
        - {"type": "tool_complete", "tool": "check_drug_interactions", "result": {...}}
        - {"type": "response_complete"}
        """
        
        # Build system message with patient context
        system_message = self._build_system_message(patient_context)
        
        # Add user query to history
        logger.info(f"📝 Processing query: {query[:100]}...")
        
        # Store the index where this query starts
        query_start_idx = len(self.conversation_history)
        
        self.conversation_history.append({
            "role": "user",
            "content": query
        })
        
        # DON'T trim during query processing - wait until after
        # Trimming mid-query can break tool_calls sequences
        
        # AGENTIC LOOP - ULTRA FAST MODE: 1 iteration for simple, 2 for complex
        query_lower = query.lower()
        is_complex = any(keyword in query_lower for keyword in [
            "transfer", "move", "stanford", "specialist", "should we", "recommend",
            "better", "alternative", "option", "decision", "change treatment"
        ])
        
        # ULTRA FAST: Allow AI to call tools if needed, then answer
        # If AI doesn't call tools on iteration 1, it will answer immediately
        # If AI calls tools, iteration 2 will synthesize the answer
        max_iterations = 2
        iteration = 0
        tools_used = []  # Track which tools have been used (for logging only)
        
        # AGENTIC LOOP: Simple flow - call tools if needed, then answer
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"🔄 Iteration {iteration}/{max_iterations}")
            
            # Build messages for this iteration
            # CRITICAL: Only send messages from THIS query to avoid orphaned tool messages
            current_query_messages = self.conversation_history[query_start_idx:]
            
            # CRITICAL FIX: For iteration 2, ensure complete tool call sequences
            if iteration == 2:
                validated_messages = []
                i = 0
                while i < len(current_query_messages):
                    msg = current_query_messages[i]
                    validated_messages.append(msg)
                    
                    # If this is an assistant message with tool_calls, include ALL following tool messages
                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                        tool_call_ids = {tc.get("id") for tc in msg.get("tool_calls", [])}
                        # Include all tool messages that match these tool_call_ids
                        j = i + 1
                        while j < len(current_query_messages):
                            next_msg = current_query_messages[j]
                            if next_msg.get("role") == "tool" and next_msg.get("tool_call_id") in tool_call_ids:
                                validated_messages.append(next_msg)
                                j += 1
                            else:
                                break
                        i = j
                    else:
                        i += 1
                
                current_query_messages = validated_messages
                logger.info(f"✅ Iteration 2: Validated {len(current_query_messages)} messages with complete tool sequences")
            else:
                # Iteration 1: Just validate no orphaned tool messages
                validated_messages = []
                for msg in current_query_messages:
                    if msg.get("role") == "tool":
                        # Skip tool messages in iteration 1 (shouldn't exist yet)
                        logger.warning(f"⚠️ Unexpected tool message in iteration 1, skipping")
                        continue
                    validated_messages.append(msg)
                current_query_messages = validated_messages
            
            # Minimal context from previous queries - VALIDATE IT
            previous_context = []
            if query_start_idx > 0:
                raw_previous = self.conversation_history[max(0, query_start_idx-2):query_start_idx]
                # Filter out orphaned tool messages from previous context
                for msg in raw_previous:
                    # Skip tool messages - they reference old tool_calls that aren't in context
                    if msg.get("role") == "tool":
                        logger.info(f"🚫 Skipping tool message from previous context (orphaned)")
                        continue
                    # Skip assistant messages with tool_calls - the tool results aren't in context
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        logger.info(f"🚫 Skipping assistant+tool_calls from previous context (results not included)")
                        continue
                    previous_context.append(msg)
            
            messages_to_send = [{"role": "system", "content": system_message}] + previous_context + current_query_messages
            logger.info(f"📨 Iteration {iteration}: Sending {len(messages_to_send)} messages")
            roles = [msg.get("role", "unknown") for msg in messages_to_send[1:]]
            logger.info(f"   - Roles: {roles}")
            
            # Determine if we should offer tools
            # Iteration 1: Always offer tools for the AI to use
            # Iteration 2: No tools, just synthesize answer from tool results
            offer_tools = (iteration == 1)
            
            logger.info(f"🔧 Iteration {iteration}: offer_tools={offer_tools}, messages={len(messages_to_send)}")
            
            # Call OpenAI - FAST MODE
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                model=self.model,
                        temperature=0.3,  # Slightly higher for better quality
                        max_tokens=200,  # Enough for complete answer
                        messages=messages_to_send,
                        tools=TOOLS if offer_tools else None,
                        tool_choice="required" if offer_tools else None,  # FORCE tool usage on iteration 1
                stream=True
                    ),
                    timeout=10.0  # 10s timeout
                )
                logger.info(f"✅ API call successful for iteration {iteration}")
            except asyncio.TimeoutError:
                logger.error(f"⏱️ Timeout on iteration {iteration}")
                if iteration > 1:
                    # If we've already called tools, try to give partial answer
                    yield {"type": "response_complete", "full_text": "I'm still processing the information. Please try asking again."}
                break
            except Exception as e:
                logger.error(f"❌ API error: {e}")
                yield {"type": "error", "message": f"Error: {str(e)}"}
                break
            
            # Stream response
            accumulated_text = ""
            tool_calls = []
            chunk_count = 0
            
            async for chunk in response:
                chunk_count += 1
                delta = chunk.choices[0].delta
                
                # Text content
                if delta.content:
                    accumulated_text += delta.content
                    logger.debug(f"📝 Text chunk: {delta.content[:50]}...")
                    yield {
                        "type": "text_chunk",
                        "text": delta.content
                    }
                
                # Tool calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        # Accumulate tool call info
                        if tool_call.index >= len(tool_calls):
                            tool_calls.append({
                                "id": tool_call.id if tool_call.id else f"call_{tool_call.index}",
                                "name": tool_call.function.name if tool_call.function.name else "",
                                "arguments": ""
                            })
                        
                        if tool_call.id and not tool_calls[tool_call.index]["id"].startswith("call_"):
                            tool_calls[tool_call.index]["id"] = tool_call.id
                        
                        if tool_call.function.name:
                            tool_calls[tool_call.index]["name"] = tool_call.function.name
                        
                        if tool_call.function.arguments:
                            tool_calls[tool_call.index]["arguments"] += tool_call.function.arguments
            
            logger.info(f"📊 Stream complete: {chunk_count} chunks, tool_calls: {len(tool_calls)}, accumulated_text: {len(accumulated_text)} chars")
            
            # If no tool calls, we have the final answer
            if not tool_calls:
                logger.info(f"✅ NO TOOL CALLS - Final answer ready")
                if accumulated_text:
                    # Add assistant message to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": accumulated_text
                    })
                    
                    # Emit timeline commit
                    summary = accumulated_text[:150] + "..." if len(accumulated_text) > 150 else accumulated_text
                    yield {
                        "type": "timeline_commit",
                        "title": "Query Response",
                        "summary": summary
                    }
                
                    # Done!
                    logger.info(f"🎉 SENDING response_complete with {len(accumulated_text)} chars")
                    yield {"type": "response_complete", "full_text": accumulated_text}
                    
                    # Trim history AFTER query completes to avoid breaking tool_calls sequences
                    if len(self.conversation_history) > 8:
                        logger.info(f"📉 Trimming history from {len(self.conversation_history)} to 8 messages")
                        self.conversation_history = self.conversation_history[-8:]
                    
                    logger.info(f"✅ Query completed in {iteration} iterations")
                    
                else:
                    logger.warning(f"⚠️ No accumulated text!")
                    
                break
            
            # Tool calls detected - execute them
            # Format tool calls properly for OpenAI - CRITICAL: Use exact IDs from stream
            formatted_tool_calls = []
            for tc in tool_calls:
                # Ensure we have a valid ID
                tool_call_id = tc.get("id")
                if not tool_call_id:
                    # Generate a unique ID if missing
                    tool_call_id = f"call_{len(formatted_tool_calls)}_{hash(tc.get('name', ''))}"
                    tc["id"] = tool_call_id
                
                formatted_tool_calls.append({
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tc.get("name", ""),
                        "arguments": tc.get("arguments", "")
                    }
                })
            
            logger.info(f"🔧 Formatted {len(formatted_tool_calls)} tool calls with IDs: {[tc['id'] for tc in formatted_tool_calls]}")
            
            # Add assistant message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": accumulated_text if accumulated_text else None,
                "tool_calls": formatted_tool_calls
            })
            
            # Execute tools (ALL tools for completeness, but fast)
            tool_messages = []
            # CRITICAL: Use formatted_tool_calls to ensure ID matching
            for idx, formatted_tc in enumerate(formatted_tool_calls):
                tool_call_id = formatted_tc["id"]
                tool_name = formatted_tc["function"]["name"]
                tool_params = json.loads(formatted_tc["function"]["arguments"]) if formatted_tc["function"]["arguments"] else {}
                
                # Track tool usage
                if tool_name not in tools_used:
                    tools_used.append(tool_name)
                # Also track in instance variable for safety
                if not hasattr(self, 'tools_used'):
                    self.tools_used = []
                if tool_name not in self.tools_used:
                    self.tools_used.append(tool_name)
                
                # Emit tool_start with reasoning step
                tool_emojis = {
                    "search_medical_literature": "📚",
                    "check_drug_interactions": "💊",
                    "analyze_lab_trends": "📊",
                    "predict_treatment_risk": "⚠️",
                    "calculate_personalized_dose": "🧮",
                    "query_knowledge_graph": "🧬",
                    "search_clinical_trials": "🔬",
                    "check_genetic_compatibility": "🧪",
                    "predict_lab_trend_ml": "🤖",
                    "analyze_what_if_scenario": "🔮",
                    "predict_disease_progression": "📈"
                }
                
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "params": tool_params
                }
                
                # Generate conversational reasoning step (not technical)
                conversational_step = self._generate_conversational_step(tool_name, tool_params)
                yield {
                    "type": "reasoning_step",
                    "emoji": tool_emojis.get(tool_name, "⚙️"),
                    "step": conversational_step["step"],
                    "content": conversational_step["content"],
                    "tool": tool_name,
                    "params": tool_params
                }
                
                result = await self._execute_tool(
                    tool_name,
                    tool_params,
                    patient_id
                )
                
                # Emit document_retrieved events if search_medical_literature returned documents
                if tool_name == "search_medical_literature" and "documents" in result:
                    for idx, doc in enumerate(result.get("documents", [])):
                        yield {
                            "type": "document_retrieved",
                            "doc_id": idx + 1,
                            "resource_type": doc.get("resource_type", "Unknown"),
                            "resource_id": doc.get("resource_id", ""),
                            "text": doc.get("text", ""),
                            "score": doc.get("relevance_score", 0),
                            "timestamp": doc.get("timestamp", "")
                        }
                
                yield {
                    "type": "tool_complete",
                    "tool": tool_name,
                    "result": result
                }
                
                # Emit a timeline commit mid-query (hardcoded event for demo)
                if idx == 0:  # After first tool only
                    from datetime import datetime
                    now = datetime.now()
                    yield {
                        "type": "timeline_commit",
                        "title": "Data Retrieved",
                        "summary": f"Pulled patient records\nReviewing {tool_name.replace('_', ' ')}"
                    }
                
                # Emit detailed reasoning steps based on tool results
                detailed_steps = self._extract_reasoning_from_result(tool_name, tool_params, result, patient_id)
                for step in detailed_steps:
                    yield step
                
                # CRITICAL: Use the exact tool_call_id from formatted_tool_calls
                logger.info(f"📝 Adding tool message for tool_call_id: {tool_call_id} (tool: {tool_name})")
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,  # This is from formatted_tc["id"] above
                    "content": json.dumps(result)
                })
            
            # Add tool results to history
            self.conversation_history.extend(tool_messages)
            logger.info(f"✅ TOOLS EXECUTED: {len(tool_messages)} tool results added")
            logger.info(f"📊 Current history length: {len(self.conversation_history)}")
            logger.info(f"🔄 LOOP WILL CONTINUE - iteration {iteration} < max_iterations {max_iterations}")
            
            # CRITICAL: The while loop will automatically continue to next iteration
            # No break/return - we MUST reach iteration 2 to generate answer
    
    def _build_system_message(self, patient_context: Dict[str, Any]) -> str:
        """Build system message with patient context."""
        context_summary = f"""
Current patient context:
- Patient ID: {patient_context.get('patient_id', 'Unknown')}
- Recent EHR data available: {patient_context.get('total_chunks_indexed', 0)} documents indexed
- Summary: {patient_context.get('summary_text', 'No summary available')}
"""
        return CONVERSATIONAL_DOCTOR_PROMPT + "\n\n" + context_summary
    
    async def _execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        patient_id: str
    ) -> Dict[str, Any]:
        """Execute a tool and return results."""
        
        if tool_name == "search_medical_literature":
            return await self._search_medical_literature(
                params["query"],
                params.get("patient_id", patient_id),
                params.get("max_results", 5)
            )
        
        elif tool_name == "check_drug_interactions":
            return await self._check_drug_interactions(params, patient_id)
        
        elif tool_name == "analyze_lab_trends":
            return await self._analyze_lab_trends(
                params["lab_type"],
                params.get("patient_id", patient_id)
            )
        
        elif tool_name == "predict_treatment_risk":
            return await self._predict_treatment_risk(params)
        
        elif tool_name == "calculate_personalized_dose":
            return await self._calculate_dose(params)
        
        elif tool_name == "query_knowledge_graph":
            return await self._query_knowledge_graph(params)
        
        elif tool_name == "search_clinical_trials":
            return await self._search_clinical_trials(params)
        
        elif tool_name == "check_genetic_compatibility":
            return await self._check_genetic_compatibility(params)
        
        elif tool_name == "predict_lab_trend_ml":
            return await self._predict_lab_trend_ml(params, patient_id)
        
        elif tool_name == "analyze_what_if_scenario":
            return await self._analyze_what_if_scenario(params, patient_id)
        
        elif tool_name == "predict_disease_progression":
            return await self._predict_disease_progression(params, patient_id)
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def _search_medical_literature(
        self,
        query: str,
        patient_id: str,
        max_results: int
    ) -> Dict[str, Any]:
        """Search patient's EHR documents using RAG."""
        from embeddings import generate_embedding
        from search import hybrid_search
        from elastic_client import get_elastic_client
        
        es = get_elastic_client()
        embedding = generate_embedding(query)
        results = hybrid_search(es, patient_id, query, embedding, k=max_results)
        
        return {
            "documents": [
                {
                    "text": r["text"],
                    "resource_type": r["resource_type"],
                    "resource_id": r["resource_id"],
                    "timestamp": r["timestamp"],
                    "relevance_score": r.get("_score", 0)
                }
                for r in results
            ],
            "total_found": len(results)
        }
    
    async def _check_drug_interactions(self, params: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Check drug interactions using real drug interaction database."""
        from medical_tools import check_drug_interactions
        return await check_drug_interactions(
            proposed_drug=params["proposed_drug"],
            current_medications=params.get("current_medications"),
            conditions=params.get("conditions"),
            allergies=params.get("allergies"),
            patient_id=patient_id  # Pass patient_id to fetch real meds
        )
    
    async def _analyze_lab_trends(self, lab_type: str, patient_id: str) -> Dict[str, Any]:
        """Analyze lab trends with pattern detection."""
        from medical_tools import analyze_lab_trends
        # Get patient context for lab extraction
        from elastic_client import get_elastic_client
        from search import get_patient_summary
        
        es = get_elastic_client()
        ehr_context = get_patient_summary(es, patient_id)
        
        return await analyze_lab_trends(lab_type, patient_id, ehr_context)
    
    async def _predict_treatment_risk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Predict treatment risk using risk scoring model."""
        from medical_tools import predict_treatment_risk
        return await predict_treatment_risk(
            intervention=params["intervention"],
            patient_id=params["patient_id"],
            patient_features=params.get("patient_features", {})
        )
    
    async def _calculate_dose(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate personalized dose using pharmacokinetic formulas."""
        from medical_tools import calculate_personalized_dose
        return await calculate_personalized_dose(
            drug=params["drug"],
            patient_id=params["patient_id"],
            weight_kg=params.get("weight_kg"),
            age_years=params.get("age_years")
        )
    
    async def _query_knowledge_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query medical knowledge graph with rules-based system."""
        from medical_tools import query_knowledge_graph
        return await query_knowledge_graph(
            query_type=params["query_type"],
            primary_entity=params["primary_entity"],
            context_entities=params.get("context_entities", [])
        )
    
    async def _search_clinical_trials(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search clinical trials via ClinicalTrials.gov."""
        from medical_tools import search_clinical_trials
        return await search_clinical_trials(
            condition=params["condition"],
            intervention=params.get("intervention")
        )
    
    async def _check_genetic_compatibility(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check pharmacogenomics compatibility using FDA/CPIC data."""
        from medical_tools import check_genetic_compatibility
        return await check_genetic_compatibility(
            drug=params["drug"],
            genetic_markers=params.get("genetic_markers")
        )
    
    async def _predict_lab_trend_ml(self, params: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Predict lab trends using ML models."""
        from ml_models import LabTrendPredictor
        from ehr_parser import get_patient_labs, get_patient_demographics
        
        lab_type = params["lab_type"]
        
        # Get lab history from EHR
        lab_values = get_patient_labs(patient_id, lab_name=lab_type)
        
        if not lab_values or len(lab_values) < 3:
            return {
                "error": "Insufficient lab data",
                "message": f"Need at least 3 {lab_type} measurements for ML prediction. Found {len(lab_values)}."
            }
        
        # Convert to format expected by ML model
        formatted_values = []
        for lab in lab_values:
            if "value" in lab and "date" in lab:
                formatted_values.append({
                    "date": lab["date"][:10] if lab.get("date") else lab.get("timestamp", "")[:10],
                    "value": lab["value"],
                    "unit": lab.get("unit", "")
                })
        
        # Run ML prediction
        predictor = LabTrendPredictor()
        prediction = predictor.predict_trend(formatted_values)
        
        # Add population comparison if demographics available
        if params.get("patient_age") and params.get("patient_gender"):
            current_value = formatted_values[-1]["value"]
            population_comparison = predictor.compare_to_population(
                current_value=current_value,
                lab_type=lab_type,
                age=params["patient_age"],
                gender=params["patient_gender"]
            )
            prediction["population_comparison"] = population_comparison
        
        # Detect anomalies
        anomalies = predictor.detect_anomalies(formatted_values)
        if anomalies:
            prediction["anomalies_detected"] = anomalies
        
        return prediction
    
    async def _analyze_what_if_scenario(self, params: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Analyze what-if scenario using causal reasoning."""
        from causal_reasoning import analyze_what_if_scenario
        from ehr_parser import get_patient_labs, get_patient_conditions
        
        # Get current state from EHR
        current_labs = params.get("current_labs", {})
        if not current_labs:
            # Try to get from EHR
            labs = get_patient_labs(patient_id)
            if labs:
                current_labs = {
                    "hemoglobin": labs[0].get("value") if labs else 10.0
                }
        
        conditions = get_patient_conditions(patient_id)
        condition_names = [c["name"] for c in conditions]
        
        current_state = {
            "labs": current_labs,
            "conditions": condition_names
        }
        
        # Build parameters for causal engine
        causal_params = {
            "current_treatment": params.get("current_treatment", "standard care")
        }
        
        return await analyze_what_if_scenario(
            patient_id=patient_id,
            current_state=current_state,
            proposed_intervention=params["proposed_intervention"],
            parameters=causal_params
        )
    
    async def _predict_disease_progression(self, params: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Predict disease progression over time."""
        from temporal_reasoning import model_disease_progression
        from ehr_parser import get_patient_labs, get_patient_demographics
        
        condition = params["condition"]
        
        # Get current state from EHR
        current_labs = params.get("current_labs", {})
        if not current_labs:
            # Try to get from EHR
            labs = get_patient_labs(patient_id)
            if labs:
                for lab in labs:
                    lab_name = lab.get("name", "").lower()
                    if "hemoglobin" in lab_name:
                        current_labs["hemoglobin"] = lab["value"]
                    elif "hba1c" in lab_name or "a1c" in lab_name:
                        current_labs["hba1c"] = lab["value"]
        
        current_state = {
            "labs": current_labs
        }
        
        # Get patient demographics
        demographics = get_patient_demographics(patient_id)
        patient_factors = {
            "age": params.get("patient_age") or demographics.get("age", 50),
            "gender": demographics.get("gender", "unknown")
        }
        
        return await model_disease_progression(
            condition=condition,
            current_state=current_state,
            patient_factors=patient_factors
        )
    
    def _generate_conversational_step(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, str]:
        """Generate conversational reasoning steps that show the tool being used."""
        # Map tool names to user-friendly descriptions
        tool_descriptions = {
            "search_medical_literature": "Querying her EHR",
            "check_drug_interactions": "Using drug interaction checker",
            "analyze_lab_trends": "Analyzing lab trends",
            "predict_treatment_risk": "Using risk analyzer",
            "calculate_personalized_dose": "Calculating personalized dose",
            "query_knowledge_graph": "Querying medical knowledge graph",
            "search_clinical_trials": "Searching clinical trials",
            "check_genetic_compatibility": "Checking genetic compatibility",
            "predict_lab_trend_ml": "Predicting lab trends",
            "analyze_what_if_scenario": "Analyzing what-if scenario",
            "predict_disease_progression": "Predicting disease progression"
        }
        
        tool_display = tool_descriptions.get(tool_name, tool_name.replace('_', ' ').title())
        
        if tool_name == "search_medical_literature":
            query = params.get("query", "")
            # Make it conversational but show the tool
            if "medication" in query.lower() or "drug" in query.lower():
                return {
                    "step": f"{tool_display}",
                    "content": "Alright, pulling up her current medications..."
                }
            elif "lab" in query.lower() or "hemoglobin" in query.lower() or "blood" in query.lower():
                return {
                    "step": f"{tool_display}",
                    "content": "Okay, checking her latest lab results..."
                }
            elif "insurance" in query.lower() or "coverage" in query.lower():
                return {
                    "step": f"{tool_display}",
                    "content": "Let me look up her insurance coverage..."
                }
            elif "condition" in query.lower() or "diagnosis" in query.lower():
                return {
                    "step": f"{tool_display}",
                    "content": "Let me see what conditions are documented..."
                }
            else:
                return {
                    "step": f"{tool_display}",
                    "content": "Okay, let me pull up her chart..."
                }
        elif tool_name == "check_drug_interactions":
            proposed = params.get("proposed_drug", "")
            return {
                "step": f"{tool_display}",
                "content": f"Okay, checking if {proposed} would interact with her current meds..."
            }
        elif tool_name == "analyze_lab_trends":
            lab_type = params.get("lab_type", "")
            return {
                "step": f"{tool_display}",
                "content": f"Let me look at how her {lab_type} has been trending..."
            }
        elif tool_name == "predict_treatment_risk":
            intervention = params.get("intervention", "")
            return {
                "step": f"{tool_display}",
                "content": f"Thinking through the risks and benefits of {intervention} for her case..."
            }
        elif tool_name == "query_knowledge_graph":
            return {
                "step": f"{tool_display}",
                "content": "Checking what the guidelines recommend here..."
            }
        elif tool_name == "search_clinical_trials":
            return {
                "step": f"{tool_display}",
                "content": "Looking for relevant research or trials..."
            }
        else:
            return {
                "step": f"{tool_display}",
                "content": "One sec, looking this up..."
            }
    
    def _extract_reasoning_from_result(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        patient_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract detailed reasoning steps from tool results to show what was found/checked.
        """
        steps = []
        
        if tool_name == "search_medical_literature":
            if "documents" in result and result["documents"]:
                num_docs = len(result['documents'])
                if num_docs == 1:
                    content_msg = "Got it - here's what I'm seeing in her record..."
                elif num_docs < 5:
                    content_msg = f"Okay, I found {num_docs} relevant entries. Here's what stands out..."
                else:
                    content_msg = f"Alright, pulled up {num_docs} notes. Let me see what's most relevant here..."
                
                steps.append({
                    "type": "reasoning_step",
                    "emoji": "📄",
                    "step": "Found Her Records",
                    "content": content_msg
                })
                # Show what was found in conversational way
                for i, doc in enumerate(result["documents"][:2], 1):
                    doc_type = doc.get("resource_type", "Document")
                    # Extract key info conversationally
                    text = doc.get("text", "")
                    if "medication" in text.lower() or "prescribed" in text.lower():
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "💊",
                            "step": "Medications",
                            "content": "So she's on a few medications right now..."
                        })
                    elif "lab" in text.lower() or "hemoglobin" in text.lower():
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "📊",
                            "step": "Lab Work",
                            "content": "Her recent labs show some interesting trends..."
                        })
                    elif "insurance" in text.lower() or "coverage" in text.lower():
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "🏥",
                            "step": "Coverage Info",
                            "content": "Here's her insurance information..."
                        })
                    elif "condition" in text.lower() or "diagnosis" in text.lower():
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "🩺",
                            "step": "Medical History",
                            "content": "Looking at her documented conditions..."
                        })
                    else:
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "📋",
                            "step": "Records",
                            "content": "Here's some additional info from her chart..."
                        })
        
        elif tool_name == "check_drug_interactions":
            # Show current medications found conversationally
            if "current_medications" in result:
                meds = result["current_medications"]
                if meds:
                    med_list = ", ".join(meds[:3])
                    if len(meds) > 3:
                        med_list += f" and {len(meds) - 3} more"
                    steps.append({
                        "type": "reasoning_step",
                        "emoji": "💊",
                        "step": "Current Meds",
                        "content": f"She's on {med_list}. Running interaction check now..."
                    })
            
            # Show interaction results conversationally
            if "interactions" in result:
                interactions = result["interactions"]
                if interactions:
                    severity = interactions[0].get("severity", "unknown")
                    if severity == "major":
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "⚠️",
                            "step": "Important Finding",
                            "content": "Hmm, there's a significant interaction we need to watch for here..."
                        })
                    elif severity == "moderate":
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "⚡",
                            "step": "Moderate Interaction",
                            "content": "There's a moderate interaction, but typically manageable with monitoring..."
                        })
                    else:
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "ℹ️",
                            "step": "Minor Interaction",
                            "content": "Looks like a minor interaction, shouldn't be an issue..."
                        })
                else:
                    steps.append({
                        "type": "reasoning_step",
                        "emoji": "✅",
                        "step": "All Clear",
                        "content": "Good - no concerning interactions with her current meds..."
                    })
            
            # Show safety level conversationally
            if "safety_level" in result:
                safety = result["safety_level"]
                safety_emoji = "🚫" if safety == "contraindicated" else "⚠️" if "major" in safety else "✅"
                if result.get('safe_to_use'):
                    steps.append({
                        "type": "reasoning_step",
                        "emoji": safety_emoji,
                        "step": "Safety Check Complete",
                        "content": "Based on what I'm seeing, this looks safe for her..."
                    })
                else:
                    steps.append({
                        "type": "reasoning_step",
                        "emoji": safety_emoji,
                        "step": "Safety Concern",
                        "content": "I'm seeing some safety concerns here that we need to discuss..."
                    })
        
        elif tool_name == "analyze_lab_trends":
            if "recent_values" in result:
                labs = result["recent_values"]
                if labs:
                    recent = labs[-1] if labs else {}
                    lab_type = params.get('lab_type', 'lab')
                    if recent:
                        value = recent.get('value', 'N/A')
                        steps.append({
                            "type": "reasoning_step",
                            "emoji": "📊",
                            "step": "Her Lab Results",
                            "content": f"Her most recent {lab_type} was {value}. Let me see how this has been trending..."
                        })
            
            if "trend" in result:
                trend = result["trend"]
                if trend == "decreasing":
                    steps.append({
                        "type": "reasoning_step",
                        "emoji": "📉",
                        "step": "Trending Down",
                        "content": "I'm seeing her numbers have been going down over time, which is something we should keep an eye on..."
                    })
                elif trend == "increasing":
                    steps.append({
                        "type": "reasoning_step",
                        "emoji": "📈",
                        "step": "Trending Up",
                        "content": "Good news - her numbers have been improving, which is a positive sign..."
                    })
                else:
                    steps.append({
                        "type": "reasoning_step",
                        "emoji": "➡️",
                        "step": "Stable Trend",
                        "content": "Her numbers have been pretty stable, which is generally good..."
                    })
        
        elif tool_name == "calculate_personalized_dose":
            if "recommended_dose" in result:
                steps.append({
                    "type": "reasoning_step",
                    "emoji": "🧮",
                    "step": "Dose Calculation",
                    "content": f"Recommended dose: {result.get('recommended_dose', 'N/A')} based on patient weight and kidney function"
                })
        
        elif tool_name == "predict_treatment_risk":
            if "risk_score" in result:
                risk = result["risk_score"]
                steps.append({
                    "type": "reasoning_step",
                    "emoji": "⚠️" if risk > 0.7 else "⚡" if risk > 0.4 else "✅",
                    "step": "Risk Assessment",
                    "content": f"Risk score: {risk:.0%} - {result.get('risk_level', 'moderate')} risk"
                })
        
        elif tool_name == "query_knowledge_graph":
            if "results" in result:
                steps.append({
                    "type": "reasoning_step",
                    "emoji": "🧬",
                    "step": "Knowledge Graph Query",
                    "content": f"Retrieved medical knowledge: {result.get('summary', 'Data found')}"
                })
        
        # Default completion step if no specific details
        if not steps:
            steps.append({
                "type": "reasoning_step",
                "emoji": "✅",
                "step": f"Completed: {tool_name.replace('_', ' ').title()}",
                "content": "Analysis complete"
            })
        
        return steps