import asyncio
import os
import sys

import rich
from dotenv import load_dotenv

from app.config.logging_config import setup_logging
from app.services.web_fetcher import get_web_fetcher

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

url="https://www.coles.com.au/_next/data/20251104.2-4b13023beb9ac0c329ed0a47c852cc8335126b51/en/search/products.json?q=tomato"


load_dotenv()

logger = setup_logging()

web_fetcher = get_web_fetcher()

async def fetch_page():
    rich.print(f"Fetching URL: {url}")
    page_content = await web_fetcher.fetch_url(url)
    rich.print("------------------- PAGE CONTENT ------------------")
    rich.print(page_content)    


if __name__ == "__main__":
    asyncio.run(fetch_page())
    