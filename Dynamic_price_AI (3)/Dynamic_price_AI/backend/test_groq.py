import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say hello",
            }
        ],
        model="llama3-8b-8192",
    )
    print("Groq Test Result:", chat_completion.choices[0].message.content)
except Exception as e:
    print("Groq Test Error:", e)
