from src.llm_client import get_client
import dotenv
dotenv.load_dotenv('.env')

client = get_client()
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a classifier. Analyze the user message and return ONLY a single word string. Must be one of: 'general', 'ticket', 'wifi', 'password_reset', 'other'. If the user mentions a ticket, output 'ticket'. If they mention wifi, output 'wifi'. DO NOT return JSON. Return ONLY the raw word."},
        {"role": "user", "content": "My ticket is IT-8812."}
    ],
    max_tokens=10,
    temperature=0.0
)
print("RAW LLM OUTPUT:", repr(response.choices[0].message.content))
