import re
import logging
import urllib.parse
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScrapeResult, ScrapedProduct

logger = logging.getLogger(__name__)

class RelianceScraper(BaseScraper):
    platform = "Reliance Digital"
    BASE_URL = "https://www.reliancedigital.in/search?q={query}"

    async def scrape(self, query: str) -> ScrapeResult:
        search_url = self.BASE_URL.format(query=urllib.parse.quote_plus(query))
        # Prefer fast direct fetch first (more stable than browser here).
        html = await self._fetch_fast(search_url, timeout=12)
        if not html:
            html = await self._playwright_fetch(search_url)
        if not html:
            html = await self._fetch(search_url)
        if not html:
            fallback_products = await self._search_index_fallback(query, "reliancedigital.in")
            return ScrapeResult(
                self.platform,
                len(fallback_products) > 0,
                products=fallback_products,
                error="" if fallback_products else "Reliance Browser Blocked",
            )

        soup = BeautifulSoup(html, "lxml")
        products = []
        
        # Reliance uses li.product-item or specific grid cards
        items = soup.select("li.product-item") or soup.select("div.sp__product") or soup.select("div.plp-grid-card")

        for item in items[:10]:
            try:
                title_el = item.select_one(".sp__name") or item.select_one("p")
                title = title_el.get_text(strip=True) if title_el else "Reliance Digital Item"

                # Price Discovery
                card_text = item.get_text()
                prices = re.findall(r"₹\s?([\d,]+)", card_text)
                
                if not prices: continue
                price_text = "₹" + prices[0]

                link_el = item.find("a", href=True)
                link = "https://www.reliancedigital.in" + link_el["href"] if link_el else "#"

                products.append(ScrapedProduct(
                    platform=self.platform,
                    product_name=title,
                    price_raw=price_text,
                    url=link
                ))
            except Exception: continue

        if products:
            return ScrapeResult(self.platform, True, products=products)

        fallback_products = await self._search_index_fallback(query, "reliancedigital.in")
        if not fallback_products and html:
            fallback_products = self._extract_prices_from_html(html, query, search_url)
        if not fallback_products:
            fallback_products = await self._scrape_prices_from_discovered_urls(query, "reliancedigital.in")
        return ScrapeResult(
            self.platform,
            len(fallback_products) > 0,
            products=fallback_products,
            error="" if fallback_products else "No products found on Reliance Digital",
        )
