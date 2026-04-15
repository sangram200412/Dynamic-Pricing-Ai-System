"""
Base scraper — shared infrastructure for all scrapers.
  • Rotating user-agents
  • Random delay (1–4 sec)
  • Retry logic (max 3 retries)
  • Timeout (25 sec per scraper)
"""
import asyncio
import random
import logging
import re
import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError
from bs4 import BeautifulSoup

from config import (
    USER_AGENTS,
    SCRAPER_TIMEOUT,
    SCRAPER_MAX_RETRIES,
    SCRAPER_DELAY_MIN,
    SCRAPER_DELAY_MAX,
)

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Single scraped listing."""
    platform: str
    product_name: str = ""
    price_raw: str = ""
    price_clean: float = 0.0
    currency: str = "INR"
    url: str = ""
    seller: str = ""
    rating: Optional[float] = None
    reviews: Optional[int] = None
    in_stock: bool = True
    image_url: str = ""


@dataclass
class ScrapeResult:
    """Full result from one platform."""
    platform: str
    success: bool = False
    products: list[ScrapedProduct] = field(default_factory=list)
    error: str = ""
    time_taken: float = 0.0


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    platform: str = "unknown"

    def __init__(self):
        self.timeout = SCRAPER_TIMEOUT
        self.max_retries = SCRAPER_MAX_RETRIES
        self.delay_min = SCRAPER_DELAY_MIN
        self.delay_max = SCRAPER_DELAY_MAX

    def _random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    def _headers(self) -> dict:
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self._random_ua(),
        }

    async def _delay(self):
        wait = random.uniform(self.delay_min, self.delay_max)
        logger.debug(f"[{self.platform}] Sleeping {wait:.1f}s")
        await asyncio.sleep(wait)

    async def _fetch(self, url: str) -> Optional[str]:
        """HTTP GET with retry + timeout."""
        domain = url.split("//")[-1].split("/")[0]
        for attempt in range(1, self.max_retries + 1):
            try:
                await self._delay()
                headers = self._headers()
                headers["Referer"] = f"https://{domain}/"

                # Rotate impersonation to bypass fingerprinting
                target = random.choice(["chrome", "safari", "edge"])
                
                async with requests.AsyncSession(
                    impersonate=target,
                    timeout=self.timeout,
                    verify=False,
                ) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        return resp.text
                    elif resp.status_code == 404:
                        logger.warning(f"[{self.platform}] 404 Not Found: {url}")
                        return None
                    
                    logger.warning(
                        f"[{self.platform}] Attempt {attempt}: HTTP {resp.status_code}"
                    )
            except RequestsError as req_err:
                logger.warning(f"[{self.platform}] Attempt {attempt}: RequestsError: {req_err}")
            except Exception as exc:
                logger.warning(f"[{self.platform}] Attempt {attempt}: {exc}")

            if attempt < self.max_retries:
                backoff = attempt * 2
                logger.info(f"[{self.platform}] Retrying in {backoff}s …")
                await asyncio.sleep(backoff)

        return None

    async def _fetch_fast(self, url: str, timeout: int = 12) -> Optional[str]:
        """Single-attempt fast fetch without random delay/backoff."""
        try:
            headers = self._headers()
            domain = url.split("//")[-1].split("/")[0]
            headers["Referer"] = f"https://{domain}/"
            async with requests.AsyncSession(
                impersonate="chrome",
                timeout=timeout,
                verify=False,
            ) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text
        except Exception:
            return None
        return None

    async def _playwright_fetch(self, url: str, wait_selector: str = "body") -> Optional[str]:
        """Fetch page using a real browser instance for stubborn sites."""
        from playwright.async_api import async_playwright
        logger.info(f"[{self.platform}] Launching browser fetch for {url}...")
        
        pw = None
        browser = None
        try:
            pw = await async_playwright().start()
            # Added stability flags to prevent PROTOCOL_ERROR and crashes
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            context = await browser.new_context(
                user_agent=self._random_ua(),
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            
            # Use a reasonable timeout
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Auto-scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            await asyncio.sleep(1.5)
            
            html = await page.content()
            return html
        except Exception as e:
            logger.warning(f"[{self.platform}] Browser fetch failed: {e}")
            # Fall back to regular HTTP fetch
            return await self._fetch(url)
        finally:
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            if pw:
                try:
                    await pw.stop()
                except:
                    pass

    async def _search_index_fallback(self, query: str, site_domain: str) -> list[ScrapedProduct]:
        """
        Fallback extraction using DuckDuckGo HTML results.
        Useful when direct platform scraping is blocked by anti-bot protections.
        """
        search_query = f"site:{site_domain} {query} price"
        search_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(search_query)
        # Keep fallback fast: avoid scraper-level random delays/backoff.
        try:
            headers = {
                "User-Agent": self._random_ua(),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://duckduckgo.com/",
            }
            async with requests.AsyncSession(
                impersonate="chrome",
                timeout=10,
                verify=False,
            ) as client:
                resp = await client.get(search_url, headers=headers)
                html = resp.text if resp.status_code == 200 else ""
        except Exception:
            html = ""
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        products: list[ScrapedProduct] = []

        result_cards = soup.select("div.result") or soup.select(".results .result")
        for card in result_cards[:20]:
            title_el = card.select_one("a.result__a")
            snippet_el = card.select_one(".result__snippet")
            if not title_el:
                continue

            href = title_el.get("href", "")
            title = title_el.get_text(" ", strip=True)
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            haystack = f"{title} {snippet}"

            prices = re.findall(r"(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{1,2})?)", haystack, flags=re.IGNORECASE)
            if not prices:
                continue

            products.append(
                ScrapedProduct(
                    platform=self.platform,
                    product_name=title[:120],
                    price_raw=f"₹{prices[0]}",
                    url=href,
                )
            )

        if products:
            logger.info(f"[{self.platform}] Fallback index yielded {len(products)} products")
        return products

    async def _discover_product_urls(self, query: str, site_domain: str, max_urls: int = 8) -> list[str]:
        """Discover product URLs from DuckDuckGo HTML results."""
        ddg_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(f"site:{site_domain} {query}")
        html = await self._fetch_fast(ddg_url, timeout=10)
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            if not href:
                continue
            if "duckduckgo.com/l/?" in href:
                parsed = urllib.parse.urlparse(href)
                q = urllib.parse.parse_qs(parsed.query)
                href = q.get("uddg", [href])[0]
            if site_domain not in href:
                continue
            if "/search" in href or "/sch/i.html" in href:
                continue
            if href not in urls:
                urls.append(href)
            if len(urls) >= max_urls:
                break
        return urls

    async def _scrape_prices_from_discovered_urls(self, query: str, site_domain: str, max_products: int = 8) -> list[ScrapedProduct]:
        """
        Crawl discovered product URLs (via search results) and extract price tokens.
        Uses r.jina.ai mirror to reduce anti-bot failures.
        """
        urls = await self._discover_product_urls(query, site_domain, max_urls=max_products * 2)
        products: list[ScrapedProduct] = []
        for url in urls:
            mirror = "https://r.jina.ai/http://" + url
            text = await self._fetch_fast(mirror, timeout=12)
            if not text:
                continue
            # Prefer INR/Rs; fallback to USD.
            price_match = re.search(r"(?:₹|Rs\.?|INR)\s*([0-9][0-9,]{1,10}(?:\.[0-9]{1,2})?)", text, flags=re.IGNORECASE)
            currency = "INR"
            if not price_match:
                price_match = re.search(r"\$\s*([0-9][0-9,]{1,10}(?:\.[0-9]{1,2})?)", text)
                currency = "USD"
            if not price_match:
                continue
            price_raw = price_match.group(0).replace("INR", "₹")
            if currency == "USD":
                price_raw = "$" + price_match.group(1)
            title_match = re.search(r"Title:\s*(.+)", text)
            title = title_match.group(1).strip() if title_match else f"{query} ({self.platform})"
            products.append(
                ScrapedProduct(
                    platform=self.platform,
                    product_name=title[:120],
                    price_raw=price_raw,
                    url=url,
                )
            )
            if len(products) >= max_products:
                break
        if products:
            logger.info(f"[{self.platform}] URL discovery fallback yielded {len(products)} products")
        return products

    def _extract_prices_from_html(self, html: str, query: str, default_url: str, limit: int = 10) -> list[ScrapedProduct]:
        """
        Last-resort fallback for heavily obfuscated pages.
        Extracts numeric price fields directly from embedded JSON/script text.
        """
        raw_prices = re.findall(
            r'"(?:discountedPrice|discounted_price|price|salePrice|selling_price|original_price|finalPrice|offerPrice|mrp|currentPrice|min_price|max_price)"\s*:\s*"?([0-9]{2,8}(?:\.[0-9]{1,2})?)"?',
            html,
            flags=re.IGNORECASE,
        )
        if len(raw_prices) < 3:
            raw_prices.extend(
                re.findall(
                    r"(?:₹|Rs\.?|INR)\s*([0-9][0-9,]{1,10}(?:\.[0-9]{1,2})?)",
                    html,
                    flags=re.IGNORECASE,
                )
            )
        products: list[ScrapedProduct] = []
        seen: set[str] = set()
        for p in raw_prices:
            p = p.replace(",", "")
            if p in seen:
                continue
            seen.add(p)
            products.append(
                ScrapedProduct(
                    platform=self.platform,
                    product_name=f"{query} ({self.platform})",
                    price_raw=f"₹{p}",
                    url=default_url,
                )
            )
            if len(products) >= limit:
                break
        if products:
            logger.info(f"[{self.platform}] HTML price fallback yielded {len(products)} products")
        return products

    @abstractmethod
    async def scrape(self, query: str) -> ScrapeResult:
        """Scrape the platform for `query`. Must be implemented by subclasses."""
        ...

    async def safe_scrape(self, query: str) -> ScrapeResult:
        """Run scrape() wrapped in timeout + error handling."""
        import time
        start = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                self.scrape(query), timeout=self.timeout
            )
            result.time_taken = round(time.perf_counter() - start, 2)
            return result
        except asyncio.TimeoutError:
            logger.error(f"[{self.platform}] Global timeout after {self.timeout}s")
            return ScrapeResult(
                platform=self.platform,
                success=False,
                error=f"Timeout after {self.timeout}s",
                time_taken=round(time.perf_counter() - start, 2),
            )
        except Exception as exc:
            logger.error(f"[{self.platform}] Fatal: {exc}")
            return ScrapeResult(
                platform=self.platform,
                success=False,
                error=str(exc),
                time_taken=round(time.perf_counter() - start, 2),
            )
