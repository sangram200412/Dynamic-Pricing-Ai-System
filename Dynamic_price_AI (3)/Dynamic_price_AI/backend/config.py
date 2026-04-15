"""
Central configuration — loads .env, exposes typed settings.
"""
import os
from dotenv import load_dotenv

# ✅ Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── API Keys ────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# ── OpenRouter Settings ─────────────────────────────
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL: str = "google/gemini-flash-1.5"
OPENROUTER_TIMEOUT: int = 45  # Configurable timeout for AI calls

# ── Gemini Direct Settings ──────────────────────────
GEMINI_MODEL: str = "gemini-1.5-flash-latest"

# ── Scraper Tuning ──────────────────────────────────
# Parallel runs need headroom: each scraper may retry + delay; 7 at once is heavy.
SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "55"))
SCRAPER_MAX_RETRIES: int = int(os.getenv("SCRAPER_MAX_RETRIES", "2"))
SCRAPER_DELAY_MIN: float = float(os.getenv("SCRAPER_DELAY_MIN", "0.4"))
SCRAPER_DELAY_MAX: float = float(os.getenv("SCRAPER_DELAY_MAX", "1.6"))
# Max concurrent scrapers (rest are queued) — reduces timeouts when all hit the network at once.
SCRAPER_MAX_CONCURRENT: int = int(os.getenv("SCRAPER_MAX_CONCURRENT", "4"))

# ── ML Tuning ───────────────────────────────────────
ML_CLUSTERS: int = 3               # budget / mid / premium
ML_OUTLIER_CONTAMINATION: float = 0.1

# ── Currency ────────────────────────────────────────
DEFAULT_CURRENCY: str = "INR"

# ── Rotating User Agents ───────────────────────────
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
]

# ── CORS ────────────────────────────────────────────
ALLOWED_ORIGINS: list[str] = ["*"]