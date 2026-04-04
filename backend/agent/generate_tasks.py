"""
Auto-generate actionable tasks from clinical context.
"""
from typing import List, Dict
from openai import OpenAI
from datetime import datetime, timedelta
import json

def generate_taskboard(
    patient_id: str,
    evidence_events: List[Dict],
    ehr_context: str,
    conversation: str
) -> List[Dict]:
    """
    Generate actionable, time-bound tasks based on:
    - Evidence events extracted from conversation
    - EHR context (conditions, meds, vitals)
    - Clinical guidelines
    
    Returns prioritized task list with deadlines and rationale.
    """
    client = OpenAI()
    
    prompt = f"""You are a clinical task planner. Generate actionable tasks for caregivers.

Patient Context:
{ehr_context}

Recent Evidence Events:
{json.dumps(evidence_events, indent=2)}

Conversation:
{conversation}

Generate tasks in this format:
{{
  "tasks": [
    {{
      "title": "Brief task description",
      "priority": "critical|high|medium|low",
      "deadline": "YYYY-MM-DD or 'ASAP' or 'within 24h'",
      "category": "medication|monitoring|appointment|education|emergency",
      "action_steps": ["step 1", "step 2"],
      "rationale": "Why this task is needed (cite evidence)",
      "citations": ["resource_type/resource_id"]
    }}
  ]
}}

Focus on:
- Safety-critical actions first
- Medication adherence
- Follow-up appointments
- Patient education
- Monitoring needs

Be specific and actionable. No vague suggestions."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    
    result = json.loads(response.choices[0].message.content)
    tasks = result.get("tasks", [])
    
    # Add metadata and task IDs
    for i, task in enumerate(tasks):
        task["task_id"] = f"{patient_id}-task-{datetime.now().strftime('%Y%m%d')}-{i+1}"
        task["patient_id"] = patient_id
        task["created_at"] = datetime.now().isoformat()
        task["status"] = "pending"
    
    return tasks


if __name__ == "__main__":
    # Example usage
    events = [
        {
            "type": "symptom_report",
            "description": "Chest pain on exertion",
            "urgency": "high"
        }
    ]
    
    ehr_context = """
    Patient: Emily Johnson, 39F
    Conditions: Hypertension, Type 2 Diabetes
    Medications: Metformin 500mg BID, Lisinopril 10mg QD
    Last BP: 135/85 (2024-01-15)
    Last HbA1c: 7.2% (2024-01-15)
    """
    
    conversation = "Patient reports chest pain when climbing stairs, started 3 days ago."
    
    tasks = generate_taskboard("synthetic-001", events, ehr_context, conversation)
    
    print("GENERATED TASK BOARD:")
    for task in tasks:
        print(f"\n[{task['priority'].upper()}] {task['title']}")
        print(f"  Deadline: {task['deadline']}")
        print(f"  Rationale: {task['rationale']}")
        print(f"  Actions: {', '.join(task['action_steps'])}")
