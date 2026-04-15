import re
import logging
import urllib.parse
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, ScrapeResult, ScrapedProduct

logger = logging.getLogger(__name__)

class FlipkartScraper(BaseScraper):
    platform = "Flipkart"
    # Unified search URL
    BASE_URL = "https://www.flipkart.com/search?q={query}"

    async def scrape(self, query: str) -> ScrapeResult:
        search_url = self.BASE_URL.format(query=urllib.parse.quote_plus(query))
        
        # Use our stealth-impersonated fetcher
        html = await self._fetch(search_url)
        if not html:
            return ScrapeResult(self.platform, False, error="Blocked by Flipkart Firewall")

        soup = BeautifulSoup(html, "lxml")
        products = []

        # ── DISCOVERY MODE: Broad search for product units ──
        # Flipkart uses different layouts for different categories
        containers = soup.select("div[data-id]") or soup.select("div._1AtVbE") or soup.select("div._13oc-S")
        
        if not containers:
            # Fallback to broad div search if specific ones are missing
            containers = soup.find_all("div", recursive=False)

        for card in containers[:10]:
            try:
                # 1. Product Name Extraction
                title_el = (card.select_one("div._4rR01T") or 
                            card.select_one("a.s1Q9rs") or 
                            card.select_one("a.IRpwTa") or
                            card.select_one("div[class*='title']"))
                
                title = title_el.get_text(strip=True) if title_el else "Flipkart Product"
                if len(title) < 5: continue

                # 2. Aggressive Price Discovery (Regex)
                # We search the entire text of the card for the ₹ symbol and digits
                card_text = card.get_text()
                # Pattern: Find ₹ followed by numbers, potentially with commas
                prices = re.findall(r"₹\s?([\d,]+)", card_text)
                
                if not prices: continue
                
                # Take the first prominent number as the price (ignoring small discount numbers)
                best_price_str = prices[0].replace(",", "")
                # Ensure it's a realistic price (not 0 or too small)
                if int(best_price_str) < 10: 
                    if len(prices) > 1:
                        best_price_str = prices[1].replace(",", "")
                    else: continue

                # 3. Link Extraction
                link_el = card.find("a", href=True)
                link = "https://www.flipkart.com" + link_el["href"] if link_el else "#"

                products.append(ScrapedProduct(
                    platform=self.platform,
                    product_name=title,
                    price_raw="₹" + best_price_str,
                    url=link
                ))
            except Exception:
                continue

        return ScrapeResult(self.platform, len(products) > 0, products=products)
