"""Web content fetcher service for downloading recipe pages and other web content.

Environment Variables:
    FETCHER_TIMEOUT: Request timeout in seconds (default: 30)
    FETCHER_MAX_SIZE: Maximum content size in bytes (default: 10485760)
    FETCHER_USER_AGENT: User agent string for requests
    FETCHER_CACHE_TTL: Cache TTL in seconds (default: 3600)
    FETCHER_TMP_FOLDER: Temporary folder for caching (default: tmp/web_cache)
    FETCHER_ENABLE_CONTENT_SAVING: Enable saving content to disk (default: false)
    FETCHER_ENABLE_CONTENT_LOADING: Enable loading content from disk (default: false)
"""

import time
from pathlib import Path
from typing import Any, Dict

import httpx

from ..config.pydantic_config import (
    FETCHER_TIMEOUT,
    FETCHER_MAX_SIZE,
    FETCHER_USER_AGENT,
    FETCHER_CACHE_TTL,
    FETCHER_TMP_FOLDER,
    FETCHER_ENABLE_CONTENT_SAVING,
    FETCHER_ENABLE_CONTENT_LOADING,
)
from ..config.logging_config import get_logger, log_api_request, log_function_call
from .cache_manager import CacheManager
from .content_storage import ContentStorage
from ..utils.html_helpers import clean_html_for_ai

logger = get_logger(__name__)


class WebFetcher:
    """Service for fetching web content with caching and error handling."""
    
    def __init__(self):
        self.timeout = FETCHER_TIMEOUT
        self.max_content_size = FETCHER_MAX_SIZE
        self.user_agent = FETCHER_USER_AGENT
        
        # Cache TTL configuration
        cache_ttl = FETCHER_CACHE_TTL
        cache_max_size = FETCHER_MAX_SIZE
        
        # Content saving/loading configuration
        enable_content_saving = FETCHER_ENABLE_CONTENT_SAVING
        enable_content_loading = FETCHER_ENABLE_CONTENT_LOADING
        
        # Setup tmp folder for file-based caching
        self.tmp_folder = Path(FETCHER_TMP_FOLDER)
        self.tmp_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache manager and content storage
        self.cache_manager = CacheManager(cache_ttl, cache_max_size)
        self.content_storage = ContentStorage(self.tmp_folder, enable_content_saving, enable_content_loading)
        
        # Keep references for backward compatibility
        self.enable_content_saving = enable_content_saving
        self.enable_content_loading = enable_content_loading
        
        logger.info(f"WebFetcher initialized - Timeout: {self.timeout}s, Max size: {self.max_content_size} bytes")
        logger.info(f"WebFetcher tmp folder: {self.tmp_folder}")
        logger.info(f"WebFetcher content saving: {self.enable_content_saving}, loading: {self.enable_content_loading}")
    
    async def fetch_url(self, url: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Fetch content from a URL with caching and error handling.
        
        Args:
            url: URL to fetch
            use_cache: Whether to use cached content if available
            
        Returns:
            Dict containing:
                - content: HTML content
                - url: Final URL (after redirects)
                - status_code: HTTP status code
                - headers: Response headers
                - from_cache: Whether content was served from cache
                - from_file_cache: Whether content was served from file cache
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

                logger.info(f"[WebFetcher] Fetching URL: {url}")
                response = await client.get(url)
                response.raise_for_status()
                
                # Check content size
                content_length = len(response.content)
                if content_length > self.max_content_size:
                    raise ValueError(f"[WebFetcher] Content too large: {content_length} bytes (max: {self.max_content_size})")
                
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
                    "from_file_cache": False,
                    "size": content_length
                }
                
                # Cache the result using cache manager
                self.cache_manager.save_content(url, result, use_cache)
                
                logger.info(f"[WebFetcher] Successfully fetched {url} - {content_length} bytes in {duration:.2f}s")
                return result
              
        except httpx.TimeoutException:
            duration = time.time() - start_time
            log_api_request("WebFetcher", url, 0, duration, False)
            logger.error(f"[WebFetcher] Timeout fetching {url} after {duration:.2f}s")
            raise
        except httpx.HTTPStatusError as e:
            duration = time.time() - start_time
            log_api_request("WebFetcher", url, 0, duration, False)
            logger.error(f"[WebFetcher] HTTP error fetching {url}: {e.response.status_code}")
            raise
        except Exception as e:
            duration = time.time() - start_time
            log_api_request("WebFetcher", url, 0, duration, False)
            logger.error(f"[WebFetcher] Error fetching {url}: {e}")
            raise
    
    async def fetch_recipe_content(self, url: str, clean_html: bool = True, save_to_disk: bool = None) -> Dict[str, Any]:
        """
        Fetch and optionally clean HTML content for recipe processing.
        
        Args:
            url: Recipe URL to fetch
            clean_html: Whether to clean HTML content for AI processing
            save_to_disk: Whether to save original and cleaned content to disk files 
                         (None = use global config, True/False = override)
            
        Returns:
            Dict containing fetched content and metadata
        """
        # Determine if we should save to disk (parameter overrides global config)
        should_save_to_disk = save_to_disk if save_to_disk is not None else self.enable_content_saving
        should_load_from_disk = self.enable_content_loading and should_save_to_disk
        
        log_function_call("WebFetcher.fetch_recipe_content", {
            "url": url, 
            "clean_html": clean_html, 
            "save_to_disk": should_save_to_disk,
            "load_from_disk": should_load_from_disk
        })
        
        result = await self.fetch_url(url)
        
        cleaned_content = None
        loaded_from_disk = False
        
        if clean_html:
            # First, try to load cleaned content from disk if available and enabled
            if should_load_from_disk:
                disk_content = self.content_storage.load_content(url)
                if "cleaned_content" in disk_content:
                    cleaned_content = disk_content["cleaned_content"]
                    loaded_from_disk = True
                    logger.info(f"[WebFetcher] Using cleaned content from disk for {url}")
            
            # If not found on disk or loading disabled, generate cleaned content
            if cleaned_content is None:
                cleaned_content = clean_html_for_ai(result["content"])
                logger.debug(f"[WebFetcher] Generated cleaned HTML content: {len(result['content'])} -> {len(cleaned_content)} chars")
            
            result["cleaned_content"] = cleaned_content
            result["cleaned_from_disk"] = loaded_from_disk
        
        # Save both original and cleaned content to disk if enabled
        if should_save_to_disk:
            # Update content storage config if needed (for parameter override)
            if save_to_disk is not None:
                self.content_storage.update_config(enable_saving=should_save_to_disk)
            
            saved_files = self.content_storage.save_content(url, result["content"], cleaned_content)
            if saved_files:
                result["saved_files"] = saved_files
                if not loaded_from_disk:
                    logger.info(f"[WebFetcher] Saved content to disk for {url}")
                else:
                    logger.info(f"[WebFetcher] Content files updated for {url}")
        else:
            logger.debug(f"[WebFetcher] Content saving disabled for {url}")

        return result
    
    def clear_cache(self, clear_file_cache: bool = True, clear_content_files: bool = False) -> None:
        """
        Clear the content cache.
        
        Args:
            clear_file_cache: Whether to also clear the file cache
            clear_content_files: Whether to also clear saved content files
        """
        # Clear cache using cache manager
        cache_stats = self.cache_manager.clear_cache(clear_file_cache)
        
        content_files_count = 0
        if clear_content_files:
            content_files_count = self.content_storage.clear_content_files()
        
        log_msg = f"[WebFetcher] Cleared fetcher cache (memory: {cache_stats['memory_entries']}, files: {cache_stats['file_entries']}"
        if clear_content_files:
            log_msg += f", content files: {content_files_count}"
        log_msg += ")"
        logger.info(log_msg)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_stats = self.cache_manager.get_cache_stats()
        content_stats = self.content_storage.get_content_stats()
        
        return {
            "memory_cache": cache_stats["memory_cache"],
            "file_cache": cache_stats["file_cache"],
            "content_files": content_stats,
            "ttl_seconds": cache_stats["ttl_seconds"]
        }


# Global fetcher instance
_fetcher_instance = None

def get_web_fetcher() -> WebFetcher:
    """Get or create the global web fetcher instance."""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = WebFetcher()
    return _fetcher_instance