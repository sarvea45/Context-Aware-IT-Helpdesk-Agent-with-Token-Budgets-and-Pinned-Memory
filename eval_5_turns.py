import requests
import time
import os
import sys

# Force UTF-8 encoding for Windows terminal to prevent charmap errors on LLM outputs
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"
SESSION_ID = f"eval_{int(time.time())}"
# Strict token budget specifically to force early eviction during this eval sequence (req-4 & req-6)
TOKEN_LIMIT = 100 

def test_turn(turn_num, message, expected_topic_keyword=None, expect_pinned_ticket=None):
    print(f"\n[{turn_num}/5] User: {message}")
    
    # Send message (req-1-chat-endpoint)
    resp = requests.post(
        f"{API_URL}/v1/chat",
        json={"session_id": SESSION_ID, "message": message, "token_limit_override": TOKEN_LIMIT}
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"Agent: {data['response']}")
    print(f"Active Topic: {data['active_topic']}")
    
    # Retrieve state via API (req-9-context-retrieval-api)
    ctx_resp = requests.get(f"{API_URL}/v1/context/{SESSION_ID}")
    ctx_resp.raise_for_status()
    ctx = ctx_resp.json()
    print(f"Current Pinned: {ctx['pinned']}")
    print(f"Total Recent Tokens: {ctx['total_recent_tokens']}")
    
    # Validate Context JSON Dump Exists (req-2-context-persistence)
    assert os.path.exists(f"logs/context_{SESSION_ID}.json"), "Context log file was not saved!"
    
    # Assertions for topic tracking and pinning (req-3 and req-5)
    if expected_topic_keyword:
        assert expected_topic_keyword.lower() in data['active_topic'].lower(), f"Expected topic '{expected_topic_keyword}' not found in {data['active_topic']}"
    if expect_pinned_ticket:
        assert ctx['pinned'].get('ticket_id') == expect_pinned_ticket, f"Expected pinned ticket {expect_pinned_ticket}, got {ctx['pinned'].get('ticket_id')}"
    
    return ctx, data['response']

def run_eval():
    try:
        print("Starting 5-Turn Evaluation Script (req-6-five-turn-eval-script)...")
        
        # Turn 1: General
        test_turn(1, "Hi, I need help.", expected_topic_keyword="general")
        
        # Turn 2: Provide Ticket -> Pin extraction (req-3)
        test_turn(2, "My ticket is IT-8812.", expected_topic_keyword="ticket", expect_pinned_ticket="IT-8812")
        
        # Turn 3: Topic Switch -> Long message to force eviction
        long_wifi_msg = "Actually, before we do that, my WiFi in the library just dropped. I am using a Mac. It says 'connected without internet'. " * 4
        test_turn(3, long_wifi_msg, expected_topic_keyword="wifi", expect_pinned_ticket="IT-8812")
        
        # Turn 4: Continuation of new topic
        test_turn(4, "Can you give me the Mac troubleshooting steps? I need detailed instructions.", expect_pinned_ticket="IT-8812")
        
        # Turn 5: Return to original topic / assertion of memory
        final_ctx, final_reply = test_turn(5, "Okay, I fixed the WiFi. Let's go back to my original ticket. What was the status of the ticket I mentioned earlier?", expect_pinned_ticket="IT-8812")
        
        assert "IT-8812" in final_reply, f"Final AI response MUST contain the ticket ID 'IT-8812'! Got: {final_reply}"

        # Evaluate eviction (req-4-token-budget-eviction)
        recent_texts = " ".join([m['content'] for m in final_ctx['recent']])
        
        # Because of our TOKEN_LIMIT=100, the "My ticket is IT-8812." message MUST have been evicted from recent history.
        assert "My ticket is IT-8812." not in recent_texts, "Turn 2 should have been evicted from 'recent' history due to token budget!"
        
        # However, the Context Manager MUST have pinned it, enabling the agent to know it.
        assert final_ctx['pinned'].get("ticket_id") == "IT-8812", "Ticket IT-8812 MUST survive in 'pinned' memory!"
        
        print("\n[SUCCESS] All Eval Contracts Passed! Context Manager successfully evicted history while preserving pinned facts.")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[ERROR] Evaluation Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Evaluation Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_eval()
