from functools import partial
import logging

from app.services.web_fetcher import get_web_fetcher

from ..config.logging_config import get_logger, log_function_call
from ..config.pydantic_config import WEB_DATA_SERVICE_SETTINGS
from ..manager.cache_manager import get_cache_manager
from ..manager.storage_manager import get_storage_manager
from ..utils.html_helpers import clean_html_for_ai

logger = get_logger(__name__)


class WebDataService:
    """Service for processing data with caching and error handling."""
    
    def __init__(self):
        self.name = "WebDataService"

        # Initialize cache manager and content storage
        self.cache_manager = get_cache_manager()
        self.content_storage = get_storage_manager(WEB_DATA_SERVICE_SETTINGS.storage_path)

        # Initialize web fetcher
        self.web_fetcher = get_web_fetcher()

    async def _fetch(self, url: str, data_format: str ) -> dict:
        """Fetch content from cache, disk, or web (in that order)."""
        # Try loading from cache
        cached_data = self.cache_manager.load(url)
        if cached_data:
            logger.info(f"{self.name}: Loaded data from cache for {url}")
            return cached_data

        # Try loading from disk
        disk_data = self.content_storage.load(url)
        if disk_data:
            logger.info(f"{self.name}: Loaded data from disk for {url}")
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

    async def _process(self, url: str, raw_data: dict, extractor) -> dict:
        """Process raw data using the provided extractor function."""
        # Process the raw data
        logger.info(f"{self.name}: Extracting relevant info for {url}")
        processed_data = extractor(raw_data)

        if "data" not in processed_data:
            logger.warning(f"{self.name}: Failed to extract data")
            raise ValueError("Data extraction failed, no 'data' key in processed data")

        # Save processed data to cache and disk
        if processed_data:
            self.cache_manager.save(url, processed_data.get("data"), alias="processed", format=processed_data.get("data_processed_format"))
            self.content_storage.save(url, processed_data.get("data"), alias="processed", format=processed_data.get("data_processed_format"))

        processed_data["data_processed"] = True
        return processed_data

    # def _extract_relevant_info(self, data: dict) -> dict:
    #     """Extract relevant information from raw data."""
    #     format_type = data.get("format")
    #     raw_content = data.get("data", "")

    #     if format_type == "html":
    #         logger.info(f"{self.name}: Processing HTML content for AI consumption")
    #         processed_content = clean_html_for_ai(raw_content)
    #     elif format_type == "json":
    #         logger.info(f"{self.name}: Processing JSON content for AI consumption")
    #         processed_content = raw_content
    #         # TODO
    #         # Optionally process JSON further here
    #     else:
    #         logger.warning(f"{self.name}: Unknown data format for processing: {format_type}")
    #         processed_content = raw_content

    #     return {**data, "data": processed_content}

    async def fetch_and_process(self, url: str, extractor, data_format: str ="html") -> dict:
        """Fetch and process web data with caching."""
        log_function_call("WebDataService.fetch_and_process", {"url": url})
        try:
            # Try loading processed data from cache
            cached_data = self.cache_manager.load(url, alias="processed")
            if cached_data:
                logger.info(f"{self.name}: Loaded processed data from cache for {url}")
                return cached_data

            # Try loading processed data from disk
            disk_data = self.content_storage.load(url, alias="processed")
            if disk_data:
                logger.info(f"{self.name}: Loaded processed data from disk for {url}")
                return disk_data

            fetch_data = await self._fetch(url, data_format)
            if "data" not in fetch_data:
                logger.warning(f"{self.name}: No raw data fetched for {url}")
                return None

            # Process the fetched data
            raw_data = fetch_data.get("data")
            processed_data = await self._process(url, raw_data, extractor)

            # Merge processed data into fetch data
            fetch_data.update(processed_data)

            return fetch_data
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching or processing data for {url}: {e}")
            raise

# Global web data service instance
_web_data_service_instance = None

def get_web_data_service() -> WebDataService:
    """Get or create the global web data service instance."""
    global _web_data_service_instance
    if _web_data_service_instance is None:
        _web_data_service_instance = WebDataService()
    return _web_data_service_instance