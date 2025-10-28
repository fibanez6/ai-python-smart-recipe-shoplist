"""Cache management for web content with both memory and file-based caching."""


import time
from pathlib import Path
from typing import Any, Dict
from cachetools import TTLCache
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages caching for web content using (in-memory TTL cache) only."""

    def __init__(self, cache_ttl: int = 3600, max_cache_size: int = 1024):
        self.cache_ttl = cache_ttl
        self.cache = TTLCache(maxsize=max_cache_size, ttl=cache_ttl)
        logger.info(f"[CacheManager] Using TTLCache (maxsize={max_cache_size}, ttl={cache_ttl}s)")
    
    def get_from_memory_cache(self, url: str) -> Dict[str, Any] | None:
        """
        Get content from in-memory cache if available and not expired.
        """
        try:
            cache_entry = self.cache[url]
            logger.info(f"[CacheManager] Serving cached content from for {url}")
            cache_entry["from_cache"] = True
            cache_entry["from_file_cache"] = False
            return cache_entry
        except KeyError:
            return None
    
    def save_to_memory_cache(self, url: str, data: Dict[str, Any]) -> None:
        """
        Save content to in-memory cache.
        """
        cache_data = data.copy()
        cache_data["timestamp"] = time.time()
        self.cache[url] = cache_data
        logger.debug(f"[CacheManager] Saved content to for {url}")
    
    
    def get_cached_content(self, url: str, use_cache: bool = True) -> Dict[str, Any] | None:
        """
        Get cached content from in-memory cache.
        """
        if not use_cache:
            return None
        return self.get_from_memory_cache(url)
    
    def save_content(self, url: str, data: Dict[str, Any], use_cache: bool = True) -> None:
        """
        Save content to in-memory cache.
        """
        if not use_cache:
            return
        self.save_to_memory_cache(url, data)
        content_length = data.get("size", 0)
        logger.debug(f"[CacheManager] Cached content for {url} ({content_length} bytes)")
    
    def clear_cache(self, clear_file_cache: bool = True) -> Dict[str, int]:
        """
        Clear all in-memory cache entries.
        """
        cleared = len(self.cache)
        self.cache.clear()
        logger.info(f"[CacheManager] Cleared all cache entries.")
        return {"cachetools_cleared": cleared}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (only)."""
        return {
            "entries": len(self.cache),
            "keys": list(self.cache.keys()),
            "ttl_seconds": self.cache_ttl
        }