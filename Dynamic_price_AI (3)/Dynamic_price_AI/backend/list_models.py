import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    models = client.models.list().data
    print("Available Models:")
    for m in models:
        print("-", m.id)
except Exception as e:
    print("Model list error:", e)
