"""Cache management for web content with both memory and file-based caching."""

import hashlib
import time
from typing import Any, Optional

from cachetools import TTLCache

from ..config.logging_config import get_logger, log_function_call
from ..config.pydantic_config import CACHE_SETTINGS

logger = get_logger(__name__)

LOADED_FROM_CACHE = {"data_from": "Local_cache"}

#  Original / source content
SOURCE_ALIAS="source"
PROCESSED_ALIAS = "processed"

class CacheManager:
    """Manages caching for web content using (in-memory TTL cache) only."""

    def __init__(self, ttl: int = CACHE_SETTINGS.ttl):
        self.name = "CacheManager"
        self.enabled = CACHE_SETTINGS.enabled
        self.ttl = ttl
        self.max_size = CACHE_SETTINGS.max_size
        self.cache = TTLCache(maxsize=self.max_size, ttl=self.ttl)

        logger.info(f"[{self.name}] Using TTLCache (maxsize={self.max_size}, ttl={self.ttl}s)")

    def _get_url_hash(self, url: str, alias: str) -> str:
        """Generate a hash for the URL to use as filename base."""
        return hashlib.md5(f"{alias}:{url}".encode()).hexdigest()

    def save(self, url: str, data: any, alias: str = SOURCE_ALIAS, format: str = "txt") -> dict:
        """
        Save content to in-memory cache.
        """
        if not self.enabled:
            return {}
        
        log_function_call("CacheManager.save", {
            "url": url,
            "alias": alias,
            "data_preview": str(data)[:20] + "...",
            "format": format
        })

        url_hash = self._get_url_hash(url, alias)
        cache_entry = {
            "url": url,
            "alias": alias,
            "hash": url_hash,
            "timestamp": time.time(),
            "data_size": len(data),
            "data_format": format,
            "data": data
        }

        self.cache[url_hash] = cache_entry

        logger.debug(f"[{self.name}] Saved data to cache for {url} and alias '{alias}'")

        return cache_entry
    
    def load(self, url: str, alias: str = SOURCE_ALIAS) -> Optional[dict]:
        """
        Retrieve content from in-memory cache if available and not expired.
        """
        if not self.enabled:
            return None

        log_function_call("CacheManager.load", {
            "url": url,
            "alias": alias
        })

        url_hash = self._get_url_hash(url, alias)

        cache_entry = self.cache.get(url_hash)
        if cache_entry is not None:
            cache_entry.update(LOADED_FROM_CACHE)
            logger.info(f"[{self.name}] Serving cached data for {url} (alias='{alias}')")
            return cache_entry

        return None
    
    def clear(self) -> dict[str, int]:
        """
        Clear all in-memory cache entries.
        """
        if not self.enabled:
            return {"cachetools_cleared": 0}

        cleared = len(self.cache)
        self.cache.clear()
        logger.info(f"[{self.name}] Cleared all cache entries.")
        return {"cachetools_cleared": cleared}

    def get_stats(self) -> dict[str, Any]:
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

# Global cache instance
_cache_instance = None

def get_cache_manager(ttl: Optional[int] = None) -> CacheManager:
    """Get or create the global cache manager instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(ttl=ttl) if ttl is not None else CacheManager()
    return _cache_instance
