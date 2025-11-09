import logging
import traceback
from functools import partial

from app.config.logging_config import get_logger, log_function_call
from app.config.store_config import StoreConfig
from app.services.web_fetcher import get_web_fetcher
from app.storage.storage_manager import get_storage_manager

from .html_content_extractor import (
    process_html_content,
    process_html_content_with_selectors,
)

logger = get_logger(__name__)

class HTMLScraper:
    """Service for processing data with caching and error handling."""
    
    def __init__(self):
        self.name = "HTMLScraper"

        # Initialize cache manager and content storage
        self.content_storage = get_storage_manager()

        # Initialize web fetcher
        self.web_fetcher = get_web_fetcher()

    async def _fetch(self, url: str, data_format: str ) -> dict:
        """Fetch content from cache, disk, or web (in that order)."""

        log_function_call("HTMLScraper._fetch", {
            "url": url,
            "data_format": data_format
        })

        # Try loading from cache or disk storage
        loaded_data = await self.content_storage.load_fetch(url)
        if loaded_data:
            logger.info(f"{self.name}: Loaded source data from content storage for {url}")
            return loaded_data

        # Fetch from web
        logger.info(f"{self.name}: Fetching data from web for {url}")
        web_data = await self.web_fetcher.fetch_url(url)

        # Debug: print keys if data is dict
        if logger.isEnabledFor(logging.DEBUG) and isinstance(web_data, dict):
            logger.debug(f"{self.name}: Web data keys: {list(web_data.keys())}")
            logger.debug(f"{self.name}: Web data preview: {web_data.get('data', '')[:200]}")

        if "data" in web_data:
            raw_data = web_data.get("data")
            await self.content_storage.save_fetch(url, raw_data, format=data_format)

        web_data["data_format"] = data_format
        return web_data

    async def _process(self, url: str, raw_data: dict, html_processor) -> dict:
        """Process raw data using the provided html_processor function."""
        # Process the raw data
        logger.info(f"{self.name}: Extracting relevant info for {url}")
        processed_data = html_processor(raw_data)

        if "data" not in processed_data:
            logger.warning(f"{self.name}: Failed to extract data")
            raise ValueError("Data extraction failed, no 'data' key in processed data")

        # Save processed data to cache and disk
        if processed_data:
            await self.content_storage.save_fetch(url, processed_data.get("data"), format=processed_data.get("data_processed_format"))

        processed_data["data_processed"] = True
        return processed_data

    def _get_html_processor(self, html_selectors: dict[str, str] = None, data_format: str = "html") -> callable:
        """Get the appropriate HTML processor function."""
        if html_selectors and data_format == "html":
            return partial(process_html_content_with_selectors, selectors=html_selectors)
        return process_html_content

    async def fetch_and_process(self, url: str, html_selectors: dict[str, str] = None, data_format: str ="html") -> dict:
        """Fetch and process web data with caching."""
        log_function_call("WebDataService.fetch_and_process", {
            "url": url,
            "data_format": data_format
        })
        try:
            # Check if processed data is already available    
            loaded_processed_data = await self.content_storage.load_fetch(key=url, alias="processed")
            if loaded_processed_data:
                logger.info(f"{self.name}: Loaded processed data from content storage for {url}")
                return loaded_processed_data

            fetched_data = await self._fetch(url, data_format)
            if "data" not in fetched_data:
                logger.warning(f"{self.name}: No raw data fetched for {url}")
                return None

            # Process the fetched data
            html_processor = self._get_html_processor(html_selectors, data_format=data_format)
            raw_data = fetched_data.get("data")
            processed_data = await self._process(url, raw_data, html_processor)

            # Merge processed data into fetch data
            fetched_data.update(processed_data)

            return fetched_data
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching or processing data for {url}: {e}")
            logger.error(f"[{self.name}] Full stack trace: {traceback.format_exc()}")
            raise

    async def query_products(self, product_name: str, store_config: StoreConfig) -> dict:
        """Query products from HTML store."""

        url = store_config.get_search_url(product_name)

        logger.info(f"{self.name}: Scraping URL: {url}")
        return await self.fetch_and_process(url, store_config.html_selectors, store_config.search_type)

# Global web scraper instance
_html_scraper_instance = None

def get_html_scraper() -> HTMLScraper:
    """Get or create the global HTML scraper instance."""
    global _html_scraper_instance
    if _html_scraper_instance is None:
        _html_scraper_instance = HTMLScraper()
    return _html_scraper_instance