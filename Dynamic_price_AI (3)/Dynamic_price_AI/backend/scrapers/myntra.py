import re
import logging
import urllib.parse
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScrapeResult, ScrapedProduct

logger = logging.getLogger(__name__)

class MyntraScraper(BaseScraper):
    platform = "Myntra"
    BASE_URL = "https://www.myntra.com/search?q={query}"

    async def scrape(self, query: str) -> ScrapeResult:
        search_url = f"https://www.myntra.com/search?q={urllib.parse.quote(query)}"
        html = await self._playwright_fetch(search_url)
        if not html or len(html) < 120000:
            raw_html = await self._fetch(search_url)
            if raw_html and len(raw_html) > len(html or ""):
                html = raw_html
        if not html:
            fallback_products = await self._search_index_fallback(query, "myntra.com")
            return ScrapeResult(
                self.platform,
                len(fallback_products) > 0,
                products=fallback_products,
                error="" if fallback_products else "Myntra Browser Blocked",
            )

        soup = BeautifulSoup(html, "lxml")
        products = []
        
        # Myntra product components
        items = soup.select(".product-base") or soup.find_all("li", class_="product-base")

        for item in items[:10]:
            try:
                # Title & Brand
                brand_el = item.select_one(".product-brand")
                title_el = item.select_one(".product-product")
                
                brand = brand_el.get_text(strip=True) if brand_el else ""
                title = title_el.get_text(strip=True) if title_el else "Myntra Item"

                # Price Discovery
                prices = re.findall(r"Rs\.\s?([\d,]+)", item.get_text())
                if not prices:
                    prices = re.findall(r"₹\s?([\d,]+)", item.get_text())
                
                if not prices: continue
                price_text = "₹" + prices[0]

                link_el = item.find("a", href=True)
                link = "https://www.myntra.com/" + link_el["href"] if link_el else "#"

                products.append(ScrapedProduct(
                    platform=self.platform,
                    product_name=f"{brand} {title}".strip(),
                    price_raw=price_text,
                    url=link
                ))
            except Exception: continue

        if products:
            return ScrapeResult(self.platform, True, products=products)

        fallback_products = await self._search_index_fallback(query, "myntra.com")
        if not fallback_products and html:
            fallback_products = self._extract_prices_from_html(html, query, search_url)
        return ScrapeResult(
            self.platform,
            len(fallback_products) > 0,
            products=fallback_products,
            error="" if fallback_products else "No products found on Myntra",
        )
