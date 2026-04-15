import re
import logging
import urllib.parse
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScrapeResult, ScrapedProduct

logger = logging.getLogger(__name__)

class MeeshoScraper(BaseScraper):
    platform = "Meesho"
    BASE_URL = "https://www.meesho.com/search?q={query}"

    async def scrape(self, query: str) -> ScrapeResult:
        url = self.BASE_URL.format(query=urllib.parse.quote_plus(query))
        html = await self._playwright_fetch(url)
        raw_html = await self._fetch(url)
        if raw_html:
            if not html:
                html = raw_html
            else:
                current_count = len(self._extract_prices_from_html(html, query, url, limit=20))
                raw_count = len(self._extract_prices_from_html(raw_html, query, url, limit=20))
                if raw_count > current_count:
                    html = raw_html
        if not html:
            fallback_products = await self._search_index_fallback(query, "meesho.com")
            return ScrapeResult(
                self.platform,
                len(fallback_products) > 0,
                products=fallback_products,
                error="" if fallback_products else "Meesho Browser Blocked",
            )

        soup = BeautifulSoup(html, "lxml")
        products = []
        
        # Meesho uses generic class names (ProductCard)
        items = soup.find_all("div", class_=re.compile(r"ProductCard|product-card"))

        for item in items[:10]:
            try:
                title_el = item.find(["p", "span"], class_=re.compile(r"Title"))
                title = title_el.get_text(strip=True) if title_el else "Meesho Item"

                # Aggressive Price Discovery
                prices = re.findall(r"₹\s?([\d,]+)", item.get_text())
                if not prices: continue
                price_text = "₹" + prices[0]

                link_el = item.find("a", href=True)
                link = "https://www.meesho.com" + link_el["href"] if link_el else "#"

                products.append(ScrapedProduct(
                    platform=self.platform,
                    product_name=title,
                    price_raw=price_text,
                    url=link
                ))
            except Exception: continue

        if products:
            return ScrapeResult(self.platform, True, products=products)

        fallback_products = await self._search_index_fallback(query, "meesho.com")
        if not fallback_products and html:
            fallback_products = self._extract_prices_from_html(html, query, url)
        if not fallback_products:
            fallback_products = await self._scrape_prices_from_discovered_urls(query, "meesho.com")
        return ScrapeResult(
            self.platform,
            len(fallback_products) > 0,
            products=fallback_products,
            error="" if fallback_products else "No products found on Meesho",
        )
