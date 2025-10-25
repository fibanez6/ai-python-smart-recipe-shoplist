"""Utility modules for the AI Recipe Shoplist Crawler."""

from .ai_helpers import (
    ALTERNATIVES_PROMPT,
    INGREDIENT_NORMALIZATION_PROMPT,
    PRODUCT_MATCHING_PROMPT,
    RECIPE_EXTRACTION_PROMPT,
    clean_json_response,
    extract_json_from_text,
    format_ai_prompt,
    normalize_ai_response,
    safe_json_parse,
    validate_ingredient_data,
    validate_recipe_data,
)
from .retry_utils import (  # Core classes; Error types; Functions; Provider-specific configs
    AIRetryConfig,
    NetworkError,
    RateLimiter,
    RateLimitError,
    RetryableError,
    ServerError,
    create_ai_retry_config,
    create_azure_retry_config,
    create_github_retry_config,
    create_ollama_retry_config,
    create_openai_retry_config,
    is_retryable_error,
    retry_with_tenacity,
    with_ai_retry,
)

__all__ = [
    # AI utilities
    "clean_json_response",
    "safe_json_parse",
    "extract_json_from_text",
    "normalize_ai_response",
    "validate_ingredient_data",
    "validate_recipe_data",
    "format_ai_prompt",
    "RECIPE_EXTRACTION_PROMPT",
    "INGREDIENT_NORMALIZATION_PROMPT", 
    "PRODUCT_MATCHING_PROMPT",
    "ALTERNATIVES_PROMPT",
    
    # Retry utilities (tenacity-based)
    "RateLimiter",
    "AIRetryConfig",
    "HTTPRetryClient",
    "RetryableError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "create_ai_retry_config",
    "retry_with_tenacity",
    "with_ai_retry",
    "is_retryable_error",
    "create_github_retry_config",
    "create_openai_retry_config",
    "create_azure_retry_config",
    "create_ollama_retry_config"
]