import requests, dotenv, os
dotenv.load_dotenv('.env')
resp = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f"Bearer {os.getenv('GROQ_API_KEY')}"})
print([m['id'] for m in resp.json().get('data', [])])
