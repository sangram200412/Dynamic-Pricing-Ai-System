"""
API Routes — SSE streaming endpoint for real-time price analysis.

Flow:
  1. POST /analyze  → accepts image, returns SSE stream
  2. SSE events:
     - vision_result:   product identification complete
     - scraper_start:   scraper X has started
     - scraper_result:  scraper X completed (prices attached)
     - scraper_error:   scraper X failed
     - ml_analysis:     ML analysis complete
     - complete:        all done, final payload

  3. POST /upload      → legacy endpoint (non-streaming, backward compatible)
"""
import io
import json
import time
import asyncio
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image

from config import SCRAPER_MAX_CONCURRENT
from vision.identifier import identify_product
from scrapers.amazon import AmazonScraper
from scrapers.flipkart import FlipkartScraper
from scrapers.ebay import EbayScraper
from scrapers.meesho import MeeshoScraper
from scrapers.reliance import RelianceScraper
from scrapers.myntra import MyntraScraper
from scrapers.snapdeal import SnapdealScraper
from scrapers.base import ScrapedProduct
from utils.normalizer import normalize_products, clean_price, format_inr
from ml.analyzer import analyze_prices
from ml.explainer import explain_recommendation

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Scraper registry ────────────────────────────────
SCRAPERS = [
    AmazonScraper(),
    FlipkartScraper(),
    EbayScraper(),
    MeeshoScraper(),
    RelianceScraper(),
    MyntraScraper(),
    SnapdealScraper(),
]



def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


async def _run_analysis(image_bytes: bytes) -> AsyncGenerator[str, None]:
    """
    Full analysis pipeline as an SSE stream generator.
    Each step yields SSE events as it completes.
    """
    total_start = time.perf_counter()

    # ──────────────────────────────────────────────
    # Step 1: Vision AI — identify product from image
    # ──────────────────────────────────────────────
    yield _sse_event("status", {"step": "vision", "message": "Analyzing product image with AI..."})

    try:
        img = Image.open(io.BytesIO(image_bytes))
        vision_result = await identify_product(img)
    except Exception as exc:
        logger.error(f"Vision failed: {exc}")
        yield _sse_event("error", {"step": "vision", "message": str(exc)})
        yield _sse_event("complete", {"success": False, "error": "Vision AI failed"})
        return

    product_name = vision_result.get("product_name", "Unknown Product")
    search_queries = vision_result.get("search_queries", [product_name])
    primary_query = search_queries[0] if search_queries else product_name

    yield _sse_event("vision_result", {
        "product_name": product_name,
        "brand": vision_result.get("brand", "Unknown"),
        "category": vision_result.get("category", "General"),
        "search_queries": search_queries,
        "confidence": vision_result.get("confidence", 0),
        "attributes": vision_result.get("attributes", {}),
    })

    # ──────────────────────────────────────────────
    # Step 2: Parallel scraping — fire all scrapers
    # ──────────────────────────────────────────────
    yield _sse_event("status", {"step": "scraping", "message": f"Searching for '{primary_query}' across 5 platforms..."})

    all_products = []
    platform_results = {}

    sem = asyncio.Semaphore(SCRAPER_MAX_CONCURRENT)

    async def _run_scraper(scraper):
        async with sem:
            return await scraper.safe_scrape(primary_query)

    tasks = [asyncio.create_task(_run_scraper(s)) for s in SCRAPERS]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        platform = result.platform

        if result.success and result.products:
            # Normalize prices
            normalized = normalize_products(result.products)

            # Get best price for this platform
            best_price = None
            best_product = None
            for p in normalized:
                if p.price_clean > 0:
                    if best_price is None or p.price_clean < best_price:
                        best_price = p.price_clean
                        best_product = p

            platform_data = {
                "platform": platform,
                "success": True,
                "product_count": len(normalized),
                "time_taken": result.time_taken,
                "products": [
                    {
                        "name": p.product_name[:80],
                        "price": p.price_clean,
                        "price_formatted": format_inr(p.price_clean),
                        "url": p.url,
                        "rating": p.rating,
                        "reviews": p.reviews,
                    }
                    for p in normalized[:5]  # top 5 per platform
                ],
            }

            if best_product:
                platform_data["best_price"] = best_price
                platform_data["best_price_formatted"] = format_inr(best_price)
                platform_data["best_url"] = best_product.url

            platform_results[platform] = platform_data
            all_products.extend(normalized)

            yield _sse_event("scraper_result", platform_data)
            logger.info(f"[{platform}] ✓ {len(normalized)} products, best: {format_inr(best_price) if best_price else 'N/A'}")
        else:
            platform_data = {
                "platform": platform,
                "success": False,
                "error": result.error or "No data found",
                "product_count": 0,
                "time_taken": result.time_taken,
                "best_price": 0,
                "best_price_formatted": "N/A",
                "products": [],
            }
            platform_results[platform] = platform_data
            yield _sse_event("scraper_result", platform_data)
            logger.warning(f"[{platform}] ✖ Scraper failed: {result.error}")

    # ──────────────────────────────────────────────
    # Step 3: ML Analysis
    # ──────────────────────────────────────────────
    yield _sse_event("status", {"step": "ml", "message": "Running ML price analysis..."})

    all_clean_prices = [p.price_clean for p in all_products if p.price_clean > 0]
    ml_result = analyze_prices(all_clean_prices)
    ml_dict = ml_result.to_dict()

    yield _sse_event("status", {"step": "ml", "message": "Generating AI pricing strategy explanation..."})
    explanation = await explain_recommendation(product_name, ml_dict)
    ml_dict["explanation"] = explanation

    yield _sse_event("ml_analysis", ml_dict)

    # ──────────────────────────────────────────────
    # Step 4: Find overall best deal
    # ──────────────────────────────────────────────
    best_overall = None
    best_overall_price = float("inf")
    best_overall_platform = ""
    best_overall_url = ""

    for platform, data in platform_results.items():
        if data.get("success") and data.get("best_price"):
            if data["best_price"] < best_overall_price:
                best_overall_price = data["best_price"]
                best_overall_platform = platform
                best_overall_url = data.get("best_url", "")

    # ──────────────────────────────────────────────
    # Step 5: Final complete event
    # ──────────────────────────────────────────────
    total_time = round(time.perf_counter() - total_start, 2)

    final_payload = {
        "success": True,
        "product_name": product_name,
        "brand": vision_result.get("brand", "Unknown"),
        "category": vision_result.get("category", "General"),
        "vision_confidence": vision_result.get("confidence", 0),
        "platforms": platform_results,
        "ml_analysis": ml_dict,
        "best_platform": best_overall_platform,
        "best_price": best_overall_price if best_overall_price < float("inf") else 0,
        "best_price_formatted": format_inr(best_overall_price) if best_overall_price < float("inf") else "N/A",
        "best_url": best_overall_url,
        "total_time": total_time,
        "total_products_found": len(all_products),
    }

    yield _sse_event("complete", final_payload)
    logger.info(f"Analysis complete in {total_time}s — {len(all_products)} products across {len(platform_results)} platforms")


# ══════════════════════════════════════════════════
# SSE Streaming Endpoint (primary)
# ══════════════════════════════════════════════════
@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    Upload a product image → receive SSE stream with real-time results.
    Each scraper sends data as it finishes.
    """
    image_bytes = await file.read()

    return StreamingResponse(
        _run_analysis(image_bytes),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ══════════════════════════════════════════════════
# Legacy Endpoint (backward compatible, non-streaming)
# ══════════════════════════════════════════════════
@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Legacy endpoint — waits for all results and returns a single JSON response.
    Compatible with the existing frontend.
    """
    image_bytes = await file.read()

    # Run vision
    try:
        img = Image.open(io.BytesIO(image_bytes))
        vision_result = await identify_product(img)
    except Exception as exc:
        return {"error": f"Vision AI failed: {exc}"}

    product_name = vision_result.get("product_name", "Unknown Product")
    search_queries = vision_result.get("search_queries", [product_name])
    primary_query = search_queries[0] if search_queries else product_name

    # Run scrapers with bounded concurrency so retries+delays do not all time out together.
    sem = asyncio.Semaphore(SCRAPER_MAX_CONCURRENT)

    async def _run_one(scraper):
        async with sem:
            return await scraper.safe_scrape(primary_query)

    results = await asyncio.gather(*[_run_one(s) for s in SCRAPERS])

    all_products = []
    platform_data = {}

    for result in results:
        if result.success:
            normalized = normalize_products(result.products)
            all_products.extend(normalized)

            best = None
            best_url = ""
            for p in normalized:
                if p.price_clean > 0 and (best is None or p.price_clean < best):
                    best = p.price_clean
                    best_url = p.url

            platform_data[result.platform] = {
                "platform": result.platform,
                "price": format_inr(best) if best else "N/A",
                "price_formatted": format_inr(best) if best else "N/A",  # frontend uses both
                "price_raw": best,
                "best_price": best,
                "best_price_formatted": format_inr(best) if best else "N/A",
                "url": best_url,
                "best_url": best_url,
                "product_count": len(normalized),
                "success": True,
            }
        else:
            platform_data[result.platform] = {
                "platform": result.platform,
                "price": "N/A",
                "price_formatted": "N/A",
                "best_price": 0,
                "best_price_formatted": "N/A",
                "url": "#",
                "product_count": 0,
                "success": False,
                "error": result.error,
            }
            logger.warning(f"[{result.platform}] ✖ Legacy scraper failed: {result.error}")

    # ML Analysis
    clean_prices = [p.price_clean for p in all_products if p.price_clean > 0]
    ml_result = analyze_prices(clean_prices)
    ml_dict = ml_result.to_dict()
    explanation = await explain_recommendation(product_name, ml_dict)
    ml_dict["explanation"] = explanation

    # Find best
    best_platform = ""
    best_price = float("inf")
    best_url = ""
    for name, data in platform_data.items():
        if data.get("price_raw") and data["price_raw"] < best_price:
            best_price = data["price_raw"]
            best_platform = name
            best_url = data.get("url", "")

    return {
        "product_name": product_name,
        "brand": vision_result.get("brand", "Unknown"),
        "category": vision_result.get("category", "General"),
        "confidence": vision_result.get("confidence", 0),
        # Flat keys for backward compatibility
        "amazon_price": platform_data.get("Amazon", {}).get("price", "N/A"),
        "amazon_url": platform_data.get("Amazon", {}).get("url", "#"),
        "flipkart_price": platform_data.get("Flipkart", {}).get("price", "N/A"),
        "flipkart_url": platform_data.get("Flipkart", {}).get("url", "#"),
        "ebay_price": platform_data.get("eBay", {}).get("price", "N/A"),
        "ebay_url": platform_data.get("eBay", {}).get("url", "#"),
        "meesho_price": platform_data.get("Meesho", {}).get("price", "N/A"),
        "meesho_url": platform_data.get("Meesho", {}).get("url", "#"),
        "reliance_price": platform_data.get("Reliance Digital", {}).get("price", "N/A"),
        "reliance_url": platform_data.get("Reliance Digital", {}).get("url", "#"),
        # ML analysis
        "ml_analysis": ml_dict,
        # Best deal
        "best_platform": best_platform,
        "best_price": format_inr(best_price) if best_price < float("inf") else "N/A",
        "best_url": best_url,
        # Platforms detailed
        "platforms": platform_data,
    }
