import asyncio
from scrapers.amazon import AmazonScraper
from scrapers.flipkart import FlipkartScraper
from scrapers.ebay import EbayScraper
from scrapers.meesho import MeeshoScraper
from scrapers.reliance import RelianceScraper

async def main():
    query = 'iphone 15'
    scrapers = [AmazonScraper(), FlipkartScraper(), EbayScraper(), MeeshoScraper(), RelianceScraper()]
    for s in scrapers:
        print(f"Testing {s.__class__.__name__}...")
        res = await s.safe_scrape(query)
        print(f'{res.platform}: Success={res.success}, Found={len(res.products)}, Error={res.error}')
        if not res.success or len(res.products) == 0:
            print(f"Failed. Error: {res.error}")

if __name__ == '__main__':
    asyncio.run(main())
