"""
Store configuration for grocery store crawlers.
Contains store metadata, URLs, and search parameters.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
    search_api_template: str

    # Product URL template
    product_url_template: str

    # Search parameters
    search_param: str = "q"
    search_limit_param: Optional[str] = None
    results_per_page: int = 5
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
    html_selectors: Optional[dict[str, str]] = None
    
    def get_search_url(self, query: str) -> str:
        """Generate search URL for a query."""
        limit = f"&{self.search_limit_param}={self.results_per_page}" if self.search_limit_param else ""
        return f"{self.search_url}?{self.search_param}={query.replace(' ', '+')}{limit}"
    
    def get_product_url(self, product_id: str) -> str:
        """Generate product URL from template."""
        return self.product_url_template.format(product_id=product_id)
    
    def get_store_name_and_search_url(self, product_name: str) -> str:
        """Return a string with the store name and product URL."""
        return f"{self.name}: {self.get_search_url(product_name)}"

# Australian grocery stores
STORE_CONFIGS: dict[str, StoreConfig] = {
    "coles": StoreConfig(
        store_id="coles",
        name="Coles",
        display_name="Coles Supermarkets",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.coles.com.au",
        search_url="https://www.coles.com.au/search",
        search_api_template="https://www.coles.com.au/api/search?q={query}",
        product_url_template="https://www.coles.com.au/search/products?q={product_id}",
        search_param="q",
        search_limit_param=None,
        rate_limit_delay=1.5,
        price_multiplier=1.0,
        html_selectors={
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
        search_url="https://www.woolworths.com.au/shop/search",
        search_api_template="https://www.woolworths.com.au/api/search?q={query}",
        product_url_template="https://www.woolworths.com.au/shop/productdetails/{product_id}",
        search_param="searchTerm",
        search_limit_param=None,
        rate_limit_delay=1.2,
        price_multiplier=1.05,
        html_selectors={
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
        search_url="https://www.aldi.com.au/results",
        search_api_template="https://api.aldi.com.au/v3/product-search?currency=AUD&q={product_id}",
        product_url_template="https://www.aldi.com.au/{product_id}",
        search_param="q",
        search_limit_param="limit",
        rate_limit_delay=2.0,  # More conservative for ALDI
        price_multiplier=0.85,  # ALDI typically cheaper
        supports_delivery=False,  # ALDI doesn't do delivery in most areas
        results_per_page=12,
        max_pages=1,
        html_selectors={
            "product_tile": ".product-tile",
            "product_name": '.product-tile__name',
            "product_price": '.product-tile__price',
            "product_price_unit": '.product-tile__unit-of-measurement',
            "product_image": '.product-tile__picture img',
            "product_brand": '.product-tile__brandname',
            "product_url": '.product-tile__link'
        }
    ),
    
    "iga": StoreConfig(
        store_id="iga",
        name="IGA",
        display_name="IGA (Independent Grocers of Australia)",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.iga.com.au", 
        search_url="https://www.iga.com.au/search",
        search_api_template="https://www.iga.com.au/api/search?q={query}",
        product_url_template="https://www.iga.com.au/product/{product_id}",
        search_param="term",
        search_limit_param=None,
        rate_limit_delay=1.8,
        price_multiplier=1.15,  # IGA typically more expensive
        max_pages=2,  # Smaller chain, fewer results
        html_selectors={
            "product_title": ".product-name",
            "product_price": ".product-price",
            "product_image": ".product-img",
            "product_brand": ".product-brand",
            "product_size": ".product-weight"
        }
    ),

}


# Regional store groups
REGIONAL_STORES = {
    StoreRegion.AUSTRALIA: ["coles", "woolworths", "aldi", "iga"],
    StoreRegion.UNITED_STATES: [],   # To be added
    StoreRegion.UNITED_KINGDOM: [],  # To be added
    StoreRegion.CANADA: []  # To be added
}


def get_store_config(store_id: str) -> Optional[StoreConfig]:
    """Get store configuration by ID."""
    return STORE_CONFIGS.get(store_id)


def get_stores_by_region(region: StoreRegion) -> list[StoreConfig]:
    """Get all stores in a specific region."""
    store_ids = REGIONAL_STORES.get(region, [])
    return [STORE_CONFIGS[store_id] for store_id in store_ids if store_id in STORE_CONFIGS]


def get_all_store_ids() -> list[str]:
    """Get all available store IDs."""
    return list(STORE_CONFIGS.keys())


def get_active_stores(region: StoreRegion = StoreRegion.AUSTRALIA) -> list[str]:
    """Get active store IDs for a region."""
    return REGIONAL_STORES.get(region, [])


def validate_store_id(store_id: str) -> bool:
    """Check if a store ID is valid."""
    return store_id in STORE_CONFIGS


def get_store_display_names() -> dict[str, str]:
    """Get mapping of store IDs to display names."""
    return {store_id: config.display_name for store_id, config in STORE_CONFIGS.items()}


# Default configuration
DEFAULT_REGION = StoreRegion.AUSTRALIA
DEFAULT_STORES = get_active_stores(DEFAULT_REGION)