import re
import logging
import urllib.parse
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScrapeResult, ScrapedProduct

logger = logging.getLogger(__name__)

class SnapdealScraper(BaseScraper):
    platform = "Snapdeal"
    BASE_URL = "https://www.snapdeal.com/search?keyword={query}"

    async def scrape(self, query: str) -> ScrapeResult:
        search_url = self.BASE_URL.format(query=urllib.parse.quote(query))
        html = await self._fetch(search_url)
        if not html:
            return ScrapeResult(self.platform, False, error="Snapdeal Handshake Failed")

        soup = BeautifulSoup(html, "lxml")
        products = []
        
        # Snapdeal tuple listing
        items = soup.select(".product-tuple-listing") or soup.find_all("div", class_="product-tuple-listing")

        for item in items[:10]:
            try:
                title_el = item.select_one(".product-title")
                title = title_el.get_text(strip=True) if title_el else "Snapdeal Item"

                # Price Discovery
                prices = re.findall(r"Rs\.\s?([\d,]+)", item.get_text())
                if not prices:
                    prices = re.findall(r"₹\s?([\d,]+)", item.get_text())
                
                if not prices: continue
                price_text = "₹" + prices[0]

                link_el = item.select_one("a.dp-widget-link") or item.find("a")
                link = link_el["href"] if link_el else "#"
                if link != "#" and not link.startswith("http"):
                    link = "https://www.snapdeal.com" + link

                products.append(ScrapedProduct(
                    platform=self.platform,
                    product_name=title,
                    price_raw=price_text,
                    url=link
                ))
            except Exception: continue

        return ScrapeResult(self.platform, len(products) > 0, products=products)
