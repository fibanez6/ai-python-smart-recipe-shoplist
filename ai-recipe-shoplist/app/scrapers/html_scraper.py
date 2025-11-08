import logging
from functools import partial

from app.scrapers.html_content_processor import (
    process_html_content,
    process_html_content_with_selectors,
)
from app.services.web_fetcher import get_web_fetcher

from ..config.logging_config import get_logger, log_function_call
from ..config.pydantic_config import WEB_SCRAPER_SETTINGS
from ..manager.cache_manager import get_cache_manager
from ..manager.storage_manager import get_storage_manager

logger = get_logger(__name__)

class WebScraper:
    """Service for processing data with caching and error handling."""
    
    def __init__(self):
        self.name = "WebScraper"

        # Initialize cache manager and content storage
        self.cache_manager = get_cache_manager()
        self.content_storage = get_storage_manager()

        # Initialize web fetcher
        self.web_fetcher = get_web_fetcher()

    async def _fetch(self, url: str, data_format: str ) -> dict:
        """Fetch content from cache, disk, or web (in that order)."""

        log_function_call("WebScraper._fetch", {
            "url": url,
            "data_format": data_format
        })

        # Try loading from cache
        cached_data = self.cache_manager.load(url)
        if cached_data:
            logger.info(f"{self.name}: Loaded source data from cache for {url}")
            return cached_data

        # Try loading from disk
        disk_data = self.content_storage.load(url, format=data_format)
        if disk_data:
            logger.info(f"{self.name}: Loaded source data from disk for {url}")
            return disk_data

        # Fetch from web
        logger.info(f"{self.name}: Fetching data from web for {url}")
        web_data = await self.web_fetcher.fetch_url(url)

        # Debug: print keys if data is dict
        if logger.isEnabledFor(logging.DEBUG) and isinstance(web_data, dict):
            logger.debug(f"{self.name}: Web data keys: {list(web_data.keys())}")
            logger.debug(f"{self.name}: Web data preview: {web_data.get('data', '')[:200]}")

        if "data" in web_data:
            raw_data = web_data.get("data")

            self.cache_manager.save(url, raw_data, format=data_format)
            self.content_storage.save(url, raw_data, format=data_format)

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
            self.cache_manager.save(key=url, obj=processed_data.get("data"), alias="processed", format=processed_data.get("data_processed_format"))
            self.content_storage.save(key=url, obj=processed_data.get("data"), alias="processed", format=processed_data.get("data_processed_format"))

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
            # Try loading processed data from cache
            cached_data = self.cache_manager.load(key=url, alias="processed")
            if cached_data:
                logger.info(f"{self.name}: Loaded processed data from cache for {url}")
                return cached_data

            # Try loading processed data from disk
            disk_data = self.content_storage.load(key=url, alias="processed")
            if disk_data:
                logger.info(f"{self.name}: Loaded processed data from disk for {url}")
                return disk_data

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
            raise

# Global web scraper instance
_web_scraper_instance = None

def get_web_scraper() -> WebScraper:
    """Get or create the global web scraper instance."""
    global _web_scraper_instance
    if _web_scraper_instance is None:
        _web_scraper_instance = WebScraper()
    return _web_scraper_instance