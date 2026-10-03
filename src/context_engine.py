import os
import json
import re
import tiktoken
from src.llm_client import extract_topic, generate_reply

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def count_tokens(messages: list) -> int:
    """Accurately count tokens using tiktoken (cl100k_base for OpenAI)."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
    num_tokens += 2 
    return num_tokens

class ContextManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.filepath = os.path.join(LOG_DIR, f"context_{session_id}.json")
        self.state = self.load_state()

    def load_state(self) -> dict:
        """Hydrates session state conforming strictly to req-2 schema."""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                return json.load(f)
        return {
            "session_id": self.session_id,
            "active_topic": "general",
            "pinned": {
                "ticket_id": None
            },
            "recent": [],
            "total_recent_tokens": 0
        }

    def save_state(self):
        """Persists the full context object updating total_recent_tokens (req-2)."""
        self.state["total_recent_tokens"] = count_tokens(self.state["recent"])
        with open(self.filepath, 'w') as f:
            json.dump(self.state, f, indent=2)

    def process_message(self, user_message: str, token_limit: int):
        # req-3: Extract Ticket ID to pinned.ticket_id
        ticket_matches = re.findall(r'IT-\d{4}', user_message)
        if ticket_matches:
            self.state["pinned"]["ticket_id"] = ticket_matches[0]
        
        # req-5: Infer topic
        new_topic = extract_topic(user_message)
        self.state["active_topic"] = new_topic

        # Append new message
        self.state["recent"].append({"role": "user", "content": user_message})

        # req-4: Evict old messages
        self.prune_recent(token_limit)

        system_prompt = self.build_system_prompt()
        
        try:
            reply_text = generate_reply(system_prompt, self.state["recent"])
        except Exception as e:
            # req-10: Rollback if generation fails
            self.state["recent"].pop()
            raise e
        
        self.state["recent"].append({"role": "assistant", "content": reply_text})
        self.prune_recent(token_limit)
        
        self.save_state()
        return reply_text, self.state["active_topic"]

    def prune_recent(self, token_limit: int):
        while self.state["recent"] and count_tokens(self.state["recent"]) > token_limit:
            self.state["recent"].pop(0)

    def build_system_prompt(self) -> str:
        prompt = "You are an IT helpdesk agent for a university, assisting students and faculty.\n"
        prompt += f"The user is currently discussing: {self.state['active_topic']}\n"
        if self.state["pinned"].get("ticket_id"):
            prompt += f"Known information about this user:\n- Ticket ID: {self.state['pinned']['ticket_id']}\n"
        prompt += "If answering a troubleshooting issue, be clear and step-by-step. If asked about a ticket, refer to the known information."
        return prompt
