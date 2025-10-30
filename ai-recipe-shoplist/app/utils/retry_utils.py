"""Retry utilities for AI providers using tenacity library."""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Awaitable, Callable, Optional, TypeVar

import httpx

# Import tenacity for robust retry logic
try:
    from tenacity import (
        after_log,
        before_sleep_log,
        retry,
        retry_if_exception,
        stop_after_attempt,
        wait_random_exponential,
    )
except ImportError:
    raise ImportError("tenacity library not installed. Run: pip install tenacity")

from ..config.logging_config import get_logger
from ..config.pydantic_config import RETRY_SETTINGS

logger = get_logger(__name__)

T = TypeVar('T')


def load_retry_config():
    """Load retry configuration from .env file."""
    try:
        from dotenv import load_dotenv

        # Look for .env file in the project root
        current_dir = Path(__file__).parent
        env_file = current_dir.parent.parent / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            logger.debug(f"Loaded configuration from {env_file}")
            return True
        else:
            logger.debug("No .env file found, using environment variables")
            return False
    except ImportError:
        logger.warning("python-dotenv not available, using environment variables only")
        return False
    except Exception as e:
        logger.warning(f"Error loading configuration: {e}")
        return False


# Load configuration on module import
load_retry_config()


class RateLimiter:
    """Rate limiter that tracks requests over time."""
    
    def __init__(self, requests_per_minute: int = 15):
        self.requests_per_minute = requests_per_minute
        self.request_times: list[float] = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        if self.requests_per_minute <= 0:  # 0 = unlimited
            return
            
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # If we're at the limit, wait until we can make another request
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = min(self.request_times)
            wait_time = 60 - (current_time - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limit reached ({self.requests_per_minute} RPM), waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Record this request time
        self.request_times.append(time.time())


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""


class RateLimitError(RetryableError):
    """Error indicating rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(RetryableError):
    """Error indicating server-side issue."""


class NetworkError(RetryableError):
    """Error indicating network connectivity issue."""


def is_retryable_error(exception: Exception) -> bool:
    """Check if an exception should trigger a retry."""
    if isinstance(exception, (RetryableError, RateLimitError, ServerError, NetworkError)):
        return True
    
    # HTTP errors
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on 429 (rate limit) and 5xx (server errors)
        return exception.response.status_code == 429 or exception.response.status_code >= 500
    
    # Network errors
    if isinstance(exception, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)):
        return True
    
    # AI provider specific errors
    error_str = str(exception).lower()
    if any(keyword in error_str for keyword in ['rate limit', 'timeout', 'connection', 'server error', '503', '502', '429']):
        return True
    
    return False


def create_ai_retry_decorator(
    provider_name: str,
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    multiplier: Optional[float] = None
):
    """
    Create a tenacity retry decorator for AI providers.
    
    Args:
        provider_name: Name of the provider (e.g., "GITHUB", "OPENAI")
        max_retries: Override for max retries
        base_delay: Override for base delay
        max_delay: Override for max delay
        multiplier: Override for exponential multiplier
    
    Returns:
        Configured tenacity retry decorator
    """
    # Use provider-specific env vars with fallbacks
    max_retries = max_retries or int(os.getenv(f"{provider_name}_MAX_RETRIES", "3"))
    base_delay = base_delay or float(os.getenv(f"{provider_name}_BASE_DELAY", "1.0"))
    max_delay = max_delay or float(os.getenv(f"{provider_name}_MAX_DELAY", "60.0"))
    multiplier = multiplier or float(os.getenv(f"{provider_name}_RETRY_MULTIPLIER", "2.0"))
    
    return retry(
        # Stop after max attempts
        stop=stop_after_attempt(max_retries + 1),
        
        # Exponential backoff with jitter
        wait=wait_random_exponential(
            multiplier=base_delay,
            max=max_delay,
            exp_base=multiplier
        ),
        
        # Retry on specific errors
        retry=retry_if_exception(is_retryable_error),
        
        # Logging
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        
        # Re-raise the last exception if all retries fail
        reraise=True
    )


class AIRetryConfig:
    """Configuration for AI provider retry behavior with fallback to defaults."""
    
    def __init__(
        self,
        provider_name: str,
        max_retries: Optional[int] = None,
        base_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        requests_per_minute: Optional[int] = None,
        multiplier: Optional[float] = None
    ):
        self.provider_name = provider_name

        self.max_retries = max_retries or int(os.getenv(f"{provider_name}_MAX_RETRIES") or RETRY_SETTINGS.max_attempts)
        self.base_delay = base_delay or float(os.getenv(f"{provider_name}_BASE_DELAY") or RETRY_SETTINGS.base_delay)
        self.max_delay = max_delay or float(os.getenv(f"{provider_name}_MAX_DELAY") or RETRY_SETTINGS.max_delay)
        self.multiplier = multiplier or float(os.getenv(f"{provider_name}_RETRY_MULTIPLIER") or RETRY_SETTINGS.multiplier)
        rpm = requests_per_minute or int(os.getenv(f"{provider_name}_RPM_LIMIT") or RETRY_SETTINGS.rpm_limit)

        self.rate_limiter = RateLimiter(rpm) if rpm > 0 else None
        
        # Create tenacity retry decorator
        self.retry_decorator = create_ai_retry_decorator(
            provider_name, self.max_retries, self.base_delay, self.max_delay, self.multiplier
        )
        
        logger.debug(f"[AIRetryConfig] {provider_name} retry config: max_retries={self.max_retries}, "
                    f"base_delay={self.base_delay}s, max_delay={self.max_delay}s, "
                    f"multiplier={self.multiplier}, rpm_limit={rpm}")

    
def with_ai_retry(retry_config: AIRetryConfig):
    """
    Decorator to add retry logic to async functions.
    
    Usage:
        @with_ai_retry(retry_config)
        async def my_api_call():
            # Your API logic here
            pass
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @retry_config.retry_decorator
        async def wrapper(*args, **kwargs) -> T:
            # Apply rate limiting before function call
            if retry_config.rate_limiter:
                await retry_config.rate_limiter.wait_if_needed()
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def retry_with_tenacity(
    func: Callable[[], Awaitable[T]],
    retry_config: AIRetryConfig,
    operation_name: str = "operation"
) -> T:
    """
    Retry an async function using tenacity.
    
    Args:
        func: Async function to retry
        retry_config: Retry configuration
        operation_name: Name of operation for logging
    
    Returns:
        Result of successful function call
        
    Raises:
        Last exception if all retries exhausted
    """
    @retry_config.retry_decorator
    async def execute():
        # Apply rate limiting before each attempt
        if retry_config.rate_limiter:
            await retry_config.rate_limiter.wait_if_needed()
        
        return await func()
    
    try:
        return await execute()
    except Exception as e:
        logger.error(f"{operation_name} failed after all retries: {e}")
        raise


# Convenience functions for creating retry configs
def create_ai_retry_config(
    provider_name: str,
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    requests_per_minute: Optional[int] = None
) -> AIRetryConfig:
    """
    Create a retry configuration for AI providers with environment variable support.
    
    Args:
        provider_name: Name of the provider (e.g., "GITHUB", "OPENAI")
        max_retries: Override for max retries
        base_delay: Override for base delay
        max_delay: Override for max delay
        requests_per_minute: Override for rate limit
    
    Returns:
        Configured AIRetryConfig instance
    """
    return AIRetryConfig(
        provider_name=provider_name,
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        requests_per_minute=requests_per_minute
    )


# Provider-specific convenience functions
def create_github_retry_config(**kwargs) -> AIRetryConfig:
    """Create retry config for GitHub Models with conservative defaults."""
    return create_ai_retry_config("GITHUB", requests_per_minute=15, **kwargs)


def create_openai_retry_config(**kwargs) -> AIRetryConfig:
    """Create retry config for OpenAI with higher rate limits."""
    return create_ai_retry_config("OPENAI", requests_per_minute=60, **kwargs)


def create_azure_retry_config(**kwargs) -> AIRetryConfig:
    """Create retry config for Azure OpenAI with highest rate limits."""
    return create_ai_retry_config("AZURE", requests_per_minute=120, **kwargs)


def create_ollama_retry_config(**kwargs) -> AIRetryConfig:
    """Create retry config for Ollama with no rate limiting."""
    return create_ai_retry_config("OLLAMA", requests_per_minute=0, **kwargs)