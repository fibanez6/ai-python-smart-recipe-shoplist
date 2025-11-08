"""Web content fetcher service for downloading recipe pages and other web content."""

import time
from typing import Any

import httpx

from ..config.logging_config import get_logger, log_api_request, log_function_call
from ..config.pydantic_config import FETCHER_SETTINGS

logger = get_logger(__name__)

class WebFetcher:
    """Service for fetching web content with caching and error handling."""
    
    def __init__(self):
        self.name = "WebFetcher"
        self.timeout = FETCHER_SETTINGS.timeout
        self.user_agent = FETCHER_SETTINGS.user_agent

        logger.info(f"[{self.name}] initialized - Timeout: {self.timeout}s")
    
    async def fetch_url(self, url: str) -> dict[str, Any]:
        """
        Fetch content from a URL with optional caching and robust error handling.

        Args:
            url (str): The URL to fetch.

        Returns:
            dict[str, Any]: Dictionary with:
            - url (str): Final URL after redirects.
            - status_code (int): HTTP status code.
            - headers (dict): Response headers.
            - timestamp (float): Fetch timestamp.
            - size (int): Size of the content in bytes.
            - data (str): HTML content.
        """
        log_function_call("WebFetcher.fetch_url", {"url": url})
        
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

                content_length = len(response.text)

                duration = time.time() - start_time
                log_api_request("WebFetcher", url, content_length, duration, True)

                logger.info(
                    f"[{self.name}] Successfully fetched {url} - {content_length} bytes in {duration:.2f}s"
                )

                return {
                    "url": str(response.url),
                    "status_code": response.status_code,
                    # "headers": dict(response.headers),
                    "timestamp": time.time(),
                    "data_size": content_length,
                    "data_from": "web_fetcher",
                    "data": response.text,
                }

        except httpx.TimeoutException:
            self._log_fetch_error(url, start_time, "Timeout")
            raise
        except httpx.HTTPStatusError as e:
            self._log_fetch_error(url, start_time, f"HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            self._log_fetch_error(url, start_time, f"Error: {e}")
            raise

    def _log_fetch_error(self, url: str, start_time: float, error_msg: str) -> None:
        duration = time.time() - start_time
        log_api_request("WebFetcher", url, 0, duration, False)
        logger.error(f"[{self.name}] {error_msg} fetching {url} after {duration:.2f}s")

    
# Global fetcher instance
_fetcher_instance = None

def get_web_fetcher() -> WebFetcher:
    """Get or create the global web fetcher instance."""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = WebFetcher()
    return _fetcher_instance