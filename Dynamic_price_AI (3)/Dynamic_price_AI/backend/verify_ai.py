import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Load config
load_dotenv(".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("AI-Test")

async def test_gemini():
    logger.info("📡 Testing Gemini 2.0 API Connection...")
    if not GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY missing in .env")
        return False
        
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Test models list as a connectivity check
        models = client.models.list()
        logger.info("✅ Gemini API Key is ACTIVE. Successfully retrieved model list.")
        return True
    except Exception as e:
        logger.error(f"❌ Gemini Connection FAILED: {e}")
        return False

async def test_openrouter():
    logger.info("📡 Testing OpenRouter API Connection...")
    if not OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY missing in .env")
        return False
        
    try:
        import httpx
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                logger.info("✅ OpenRouter API Key is ACTIVE.")
                return True
            else:
                logger.error(f"❌ OpenRouter Error: {resp.status_code} - {resp.text}")
                return False
    except Exception as e:
        logger.error(f"❌ OpenRouter Connection FAILED: {e}")
        return False

async def main():
    print("\n" + "="*50)
    print("      PRICESCOPE AI DIAGNOSTIC - KEY VERIFICATION")
    print("="*50 + "\n")
    
    g_res = await test_gemini()
    o_res = await test_openrouter()
    
    print("\n" + "="*50)
    if g_res and o_res:
        print("  🟢 ALL AI SYSTEMS ONLINE: READY FOR DEPLOYMENT")
    else:
        print("  🔴 SYSTEM DEGRADED: Please check keys above")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
