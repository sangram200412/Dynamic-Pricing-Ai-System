"""
Dynamic Pricing Intelligence — FastAPI Application Entry Point.

Production-ready backend with:
  • Vision AI product identification (OpenRouter / Gemini 2.0 Flash)
  • Async multi-platform price scraping (5 sources)
  • ML-based price analysis (KMeans + Isolation Forest)
  • Server-Sent Events (SSE) streaming
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from api.routes import router

# ── Logging ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-25s │ %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("pricescope")

# Suppress noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# ── App ─────────────────────────────────────────────
app = FastAPI(
    title="PriceScope Intelligence API",
    description="AI-powered dynamic pricing intelligence — image to market analysis in real-time",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "PriceScope Intelligence API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "POST /analyze": "SSE streaming analysis (recommended)",
            "POST /upload": "Legacy JSON response",
            "GET /docs": "Interactive API documentation",
            "GET /health": "Health check",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "pricescope-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
