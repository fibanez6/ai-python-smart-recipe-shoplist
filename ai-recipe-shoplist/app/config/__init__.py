"""Configuration modules for the AI Recipe Shoplist Crawler."""

from .logging_config import (
    LOG_LEVEL,
    get_logger,
    log_api_request,
    log_function_call,
    set_debug_mode,
    setup_logging,
)
from .store_config import (
    DEFAULT_REGION,
    DEFAULT_STORES,
    REGIONAL_STORES,
    STORE_CONFIGS,
    StoreConfig,
    StoreRegion,
    get_active_stores,
    get_all_store_ids,
    get_store_config,
    get_store_display_names,
    get_stores_by_region,
    validate_store_id,
)



__all__ = [
    # Store configuration
    "StoreConfig",
    "StoreRegion", 
    "STORE_CONFIGS",
    "REGIONAL_STORES",
    "get_store_config",
    "get_stores_by_region",
    "get_all_store_ids",
    "get_active_stores",
    "validate_store_id",
    "get_store_display_names",
    "DEFAULT_REGION",
    "DEFAULT_STORES",
    
    # Logging configuration
    "setup_logging",
    "get_logger", 
    "set_debug_mode",
    "log_function_call",
    "log_api_request",
    "LOG_LEVEL"
]