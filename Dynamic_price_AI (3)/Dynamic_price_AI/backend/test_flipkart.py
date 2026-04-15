import asyncio
import logging
from scrapers.flipkart import FlipkartScraper

logging.basicConfig(level=logging.ERROR)

async def test():
    s = FlipkartScraper()
    print("Testing Playwright...")
    r = await s._scrape_playwright('iphone 15')
    print(f"Success: {r.success}, Error: {r.error}")

if __name__ == "__main__":
    asyncio.run(test())
