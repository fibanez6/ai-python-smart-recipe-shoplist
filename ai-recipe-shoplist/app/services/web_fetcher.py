"""Web content fetcher service for downloading recipe pages and other web content."""

import time
from pathlib import Path
from typing import Any

import httpx

from ..config.logging_config import get_logger, log_api_request, log_function_call
from ..config.pydantic_config import FETCHER_SETTINGS
from ..utils.html_helpers import clean_html_for_ai
from .cache_manager import CacheManager
from .content_storage import ContentStorage

logger = get_logger(__name__)


class WebFetcher:
    """Service for fetching web content with caching and error handling."""
    
    def __init__(self):
        self.name = "WebFetcher"
        self.timeout = FETCHER_SETTINGS.timeout
        self.max_content_size = FETCHER_SETTINGS.max_size
        self.user_agent = FETCHER_SETTINGS.user_agent

        # Cache TTL configuration
        cache_ttl = FETCHER_SETTINGS.cache_ttl

        # Setup tmp folder for file-based caching
        self.tmp_folder = Path(FETCHER_SETTINGS.tmp_folder)

        # Initialize cache manager and content storage
        self.cache_manager = CacheManager(cache_ttl)
        self.content_storage = ContentStorage(self.tmp_folder)
        
        logger.info(f"[{self.name}] initialized - Timeout: {self.timeout}s, Max size: {self.max_content_size} bytes")
        logger.info(f"[{self.name}] tmp folder: {self.tmp_folder}")
    
    async def fetch_url(self, url: str, use_cache: bool = True) -> dict[str, Any]:
        """
        Fetch content from a URL with optional caching and robust error handling.

        Args:
            url (str): The URL to fetch.
            use_cache (bool): Whether to use cached content if available.

        Returns:
            dict[str, Any]: Dictionary with:
            - content (str): HTML content.
            - url (str): Final URL after redirects.
            - status_code (int): HTTP status code.
            - headers (dict): Response headers.
            - timestamp (float): Fetch timestamp.
            - from_cache (bool): True if served from in-memory cache.
            - from_file_cache (bool): True if served from file cache.
            - size (int): Size of the content in bytes.
        """
        log_function_call("WebFetcher.fetch_url", {"url": url, "use_cache": use_cache})
        
        # Check cache using cache manager
        cached_result = self.cache_manager.get_cached_content(url, use_cache)
        if cached_result:
            return cached_result
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": self.user_agent}
            ) as client:

                logger.info(f"[{self.name}] Fetching URL: {url}")
                response = await client.get(url)
                response.raise_for_status()
                
                # Check content size
                content_length = len(response.content)
                if content_length > self.max_content_size:
                    raise ValueError(f"[{self.name}] Content too large: {content_length} bytes (max: {self.max_content_size})")
                
                duration = time.time() - start_time
                
                # Log successful request
                log_api_request("WebFetcher", url, content_length, duration, True)
                
                result = {
                    "content": response.text,
                    "url": str(response.url),  # Final URL after redirects
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "timestamp": time.time(),
                    "from_cache": False,
                    "size": content_length
                }
                
                # Cache the result using cache manager
                self.cache_manager.save_fetch_content(url, result, use_cache)
                
                logger.info(f"[{self.name}] Successfully fetched {url} - {content_length} bytes in {duration:.2f}s")
                return result
              
        except httpx.TimeoutException:
            duration = time.time() - start_time
            log_api_request("WebFetcher", url, 0, duration, False)
            logger.error(f"[{self.name}] Timeout fetching {url} after {duration:.2f}s")
            raise
        except httpx.HTTPStatusError as e:
            duration = time.time() - start_time
            log_api_request("WebFetcher", url, 0, duration, False)
            logger.error(f"[{self.name}] HTTP error fetching {url}: {e.response.status_code}")
            raise
        except Exception as e:
            duration = time.time() - start_time
            log_api_request("WebFetcher", url, 0, duration, False)
            logger.error(f"[{self.name}] Error fetching {url}: {e}")
            raise

    async def fetch_html_content(self, url: str, html_selectors: dict[str, str] = {}, clean_html: bool = True, use_cache: bool = True) -> dict[str, Any]:
        """
        Fetch HTML content from a URL, optionally clean it, and apply HTML selectors.

        Args:
            url (str): The URL to fetch HTML content from.
            html_selectors (dict[str, str], optional): CSS selectors for extracting specific HTML parts.
            clean_html (bool): Whether to clean the HTML content for AI use.
            use_cache (bool): Whether to use cached content if available.

        Returns:
            dict[str, Any]: Dictionary with:
            - content (str): Raw HTML content.
            - cleaned_content (str, optional): Cleaned HTML content if requested.
            - saved_files (dict, optional): Paths to saved files if content was saved.
        """

        log_function_call("WebFetcher.fetch_html_content", {
            "url": url,
            "html_selectors": html_selectors,
            "clean_html": clean_html,
            "use_cache": use_cache
        })
        
        # Load from storage
        content = self.content_storage.load_html_content(url)
        if content:
            logger.info(f"[{self.name}] Using content from disk for {url}")
        
        # Fetch from web if not loaded from disk
        if "content" not in content:
            content = await self.fetch_url(url, use_cache)

        # Clean HTML if requested
        if clean_html and "cleaned_content" not in content:
            content["cleaned_content"] = clean_html_for_ai(content["content"], html_selectors)
            logger.debug(f"[{self.name}] Generated cleaned HTML content: {len(content['content'])} -> {len(content['cleaned_content'])} chars")

        # Save content to storage and cache
        self.cache_manager.save_fetch_content(url, content, use_cache)
        saved_files = self.content_storage.save_fetch_content(url, content)
        if saved_files:
            content["saved_files"] = saved_files

        return content

# Global fetcher instance
_fetcher_instance = None

def get_web_fetcher() -> WebFetcher:
    """Get or create the global web fetcher instance."""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = WebFetcher()
    return _fetcher_instance