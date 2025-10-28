"""
Store configuration for grocery store crawlers.
Contains store metadata, URLs, and search parameters.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class StoreRegion(str, Enum):
    """Supported store regions."""
    AUSTRALIA = "au"
    UNITED_STATES = "us"
    UNITED_KINGDOM = "uk"
    CANADA = "ca"


@dataclass
class StoreConfig:
    """Configuration for a grocery store."""
    
    # Basic store information
    store_id: str
    name: str
    display_name: str
    region: StoreRegion
    
    # URLs and endpoints
    base_url: str
    search_url: str
    product_url_template: str
    
    # Search parameters
    search_param: str = "q"
    results_per_page: int = 20
    max_pages: int = 3
    
    # Request settings
    rate_limit_delay: float = 1.0
    timeout: int = 30
    user_agent: Optional[str] = None
    
    # Pricing and features
    price_multiplier: float = 1.0
    supports_delivery: bool = True
    supports_click_collect: bool = True
    
    # Selectors for web scraping (CSS selectors)
    selectors: Optional[Dict[str, str]] = None
    
    def get_search_url(self, query: str) -> str:
        """Generate search URL for a query."""
        return f"{self.search_url}?{self.search_param}={query.replace(' ', '+')}"
    
    def get_product_url(self, product_id: str) -> str:
        """Generate product URL from template."""
        return self.product_url_template.format(product_id=product_id)


# Australian grocery stores
STORE_CONFIGS: Dict[str, StoreConfig] = {
    "coles": StoreConfig(
        store_id="coles",
        name="Coles",
        display_name="Coles Supermarkets",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.coles.com.au",
        search_url="https://www.coles.com.au/search",
        product_url_template="https://www.coles.com.au/product/{product_id}",
        search_param="q",
        rate_limit_delay=1.5,
        price_multiplier=1.0,
        selectors={
            "product_title": ".product-title",
            "product_price": ".price",
            "product_image": ".product-image img",
            "product_brand": ".product-brand",
            "product_size": ".product-size"
        }
    ),
    
    "woolworths": StoreConfig(
        store_id="woolworths", 
        name="Woolworths",
        display_name="Woolworths Supermarkets",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.woolworths.com.au",
        search_url="https://www.woolworths.com.au/shop/search/products",
        product_url_template="https://www.woolworths.com.au/shop/productdetails/{product_id}",
        search_param="searchTerm",
        rate_limit_delay=1.2,
        price_multiplier=1.05,
        selectors={
            "product_title": "[data-testid='product-title']",
            "product_price": "[data-testid='product-price']",
            "product_image": "[data-testid='product-image']",
            "product_brand": "[data-testid='product-brand']",
            "product_size": "[data-testid='product-package-size']"
        }
    ),
    
    "aldi": StoreConfig(
        store_id="aldi",
        name="ALDI",
        display_name="ALDI Australia",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.aldi.com.au",
        search_url="https://www.aldi.com.au/products",
        product_url_template="https://api.aldi.com.au/v3/product-search?currency=AUD&serviceType=walk-in&q={product_id}&limit=12&offset=0&sort=relevance&testVariant=A&servicePoint=G452",
        search_param="q",
        rate_limit_delay=2.0,  # More conservative for ALDI
        price_multiplier=0.85,  # ALDI typically cheaper
        supports_delivery=False,  # ALDI doesn't do delivery in most areas
        selectors={
            "product_title": ".product-tile__title",
            "product_price": ".product-tile__price",
            "product_image": ".product-tile__image",
            "product_brand": ".product-tile__brand",
            "product_size": ".product-tile__unit"
        }
    ),
    
    "iga": StoreConfig(
        store_id="iga",
        name="IGA",
        display_name="IGA (Independent Grocers of Australia)",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.iga.com.au", 
        search_url="https://www.iga.com.au/search",
        product_url_template="https://www.iga.com.au/product/{product_id}",
        search_param="term",
        rate_limit_delay=1.8,
        price_multiplier=1.15,  # IGA typically more expensive
        max_pages=2,  # Smaller chain, fewer results
        selectors={
            "product_title": ".product-name",
            "product_price": ".product-price",
            "product_image": ".product-img",
            "product_brand": ".product-brand",
            "product_size": ".product-weight"
        }
    ),
    
    # US stores (for future expansion)
    "walmart": StoreConfig(
        store_id="walmart",
        name="Walmart",
        display_name="Walmart Grocery",
        region=StoreRegion.UNITED_STATES,
        base_url="https://www.walmart.com",
        search_url="https://www.walmart.com/search",
        product_url_template="https://www.walmart.com/ip/{product_id}",
        search_param="query",
        rate_limit_delay=1.0,
        price_multiplier=0.95,
        selectors={
            "product_title": "[data-testid='product-title']",
            "product_price": "[data-testid='product-price']",
            "product_image": "[data-testid='product-image']",
            "product_brand": "[data-testid='product-brand']"
        }
    ),
    
    "target": StoreConfig(
        store_id="target",
        name="Target",
        display_name="Target Stores",
        region=StoreRegion.UNITED_STATES,
        base_url="https://www.target.com",
        search_url="https://www.target.com/s",
        product_url_template="https://www.target.com/p/{product_id}",
        search_param="searchTerm",
        rate_limit_delay=1.3,
        price_multiplier=1.1,
        selectors={
            "product_title": "[data-test='product-title']",
            "product_price": "[data-test='product-price']",
            "product_image": "[data-test='product-image']"
        }
    )
}


# Regional store groups
REGIONAL_STORES = {
    StoreRegion.AUSTRALIA: ["coles", "woolworths", "aldi", "iga"],
    StoreRegion.UNITED_STATES: ["walmart", "target"],
    StoreRegion.UNITED_KINGDOM: [],  # To be added
    StoreRegion.CANADA: []  # To be added
}


def get_store_config(store_id: str) -> Optional[StoreConfig]:
    """Get store configuration by ID."""
    return STORE_CONFIGS.get(store_id)


def get_stores_by_region(region: StoreRegion) -> List[StoreConfig]:
    """Get all stores in a specific region."""
    store_ids = REGIONAL_STORES.get(region, [])
    return [STORE_CONFIGS[store_id] for store_id in store_ids if store_id in STORE_CONFIGS]


def get_all_store_ids() -> List[str]:
    """Get all available store IDs."""
    return list(STORE_CONFIGS.keys())


def get_active_stores(region: StoreRegion = StoreRegion.AUSTRALIA) -> List[str]:
    """Get active store IDs for a region."""
    return REGIONAL_STORES.get(region, [])


def validate_store_id(store_id: str) -> bool:
    """Check if a store ID is valid."""
    return store_id in STORE_CONFIGS


def get_store_display_names() -> Dict[str, str]:
    """Get mapping of store IDs to display names."""
    return {store_id: config.display_name for store_id, config in STORE_CONFIGS.items()}


# Default configuration
DEFAULT_REGION = StoreRegion.AUSTRALIA
DEFAULT_STORES = get_active_stores(DEFAULT_REGION)