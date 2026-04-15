import json
import re
import io
import base64
import logging
import httpx
from PIL import Image
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)

# ✅ Elite Tactical Prompt
VISION_PROMPT = """You are an elite architectural surveillance unit. Identify this product with surgical precision. 
If the product brand and model are visible, provide a confidence score of 0.95 or higher. 

Return EXACTLY a JSON object with these keys:
- product_name: (Full model identification, e.g. "Apple AirPods Pro Gen 2")
- brand: (Verifiable manufacturer)
- category: (Market classification)
- search_queries: (3 strings for precision scraping)
- confidence: (0.95 to 0.99 for clear matches)
- attributes: (Color, materials, identifiable serial patterns)

Response must be raw JSON only."""

def _get_default_data(error_msg=None):
    return {
        "product_name": f"IDENT_ERROR: {error_msg[:20]}..." if error_msg else "Unknown Product",
        "brand": "Unknown",
        "category": "General",
        "search_queries": ["latest product"],
        "confidence": 0.0,
        "attributes": {"error": error_msg} if error_msg else {}
    }

async def identify_product(image: Image.Image) -> dict:
    """
    Identify product from image using OpenRouter (Gemini 2.0 Flash).
    Highly reliable, avoids 404 model errors.
    """
    if not OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY missing in .env")
        return _get_default_data("MISSING_KEY")

    try:
        # 1. Prepare Image (Base64)
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # 2. Build OpenRouter Payload (Multimodal)
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "PriceScope AI"
        }

        payload = {
            "model": "google/gemini-2.0-flash-001", # High stability model name on OpenRouter
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ]
        }

        logger.info(f"📡 Sending Vision Request to OpenRouter...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
            
            if resp.status_code != 200:
                logger.error(f"❌ OpenRouter Error: {resp.status_code} - {resp.text}")
                return _get_default_data(f"HTTP_{resp.status_code}")

            res_json = resp.json()
            text = res_json["choices"][0]["message"]["content"].strip()

            # 3. Extract JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                logger.info(f"✅ Successfully identified via OpenRouter: {data.get('product_name')}")
                return data
            
            logger.warning("No JSON found in OpenRouter response")
            return _get_default_data("PARSE_ERROR")

    except Exception as e:
        logger.error(f"❌ OpenRouter Vision failed: {e}")
        return _get_default_data(str(e))