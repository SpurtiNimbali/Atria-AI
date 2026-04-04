"""
Test the agentic loop - see if Dr. Chen queries herself multiple times
"""
import asyncio
import json

async def test_agentic_loop():
    # Import the conversational doctor
    import sys
    sys.path.insert(0, '/Users/spurtinimbali/Desktop/TreeHacks/modal')
    
    from conversational_doctor import ConversationalDoctor
    
    doctor = ConversationalDoctor()
    
    # Test query that should trigger multiple tool calls
    query = "What's her hemoglobin trend and should we be worried?"
    patient_id = "synthetic-001"
    conversation_history = []
    
    print("🧪 Testing Agentic Loop")
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)
    print()
    
    tool_count = 0
    iteration_count = 0
    current_iteration_tools = []
    
    async for event in doctor.process_query(patient_id, query, conversation_history):
        event_type = event.get("type")
        
        if event_type == "tool_start":
            tool_count += 1
            tool_name = event.get("tool")
            current_iteration_tools.append(tool_name)
            print(f"🔧 TOOL {tool_count}: {tool_name}")
            print(f"   Params: {json.dumps(event.get('params', {}), indent=2)}")
        
        elif event_type == "tool_complete":
            print(f"   ✅ Completed")
            print()
        
        elif event_type == "text_chunk":
            # This means AI is generating text response (after tools)
            if current_iteration_tools:
                iteration_count += 1
                print(f"\n📊 ITERATION {iteration_count} COMPLETE")
                print(f"   Tools called: {', '.join(current_iteration_tools)}")
                print(f"   AI now analyzing results...")
                print()
                current_iteration_tools = []
        
        elif event_type == "response_complete":
            print("=" * 60)
            print(f"✅ AGENTIC LOOP COMPLETE")
            print(f"   Total iterations: {iteration_count}")
            print(f"   Total tools called: {tool_count}")
            print("=" * 60)
    
    return tool_count > 1  # Success if multiple tools were called

if __name__ == "__main__":
    result = asyncio.run(test_agentic_loop())
    if result:
        print("\n🎉 SUCCESS: Agentic loop is working! AI queried itself multiple times.")
    else:
        print("\n⚠️ Only 1 tool called - might need to check loop logic")
