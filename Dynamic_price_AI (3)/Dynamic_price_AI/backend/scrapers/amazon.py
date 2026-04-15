"""
Amazon India scraper — httpx + BeautifulSoup.
Multi-selector approach for resilience against layout changes.
"""
import re
import logging
import urllib.parse

from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScrapeResult, ScrapedProduct

logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    platform = "Amazon"
    BASE_URL = "https://www.amazon.in/s?k={query}"

    # Multiple CSS selector strategies — fallbacks for layout changes
    PRICE_SELECTORS = [
        "span.a-price span.a-offscreen",
        "span.a-price-whole",
        ".a-color-price",
        "span.a-offscreen",
    ]

    TITLE_SELECTORS = [
        "h2 a span",
        "h2 span.a-text-normal",
        "div[data-cy='title-recipe'] h2 span",
        "span.a-size-medium.a-color-base.a-text-normal",
    ]

    LINK_SELECTORS = [
        "h2 a.a-link-normal",
        "a.a-link-normal.s-no-outline",
        "div[data-cy='title-recipe'] a",
    ]

    async def scrape(self, query: str) -> ScrapeResult:
        url = self.BASE_URL.format(query=urllib.parse.quote_plus(query))
        html = await self._fetch(url)

        if not html:
            return ScrapeResult(
                platform=self.platform,
                success=False,
                error="Failed to fetch Amazon search page",
            )

        if "api-services-support@amazon.com" in html or "robot check" in html.lower():
            logger.warning("[Amazon] Blocked by bot detection (CAPTCHA)")
            return ScrapeResult(
                platform=self.platform,
                success=False,
                error="CAPTCHA/Bot Blocked",
            )

        soup = BeautifulSoup(html, "lxml")
        products: list[ScrapedProduct] = []

        # Try multiple container strategies
        cards = (
            soup.select("div[data-component-type='s-search-result']")
            or soup.select("div.s-result-item[data-asin]")
            or soup.select(".s-card-container")
        )
        
        if not cards:
            logger.debug(f"[Amazon] No cards found using primary selectors. HTML length: {len(html)}")

        for card in cards[:15]:  # top 15
            asin = card.get("data-asin", "")
            
            # Skip empty markers
            if not asin and not card.select_one("h2"):
                continue

            # ─── Title ───
            title = ""
            for sel in self.TITLE_SELECTORS:
                el = card.select_one(sel)
                if el and el.get_text(strip=True):
                    title = el.get_text(strip=True)
                    break

            if not title or len(title) < 5:
                continue

            # ─── Price ───
            price_raw = ""
            # Strategy 1: specific price span
            for sel in self.PRICE_SELECTORS:
                el = card.select_one(sel)
                if el:
                    txt = el.get_text(strip=True)
                    if any(c.isdigit() for c in txt):
                        price_raw = txt
                        break
            
            # Strategy 2: regex fallback on card text if selector failed
            if not price_raw:
                price_match = re.search(r"₹\s?([\d,]+)", card.get_text())
                if price_match:
                    price_raw = price_match.group(0)

            if not price_raw:
                continue

            # ─── Link ───
            link = ""
            for sel in self.LINK_SELECTORS:
                el = card.select_one(sel)
                if el and el.get("href"):
                    href = el["href"]
                    if not href.startswith("http"):
                        href = "https://www.amazon.in" + href
                    link = href
                    break

            # ─── Rating & Reviews ───
            rating = None
            rating_el = card.select_one("span.a-icon-alt")
            if rating_el:
                rm = re.search(r"([\d.]+)", rating_el.get_text())
                if rm: rating = float(rm.group(1))

            reviews = None
            review_el = card.select_one("span.a-size-base.s-underline-text")
            if review_el:
                rvm = re.search(r"([\d,]+)", review_el.get_text())
                if rvm: reviews = int(rvm.group(1).replace(",", ""))

            products.append(
                ScrapedProduct(
                    platform=self.platform,
                    product_name=title,
                    price_raw=price_raw,
                    url=link,
                    rating=rating,
                    reviews=reviews,
                )
            )

        logger.info(f"[Amazon] Found {len(products)} products for '{query}'")
        return ScrapeResult(
            platform=self.platform,
            success=len(products) > 0,
            products=products,
            error="" if products else "No products found on Amazon search page",
        )
