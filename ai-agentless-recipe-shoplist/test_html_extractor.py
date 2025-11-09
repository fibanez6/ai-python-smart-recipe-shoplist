import asyncio
import os
import sys
from pathlib import Path

import rich
from dotenv import load_dotenv

from app.config.logging_config import setup_logging
from app.scrapers.html_content_extractor import process_html_content

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

logger = setup_logging()

file_path = Path("/tmp/web_cache/content/e0a8c55dc46df2946b977d7b124a0c8b")
output_path = Path("/tmp/web_cache/content/output_cleaned.html")

def extractor_html(data):
    cleaned_html = process_html_content(data)
    rich.print("------------------- CLEANED HTML ------------------")
    rich.print(cleaned_html.get("data", "")[:500])

    return cleaned_html


if __name__ == "__main__":
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()

    rich.print("------------------- RAW HTML ------------------")
    rich.print(data[:500])
    cleaned_html = extractor_html(data)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(cleaned_html.get("data", "")))
