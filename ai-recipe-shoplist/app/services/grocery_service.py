"""Store crawler with configurable store support."""

from typing import Optional

from ..config.logging_config import get_logger, log_function_call
from ..config.store_config import (
    DEFAULT_REGION,
    StoreConfig,
    StoreRegion,
    get_active_stores,
    get_store_config,
    validate_store_id,
)

logger = get_logger(__name__)


class GroceryService:
    """Store crawler with configurable store support."""
    
    def __init__(self, region: StoreRegion = DEFAULT_REGION):
        """Initialize crawler with specified region."""
        self.region = region
        self.stores = get_active_stores(region)
        logger.info(f"StoreCrawler initialized for region {region.value} with stores: {self.stores}")
    
    def set_region(self, region: StoreRegion) -> None:
        """Change the active region and update available stores."""
        self.region = region
        self.stores = get_active_stores(region)
        logger.info(f"StoreCrawler region changed to {region.value}, stores: {self.stores}")
    
    def get_store_config(self, store_id: str):
        """Get configuration for a specific store."""
        return get_store_config(store_id)
    
    def get_stores(self, store_names: list[str] = None) -> list[StoreConfig]:
        """Return a list of (store_name, config) pairs for the requested or all stores."""
        log_function_call("GroceryService.get_stores", { "store_names": store_names })

        # Validate and filter store names
        if store_names:
            active_stores = []
            for store_name in store_names:
                if validate_store_id(store_name) and store_name in self.stores:
                    active_stores.append(store_name)
                else:
                    logger.warning(f"Invalid or unavailable store: {store_name}")
        else:
            active_stores = self.stores

        if not active_stores:
            logger.error("No valid stores available for search")
            return []

        logger.info(f"Found Stores: {active_stores}")
        # Return list of (store_name, config) pairs
        return [get_store_config(store_name) for store_name in active_stores]
    
    def get_available_stores(self) -> list[str]:
        """Get list of available stores for current region."""
        return self.stores.copy()
    
    def get_store_info(self, store_id: str) -> Optional[dict]:
        """Get detailed store information."""
        config = get_store_config(store_id)
        if not config:
            return None
        
        return {
            "store_id": config.store_id,
            "name": config.name,
            "display_name": config.display_name,
            "region": config.region.value,
            "base_url": config.base_url,
            "supports_delivery": config.supports_delivery,
            "supports_click_collect": config.supports_click_collect,
            "price_multiplier": config.price_multiplier
        }
    
    def get_all_stores_info(self) -> dict[str, dict]:
        """Get information for all available stores."""
        return {
            store_id: self.get_store_info(store_id) 
            for store_id in self.stores
        }


# Global instance
grocery_service = GroceryService()