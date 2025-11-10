"""Persistent storage layer for AI Recipe Shoplist Crawler."""

from pathlib import Path
import traceback
from typing import Any, Optional

from app.config.pydantic_config import BLOB_SETTINGS
from app.models import ChatCompletionResult

from ..config.logging_config import get_logger, log_function_call
from ..storage.blob_manager import BlobManager, get_blob_manager
from ..storage.cache_manager import get_cache_manager
from ..config.pydantic_config import (
    BLOB_SETTINGS,
    CACHE_SETTINGS,
)

logger = get_logger(__name__)

class StorageManager:
    """Manager for persistent storage of data."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.name = "StorageManager"

        self.cache_manager = get_cache_manager()
        self.ai_cache_manager = get_cache_manager(ttl=CACHE_SETTINGS.ai_ttl)

        self.blob_storage = get_blob_manager()
        self.ai_blob_storage = BlobManager(BLOB_SETTINGS.base_path / "ai_cache")

        self.storage_api_path = BlobManager(BLOB_SETTINGS.base_path / "api_cache")


    async def save_fetch(self, key: str, data: Any, **kwargs) -> None:
        """Save fetched content to cache and blob storage."""

        alias = kwargs.get('alias', "html")
        format = kwargs.get('format', "html")

        log_function_call("StorageManager.save_fetch", {
            "storage_key": key,
            "alias": alias,
            "format": format,
            "content_preview": str(data)[:20] + ("..." if len(data) > 20 else "")
        })

        if data:
            self.cache_manager.save(key, data, format=format, alias=alias)
            await self.blob_storage.save(key, data, format=format, alias=alias)

    async def load_fetch(self, key: str, **kwargs) -> str:
        """Load fetched content from cache or blob storage."""
        
        alias = kwargs.get('alias', None)
        format = kwargs.get('format', None)

        log_function_call("StorageManager.load_fetch", {
            "storage_key": key,
            "alias": alias,
            "format": format
        })

        alias = kwargs.get('alias', None)
        format = kwargs.get('format', None)

        # Try loading from cache
        cached_data = self.cache_manager.load(key=key, alias=alias)
        if cached_data:
            logger.info(f"[{self.name}] Loaded data from cache for {key}")
            return cached_data

        # Try loading from blob storage
        blob_data = await self.blob_storage.load(key=key, alias=alias, format=format)
        if blob_data:
            logger.info(f"[{self.name}] Loaded data from blob storage for {key}")
            return blob_data

        logger.info(f"[{self.name}] No data found in cache or blob storage for {key}")
        return None
    
    async def save_ai_response(self, key: str, data: dict, **kwargs) -> None:
        """Save AI response to cache and blob storage."""

        alias = kwargs.get('alias', "json")
        format = kwargs.get('format', "json")

        log_function_call("StorageManager.save_ai_response", {
            "key": key,
            "alias": alias,
            "format": format,
            "data_preview": str(data)[:50] + ("..." if len(str(data)) > 50 else "")
        })

        if data:
            self.ai_cache_manager.save(key=key, obj=data, alias=alias)
            await self.ai_blob_storage.save(key=key, obj=data, alias=alias, format=format)

    async def load_ai_response(self, key: str, **kwargs) -> dict | None:
        """Load AI response from cache or blob storage."""

        alias = kwargs.get('alias', None)
        model_class = kwargs.get('model_class', None)

        log_function_call("StorageManager.load_ai_response", {
            "storage_key": key,
            "alias": alias,
            "model_class": model_class.__name__ if model_class else None
        })
        
        # Try cache first
        cached_data = self.ai_cache_manager.load(key=key, alias=alias)
        if cached_data:
            logger.info(f"[{self.name}] Loaded AI response from AI cache for model_class: {model_class}")
            return self._build_chat_result(cached_data, model_class=None)  # Set None to avoid double parsing

        # Try blob storage if cache miss
        disk_data = await self.ai_blob_storage.load(key=key, alias=alias, model_class=ChatCompletionResult)
        if disk_data:
            logger.info(f"[{self.name}] Loaded AI response from AI blob storage for model_class: {model_class}")
            return self._build_chat_result(disk_data, model_class)

        return None

    def _build_chat_result(self, data: ChatCompletionResult, model_class: type = None) -> ChatCompletionResult:
        """Build ChatCompletionResult from cached/stored data."""

        log_function_call("StorageManager._build_chat_result", {
            "data_keys": list(data.keys()),
            "model_class": model_class.__name__ if model_class else None
        })

        try:
            logger.debug(f"[{self.name}] _build_chat_result: {data}")

            data_from = data["data_from"]
            chat_result: ChatCompletionResult = data["data"]
            
            content = chat_result.content
            if model_class:
                content = model_class(**content)
                
            return chat_result.model_copy(update={
                "content": content,
                "metadata": {"data_from": data_from}
            })
        except Exception as e:
            logger.error(f"[{self.name}] Error building chat result: {e}")
            logger.error(f"[{self.name}] Full stack trace: {traceback.format_exc()}")
            return None

    async def save_api_response(self, key: str, data: dict, **kwargs) -> None:
        """Store API response in cache and blob storage."""
        alias = kwargs.get('alias', "json")
        format = kwargs.get('format', "json")

        log_function_call("StorageManager.store_api_response", {
            "storage_key": key,
            "alias": alias,
            "format": format,
            "data_preview": str(data)[:50] + ("..." if len(str(data)) > 50 else "")
        })

        if data:
            self.cache_manager.save(key, data, format=format, alias=alias)
            await self.storage_api_path.save(key, data, format=format, alias=alias)

    def clear_storage(self) -> None:
        """Clear all data from cache and blob storage."""
        log_function_call("StorageManager.clear_storage", {})
        self.cache_manager.clear()
        self.blob_storage.clear()

 # Global storage instance
_storage_instance = None

def get_storage_manager() -> StorageManager:
    """Get or create the global content storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageManager()
    return _storage_instance