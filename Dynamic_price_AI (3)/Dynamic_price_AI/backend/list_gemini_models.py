import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")

if not key:
    print("Error: GEMINI_API_KEY is not defined in .env")
else:
    print(f"Key Found (Length: {len(key)})")
    print(f"Format Check: {key[:10]}...{key[-5:]}")
    
    genai.configure(api_key=key)
    try:
        models = genai.list_models()
        print("Success: API Key is valid. Available models:")
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"API Error (403 usually means Key Rejected): {e}")
