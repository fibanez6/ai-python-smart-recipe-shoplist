"""Cache management for web content with both memory and file-based caching."""


import time
from typing import Any

from cachetools import TTLCache

from ..config.logging_config import get_logger
from ..config.pydantic_config import CACHE_SETTINGS

logger = get_logger(__name__)

FROM_CACHE = "from_cache"
TIMESTAMP = "timestamp"

class CacheManager:
    """Manages caching for web content using (in-memory TTL cache) only."""

    def __init__(self, ttl: int = CACHE_SETTINGS.ttl):
        self.name = "CacheManager"
        self.enabled = CACHE_SETTINGS.enabled
        self.ttl = ttl
        self.max_size = CACHE_SETTINGS.max_size
        self.cache = TTLCache(maxsize=self.max_size, ttl=self.ttl)

        logger.info(f"[{self.name}] Using TTLCache (maxsize={self.max_size}, ttl={self.ttl}s)")

    def get_from_memory_cache(self, url: str) -> dict[str, Any] | None:
        """
        Get content from in-memory cache if available and not expired.
        """
        if not self.enabled:
            return None

        try:
            cache_entry = self.cache[url]
            logger.info(f"[{self.name}] Serving cached content from for {url}")
            cache_entry[FROM_CACHE] = True
            return cache_entry
        except KeyError:
            return None
    
    def save_to_memory_cache(self, url: str, data: dict[str, Any]) -> None:
        """
        Save content to in-memory cache.
        """
        if not self.enabled:
            return

        cache_data = data.copy()
        cache_data[TIMESTAMP] = time.time()
        self.cache[url] = cache_data
        logger.debug(f"[{self.name}] Saved content to for {url}")
    
    
    def get_cached_content(self, url: str, use_cache: bool = True) -> dict[str, Any] | None:
        """
        Get cached content from in-memory cache.
        """
        if not use_cache or not self.enabled:
            return None
        return self.get_from_memory_cache(url)
    
    def save_fetch_content(self, url: str, data: dict[str, Any], use_cache: bool = True) -> None:
        """
        Save content to in-memory cache.
        """
        if not use_cache or not self.enabled:
            return
        self.save_to_memory_cache(url, data)
        content_length = data.get("size", 0)
        logger.debug(f"[{self.name}] Cached content for {url} ({content_length} bytes)")
    
    def clear_cache(self, clear_file_cache: bool = True) -> dict[str, int]:
        """
        Clear all in-memory cache entries.
        """
        if not self.enabled:
            return {"cachetools_cleared": 0}

        cleared = len(self.cache)
        self.cache.clear()
        logger.info(f"[{self.name}] Cleared all cache entries.")
        return {"cachetools_cleared": cleared}
    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics (only)."""

        if not self.enabled:
            return {
                "enabled": False,
                "entries": 0,
                "keys": [],
                "ttl_seconds": self.ttl,
                "max_size": self.max_size
            }
        
        return {
            "enabled": True,
            "entries": len(self.cache),
            "keys": list(self.cache.keys()),
            "ttl_seconds": self.ttl,
            "max_size": self.max_size
        }