import os
import json
import re
from groq import Groq

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_topic(message: str) -> str:
    """Uses Regex and LLM to extract the conversation topic dynamically."""
    msg_lower = message.lower()
    if "ticket" in msg_lower or re.search(r'it-\d{4}', msg_lower):
        return "ticket"
    if "wifi" in msg_lower or "internet" in msg_lower:
        return "wifi"
    if "password" in msg_lower:
        return "password_reset"
        
    client = get_client()
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a classifier. Analyze the user message and return ONLY a single word string. Must be one of: 'general', 'ticket', 'wifi', 'password_reset', 'other'. If the user mentions a ticket, output 'ticket'. If they mention wifi, output 'wifi'. DO NOT return JSON. Return ONLY the raw word."},
                {"role": "user", "content": message}
            ],
            max_tokens=10,
            temperature=0.0
        )
        topic = response.choices[0].message.content.strip().lower()
        if not topic:
            return "general"
        if "ticket" in topic:
            return "ticket"
        if "wifi" in topic:
            return "wifi"
        if "password" in topic:
            return "password_reset"
        return topic if topic in ["general", "other"] else "general"
    except Exception as e:
        print(f"Extraction Error: {e}")
        return "general"

def generate_reply(system_prompt: str, recent_messages: list) -> str:
    """Generates the main assistant reply by appending the strictly token-managed recent messages."""
    client = get_client()
    messages = [{"role": "system", "content": system_prompt}]
    for msg in recent_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )
    reply = response.choices[0].message.content
    return reply.replace('\u2011', '-')
