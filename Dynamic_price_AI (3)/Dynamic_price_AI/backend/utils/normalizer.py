"""
Price normalizer — cleans raw scraped prices into float INR values.
  • Removes currency symbols (₹, $, €, £, etc.)
  • Converts USD/EUR/GBP → INR using approximate rates
  • Handles price ranges (e.g. "$10 - $20" → average)
  • Handles comma-separated numbers
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Approximate exchange rates (updated periodically in production)
EXCHANGE_RATES = {
    "INR": 1.0,
    "USD": 83.5,
    "EUR": 91.0,
    "GBP": 106.0,
    "AUD": 55.0,
    "CAD": 62.0,
    "SGD": 63.0,
    "AED": 22.7,
    "JPY": 0.56,
    "CNY": 11.5,
}

# Currency symbol → code mapping
CURRENCY_SYMBOLS = {
    "₹": "INR",
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "A$": "AUD",
    "C$": "CAD",
    "S$": "SGD",
    "Rs": "INR",
    "Rs.": "INR",
    "INR": "INR",
    "USD": "USD",
    "US $": "USD",
    "US$": "USD",
}


def detect_currency(price_str: str) -> str:
    """Detect currency from price string."""
    price_str = price_str.strip()

    # Check longer symbols first
    for symbol, code in sorted(CURRENCY_SYMBOLS.items(), key=lambda x: -len(x[0])):
        if symbol in price_str:
            return code

    # Default to INR for Indian platforms
    return "INR"


def extract_numbers(price_str: str) -> list[float]:
    """Extract all numeric values from a price string."""
    # First remove common prefixes that might contain symbols
    # This prevents the issue where stripping symbols first makes prefix-matching fail
    cleaned = re.sub(r"(?:US\s*\$|Rs\.?|INR|USD|EUR|GBP|US\s*)", "", price_str, flags=re.IGNORECASE)
    # Then remove all standard currency symbols
    cleaned = re.sub(r"[₹$€£¥]", "", cleaned)
    cleaned = cleaned.strip()

    # Find all number patterns (supports commas and decimals)
    numbers = []
    # Match patterns like 1,299 or 1299.50
    for match in re.finditer(r"[\d,]+(?:\.\d+)?", cleaned):
        num_str = match.group().replace(",", "")
        if not num_str or num_str == ".":
            continue
        try:
            numbers.append(float(num_str))
        except ValueError:
            pass

    return numbers


def clean_price(price_raw: str, source_currency: str = "INR") -> Optional[float]:
    """
    Clean a raw price string → float in INR.

    Handles:
      - "₹1,299"          → 1299.0
      - "$15.99"           → 1335.765 (USD→INR)
      - "₹999 - ₹1,499"   → 1249.0 (average)
      - "Rs. 24,990"       → 24990.0
      - "1,23,456"         → 123456.0 (Indian numbering)
    """
    if not price_raw or price_raw.strip().upper() in ("N/A", "NA", "—", "-", ""):
        return None

    # Detect currency from the string itself
    detected_currency = detect_currency(price_raw)
    if detected_currency != "INR" and source_currency == "INR":
        source_currency = detected_currency

    numbers = extract_numbers(price_raw)

    if not numbers:
        return None

    # Filter out junk (ratings, years) but keep real low prices (e.g. ₹49 tees).
    numbers = [n for n in numbers if 1 <= n <= 10_000_000]

    if not numbers:
        return None

    # Handle multiple numbers — take the MAX (usually the main price)
    value = max(numbers)

    # Convert to INR
    rate = EXCHANGE_RATES.get(source_currency, 1.0)
    value_inr = value * rate

    return round(value_inr, 2)


def normalize_products(products: list) -> list:
    """
    Normalize a list of ScrapedProduct objects.
    Sets price_clean and currency for each.
    """
    normalized = []
    for p in products:
        price = clean_price(p.price_raw, p.currency)
        if price is not None and price > 0:
            p.price_clean = price
            p.currency = "INR"
            normalized.append(p)
        else:
            logger.debug(f"Filtered out: {p.product_name} — raw price: '{p.price_raw}'")

    return normalized


def format_inr(amount: float) -> str:
    """Format a float as Indian Rupee string with commas."""
    if amount >= 10_000_000:
        return f"₹{amount/10_000_000:.2f} Cr"
    elif amount >= 100_000:
        return f"₹{amount/100_000:.2f} L"
    else:
        # Indian comma format: 1,23,456
        s = f"{amount:,.2f}"
        # Convert to Indian format
        parts = s.split(".")
        integer_part = parts[0].replace(",", "")
        if len(integer_part) > 3:
            last3 = integer_part[-3:]
            remaining = integer_part[:-3]
            # Add commas every 2 digits from right
            formatted = ""
            for i, digit in enumerate(reversed(remaining)):
                if i > 0 and i % 2 == 0:
                    formatted = "," + formatted
                formatted = digit + formatted
            integer_part = formatted + "," + last3
        return f"₹{integer_part}.{parts[1]}"
