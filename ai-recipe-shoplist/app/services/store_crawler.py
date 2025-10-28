"""Store crawler with configurable store support."""

import asyncio
import logging
import random
from typing import Dict, List, Optional

from ..config.logging_config import get_logger
from ..config.store_config import (
    DEFAULT_REGION,
    StoreRegion,
    get_active_stores,
    get_store_config,
    validate_store_id,
)
from ..models import Ingredient, Product, StoreSearchResult

logger = get_logger(__name__)


class ConfigurableStoreCrawler:
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
    
    async def search_all_stores(self, ingredients: List[Ingredient], 
                               store_names: List[str] = None) -> Dict[str, List[StoreSearchResult]]:
        """Search all stores for ingredients."""
        # Validate and filter store names
        if store_names:
            active_stores = []
            for store_name in store_names:
                store_name_lower = store_name.lower()
                if validate_store_id(store_name_lower) and store_name_lower in self.stores:
                    active_stores.append(store_name_lower)
                else:
                    logger.warning(f"Invalid or unavailable store: {store_name}")
        else:
            active_stores = self.stores
        
        if not active_stores:
            logger.error("No valid stores available for search")
            return {}
        
        logger.info(f"Searching stores: {active_stores}")
        results = {}
        
        for store in active_stores:
            store_config = get_store_config(store)
            if not store_config:
                logger.warning(f"No configuration found for store: {store}")
                continue
                
            store_results = []
            
            for ingredient in ingredients:
                # Generate mock products with store configuration
                # products = await self._generate_mock_products(ingredient, store_config)
                
                store_results.append(StoreSearchResult(
                    ingredient_name=ingredient.name,
                    store_name=store,
                    products=products,
                    search_time=store_config.rate_limit_delay * 0.1  # Simulate search time
                ))
            
            results[store] = store_results

        logger.info(f"Completed search for stores: {list(results.keys())}")

        if logger.isEnabledFor(logging.DEBUG):
            for store, store_results in results.items():
                for result in store_results:
                    logger.debug(f"Store: {store}, Ingredient: {result.ingredient_name}, "
                                 f"Products found: {len(result.products)}")
        
        return results
    
    async def _generate_mock_products(self, ingredient: Ingredient, store_config) -> List[Product]:
        """Generate mock products for an ingredient using store configuration."""
        await asyncio.sleep(store_config.rate_limit_delay * 0.05)  # Simulate network delay based on store config
        
        base_price = random.uniform(2.0, 10.0)
        
        # Apply store-specific pricing
        final_price = base_price * store_config.price_multiplier
        
        products = [
            Product(
                title=f"{ingredient.name.title()} - {store_config.display_name} Brand",
                price=round(final_price, 2),
                store=store_config.store_id,
                url=store_config.get_product_url(f"{ingredient.name.replace(' ', '-')}-001"),
                brand=f"{store_config.name}",
                size="500g",
                availability=True
            ),
            Product(
                title=f"Premium {ingredient.name.title()}",
                price=round(final_price * 1.3, 2),
                store=store_config.store_id,
                url=store_config.get_product_url(f"premium-{ingredient.name.replace(' ', '-')}-002"),
                brand="Premium Brand",
                size="400g",
                availability=True
            )
        ]
        
        # Add organic option for stores that support it
        if store_config.supports_delivery:
            products.append(Product(
                title=f"Organic {ingredient.name.title()}",
                price=round(final_price * 1.6, 2),
                store=store_config.store_id,
                url=store_config.get_product_url(f"organic-{ingredient.name.replace(' ', '-')}-003"),
                brand="Organic Brand",
                size="350g",
                availability=True
            ))
        
        return products
    
    def get_available_stores(self) -> List[str]:
        """Get list of available stores for current region."""
        return self.stores.copy()
    
    def get_store_info(self, store_id: str) -> Optional[Dict]:
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
    
    def get_all_stores_info(self) -> Dict[str, Dict]:
        """Get information for all available stores."""
        return {
            store_id: self.get_store_info(store_id) 
            for store_id in self.stores
        }


# Global instance
store_crawler = ConfigurableStoreCrawler()