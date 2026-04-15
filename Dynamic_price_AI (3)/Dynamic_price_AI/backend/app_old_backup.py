from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DRIVER ----------
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# ---------- SCRAPER TEMPLATE ----------
def scrape_site(url, price_xpath, link_xpath=None):
    driver = get_driver()
    driver.get(url)
    time.sleep(4)

    try:
        price = driver.find_element(By.XPATH, price_xpath).text
    except:
        price = "N/A"

    try:
        link = driver.find_element(By.XPATH, link_xpath).get_attribute("href") if link_xpath else url
    except:
        link = url

    driver.quit()
    return {"price": price, "url": link}


# ---------- SITES ----------
def amazon(product):
    return scrape_site(
        f"https://www.amazon.in/s?k={urllib.parse.quote(product)}",
        "(//span[@class='a-price-whole'])[1]",
        "(//h2/a)[1]"
    )

def flipkart(product):
    return scrape_site(
        f"https://www.flipkart.com/search?q={urllib.parse.quote(product)}",
        "(//div[contains(text(),'₹')])[1]",
        "(//a[contains(@href,'/p/')])[1]"
    )

def ebay(product):
    return scrape_site(
        f"https://www.ebay.com/sch/i.html?_nkw={urllib.parse.quote(product)}",
        "(//span[@class='s-item__price'])[1]",
        "(//a[@class='s-item__link'])[1]"
    )

def meesho(product):
    return scrape_site(
        f"https://www.meesho.com/search?q={urllib.parse.quote(product)}",
        "(//h5)[1]"
    )

def reliance(product):
    return scrape_site(
        f"https://www.reliancedigital.in/search?q={urllib.parse.quote(product)}",
        "(//span[contains(text(),'₹')])[1]"
    )


# ---------- BEST PRICE ----------
def get_best(results):
    prices = {}
    for k, v in results.items():
        try:
            prices[k] = int(''.join(filter(str.isdigit, v["price"])))
        except:
            pass
    return min(prices, key=prices.get) if prices else "No Data"


# ---------- API ----------
@app.post("/upload")
def upload(file: UploadFile):
    image = Image.open(io.BytesIO(file.file.read()))

    product_name = "Samsung Galaxy Watch 4"

    sites = {
        "Amazon": amazon,
        "Flipkart": flipkart,
        "eBay": ebay,
        "Meesho": meesho,
        "Reliance": reliance
    }

    results = {}

    # 🔥 PARALLEL EXECUTION
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {executor.submit(func, product_name): name for name, func in sites.items()}

        for future in future_map:
            name = future_map[future]
            try:
                results[name] = future.result()
            except:
                results[name] = {"price": "N/A", "url": "#"}

    best = get_best(results)

    print("FINAL RESULTS:", results)

    return {
        "product_name": product_name,
        "results": results,
        "best_platform": best
    }