import httpx
import logging
import json
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL, OPENROUTER_TIMEOUT

logger = logging.getLogger(__name__)

async def explain_recommendation(product_name: str, analysis_dict: dict) -> str:
    """Analyze the market data and provide a strategy explanation via OpenRouter."""
    
    # Validation
    price = analysis_dict.get('recommended_price') or analysis_dict.get('recommended')
    if not price:
        return "Calculation in progress. Awaiting definitive price anchor."

    prompt = f"""
    Product: {product_name}
    Market Context:
    - Min: ₹{analysis_dict.get('market_min', 0)}
    - Max: ₹{analysis_dict.get('market_max', 0)}
    - Average: ₹{analysis_dict.get('market_avg', 0)}
    - Recommendation: ₹{price}
    - Strategy: {analysis_dict.get('strategy', 'COMPETITIVE')}

    Objective: Write a professional 2-sentence market rationale for this price. 
    Explain why this specific value is optimal. No tags, markdown, or emojis.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://pricescope.ai",
        "X-Title": "PriceScope"
    }

    # Verified OpenRouter IDs
    models_to_try = [
        OPENROUTER_MODEL, 
        "google/gemini-flash-1.5",
        "meta-llama/llama-3.1-8b-instruct"
    ]

    last_error = ""
    for model_id in models_to_try:
        if not model_id: continue
        
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        
        try:
            async with httpx.AsyncClient(timeout=float(OPENROUTER_TIMEOUT)) as client:
                logger.info(f"[Explainer] Routing request to {model_id}")
                resp = await client.post(OPENROUTER_BASE_URL, json=payload, headers=headers)
                
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    return content.replace('*', '').replace('#', '')
                else:
                    last_error = f"OPENROUTER_{resp.status_code}_{model_id}"
                    logger.warning(f"[Explainer] Model {model_id} rejected request: {resp.status_code}")
                    continue 
        except Exception as e:
            last_error = str(e)
            continue

    return f"Neural rationale temporarily held by secondary node. (Code: {last_error})"
