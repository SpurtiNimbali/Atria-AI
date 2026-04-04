"""
Extract structured clinical events from conversation.
"""
from typing import List, Dict
from openai import OpenAI
from datetime import datetime
import json

def extract_evidence_events(conversation_text: str, patient_id: str) -> List[Dict]:
    """
    Extract discrete clinical events from natural language conversation.
    
    Events are structured facts that update patient state:
    - Symptoms reported
    - Vitals mentioned
    - Medication changes
    - Follow-up appointments
    
    Returns list of structured events with timestamps and confidence.
    """
    client = OpenAI()
    
    prompt = f"""Extract structured clinical events from this conversation.

Conversation:
{conversation_text}

Extract events in this format:
[
  {{
    "type": "symptom_report|vital_sign|medication_change|appointment|diagnosis",
    "description": "brief description",
    "structured_data": {{"key": "value"}},
    "confidence": 0.0-1.0,
    "urgency": "low|medium|high|critical"
  }}
]

Only extract explicit, clinically relevant events. No speculation."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    result = json.loads(response.choices[0].message.content)
    events = result.get("events", [])
    
    # Add metadata
    for event in events:
        event["patient_id"] = patient_id
        event["extracted_at"] = datetime.now().isoformat()
    
    return events


if __name__ == "__main__":
    conversation = """
    Clinician: How are you feeling today?
    Patient: I've been having chest pain when I walk upstairs. 
    Clinician: When did this start?
    Patient: About 3 days ago. Also my blood pressure was 150/95 this morning.
    """
    
    events = extract_evidence_events(conversation, "synthetic-001")
    for event in events:
        print(f"Event: {event['type']} - {event['description']} (urgency: {event['urgency']})")
