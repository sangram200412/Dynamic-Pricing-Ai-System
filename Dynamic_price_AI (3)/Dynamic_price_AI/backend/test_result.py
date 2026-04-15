import sys
import os
import asyncio
from PIL import Image
from dotenv import load_dotenv

# Add backend to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vision.identifier import identify_product

async def run_test():
    # Load env
    load_dotenv(".env")
    
    # Path to your test image
    image_path = r"C:\Users\Sangram Sethi\OneDrive\Desktop\Dynamic_price_AI\test pics\Electric stove.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ ERROR: Could not find image at {image_path}")
        return

    print(f"📷 Loading image: {os.path.basename(image_path)}")
    img = Image.open(image_path)
    
    print("📡 Sending to Gemini Vision API... (This may take 5-10 seconds)")
    result = await identify_product(img)
    
    print("\n" + "="*50)
    print("           AI VISION IDENTIFICATION RESULT")
    print("="*50)
    print(f"🔍 Product Name: {result.get('product_name')}")
    print(f"🏷️  Brand:        {result.get('brand')}")
    print(f"📁 Category:     {result.get('category')}")
    print(f"🚀 Search Query: {result.get('search_queries')[0] if result.get('search_queries') else 'N/A'}")
    print(f"🎯 Confidence:   {result.get('confidence') * 100}%")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_test())
