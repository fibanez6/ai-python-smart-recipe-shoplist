"""
Store configuration for grocery store crawlers.
Contains store metadata, URLs, and search parameters.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.config.pydantic_config import RAPID_API_SETTINGS


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

    # Search parameters
    search_api_url: Optional[str] = None
    search_type: str = "html"  # e.g., "html", "api", "graphql"
    search_query_param: str = "q"
    search_headers: Optional[dict[str, Any]] = None
    search_params: Optional[dict[str, Any]] = None

    search_api_result_jsonpath: Optional[str] = None  # e.g., "data.items" for nested JSON responses
    search_api_result_jsonrules: Optional[dict[str, Any]] = None  # Extraction rules for JSON responses

    # Request settings
    request_rate_limit_delay: float = 1.0
    request_timeout: int = 30
    request_user_agent: Optional[str] = None
    
    # Selectors for web scraping for search_type: "html"
    html_selectors: Optional[dict[str, str]] = None
    
    def get_search_url(self, query: str) -> str:
        """Generate search URL for a query."""
        params = self.get_query_params(query)
        params_str = "&".join(f"{key}={value}" for key, value in params.items())

        return f"{self.search_url}?{params_str}"
    
    def get_query_params(self, query: str) -> dict:
        """Generate product query string."""
        return {
            self.search_query_param: query.replace(" ", "%20"),
            **(self.search_params or {}),
        }

# Australian grocery stores
STORE_CONFIGS: dict[str, StoreConfig] = {
    "aldi": StoreConfig(
        store_id="aldi",
        name="ALDI",
        display_name="ALDI Australia",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.aldi.com.au",
        search_url="https://www.aldi.com.au/results",
        search_api_url="https://api.aldi.com.au/v3/product-search",
        search_query_param="q",
        search_params={
            "currency": "AUD",
            "limit": 12
        },
        # search_type="html",
        search_type="Aldi_api",
        search_api_result_jsonpath="data",
        html_selectors={
            "product_tile": ".product-tile",
            "product_name": '.product-tile__name',
            "product_price": '.product-tile__price',
            "product_price_unit": '.product-tile__unit-of-measurement',
            "product_image": '.product-tile__picture img',
            "product_brand": '.product-tile__brandname',
            "product_url": '.product-tile__link'
        },
        search_api_result_jsonrules={
            "data": {
                "fields": ["name", "brandName", "quantityUnit", "sellingSize"],
                "price": {
                    "fields": ["amount", "amountRelevantDisplay", "comparisonDisplay"],
                },
                "categories[*].name": True,
                # extract only first image URL
                "assets": {
                    "limit": 1,
                    "fields": ["url"],
                },
            }
        },
        request_rate_limit_delay=2.0  # More conservative for ALDI
    ),

    "coles": StoreConfig(
        store_id="coles",
        name="Coles",
        display_name="Coles Supermarkets",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.coles.com.au",
        search_url="https://coles-product-price-api.p.rapidapi.com/coles/product-search",
        search_api_url="https://coles-product-price-api.p.rapidapi.com/coles/product-search",
        search_type="coles_rapidapi",
        search_query_param="query",
        search_api_result_jsonpath="results",
        search_headers={
            "x-rapidapi-key":  RAPID_API_SETTINGS.api_key
        },
        search_params={
            "size": 12
        },
        search_api_result_jsonrules={
            "results": True
        },
        request_rate_limit_delay=1.5,
    ),
    
    "woolworths": StoreConfig(
        store_id="woolworths", 
        name="Woolworths",
        display_name="Woolworths Supermarkets",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.woolworths.com.au",
        search_url="https://www.woolworths.com.au/shop/search",
        search_query_param="searchTerm",
        search_params={
            "size": 12
        },
        html_selectors={
            "product_title": "[data-testid='product-title']",
            "product_price": "[data-testid='product-price']",
            "product_image": "[data-testid='product-image']",
            "product_brand": "[data-testid='product-brand']",
            "product_size": "[data-testid='product-package-size']"
        },
        request_rate_limit_delay=1.2,
    ),
        
    "iga": StoreConfig(
        store_id="iga",
        name="IGA",
        display_name="IGA (Independent Grocers of Australia)",
        region=StoreRegion.AUSTRALIA,
        base_url="https://www.iga.com.au", 
        search_url="https://www.iga.com.au/search",
        search_query_param="term",
        html_selectors={
            "product_title": ".product-name",
            "product_price": ".product-price",
            "product_image": ".product-img",
            "product_brand": ".product-brand",
            "product_size": ".product-weight"
        },
        request_rate_limit_delay=1.8
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