import re
import logging
import urllib.parse
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScrapeResult, ScrapedProduct

logger = logging.getLogger(__name__)

class EbayScraper(BaseScraper):
    platform = "eBay"
    BASE_URL = "https://www.ebay.in/sch/i.html?_nkw={query}"

    async def scrape(self, query: str) -> ScrapeResult:
        search_url = self.BASE_URL.format(query=urllib.parse.quote_plus(query))
        html = await self._playwright_fetch(search_url)
        raw_html = await self._fetch(search_url)
        if raw_html:
            if not html:
                html = raw_html
            else:
                current_count = len(self._extract_prices_from_html(html, query, search_url, limit=20))
                raw_count = len(self._extract_prices_from_html(raw_html, query, search_url, limit=20))
                if raw_count > current_count:
                    html = raw_html
        if not html:
            fallback_products = await self._search_index_fallback(query, "ebay.in")
            return ScrapeResult(
                self.platform,
                len(fallback_products) > 0,
                products=fallback_products,
                error="" if fallback_products else "eBay Browser Blocked",
            )

        soup = BeautifulSoup(html, "lxml")
        products = []
        
        # eBay uses .s-item as their primary container
        items = soup.select("div.s-item__wrapper") or soup.select("li.s-item")
        
        for item in items[:10]:
            try:
                title_el = item.select_one(".s-item__title")
                title = title_el.get_text(strip=True) if title_el else "eBay Item"
                if "Shop on eBay" in title: continue

                # Price Discovery: look for $ or ₹ patterns
                price_text = item.select_one(".s-item__price").get_text() if item.select_one(".s-item__price") else ""
                if not price_text:
                    # Regex fallback
                    prices = re.findall(r"[\$\₹]\s?([\d,]+\.?\d*)", item.get_text())
                    price_text = prices[0] if prices else ""

                link_el = item.select_one("a.s-item__link")
                link = link_el["href"] if link_el else "#"

                if price_text:
                    products.append(ScrapedProduct(
                        platform=self.platform,
                        product_name=title,
                        price_raw=price_text,
                        url=link
                    ))
            except Exception: continue

        if products:
            return ScrapeResult(self.platform, True, products=products)

        fallback_products = await self._search_index_fallback(query, "ebay.in")
        if not fallback_products and html:
            fallback_products = self._extract_prices_from_html(html, query, search_url)
        if not fallback_products:
            fallback_products = await self._scrape_prices_from_discovered_urls(query, "ebay.in")
        return ScrapeResult(
            self.platform,
            len(fallback_products) > 0,
            products=fallback_products,
            error="" if fallback_products else "No products found on eBay",
        )
