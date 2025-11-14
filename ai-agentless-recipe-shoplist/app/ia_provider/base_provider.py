"""Base AI provider abstract class and common utilities."""

from abc import ABC, abstractmethod
import traceback

from app.storage.storage_manager import get_storage_manager

from ..config.logging_config import get_logger, log_function_call
from ..models import ChatCompletionResult
from ..utils.ai_helpers import (
    get_ai_token_stats,
    log_ai_chat_query,
    log_ai_chat_response,
    log_ai_error,
)

# Get module logger
logger = get_logger(__name__)

from ..config.pydantic_config import AI_SERVICE_SETTINGS
from ..utils.retry_utils import (
    AIRetryConfig,
    NetworkError,
    RateLimitError,
    ServerError,
    with_ai_retry,
)


class BaseAIProvider(ABC):
    """Complete a chat conversation using AI Models with tenacity retry logic."""

    def __init__(self):
        # Initialize cache manager and content storage
        self.content_storage = get_storage_manager()
        
        # self.cache_manager = CacheManager(ttl=CACHE_SETTINGS.ai_ttl)  # Separate TTL for AI responses
        # self.content_storage = BlobManager(BLOB_SETTINGS.base_path / "ai_cache") # Separate storage path for AI responses

    @property
    @abstractmethod
    def name(self) -> str:
        """Each child must define a name"""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Each child must define a model"""
        pass

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Each child must define a max_tokens"""
        pass

    @property
    @abstractmethod
    def temperature(self) -> float:
        """Each child must define a temperature"""
        pass

    @property
    @abstractmethod
    def retry_config(self) -> AIRetryConfig:
        """Each child must define a retry configuration"""
        pass

    async def complete_chat(self, params: any, **kwargs) -> ChatCompletionResult:
        """Complete a chat conversation."""
        
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)

        log_function_call("BaseAIProvider.complete_chat", {
            "max_tokens": max_tokens,
            "temperature": temperature
        })

        @with_ai_retry(self.retry_config)
        async def chat_completion_request() -> ChatCompletionResult:
            try:
                chat_params = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **params
                }

                log_ai_chat_query(self.name, chat_params, logger)

                if not AI_SERVICE_SETTINGS.provider_chat_enabled:
                    logger.warning(f"[{self.name}] AI provider chat calls are disabled. Skipping API call.")
                    return ChatCompletionResult(
                        success=False,
                        refusal="AI provider chat calls are disabled.",
                    )
                
                if "response_format" in chat_params:
                    response = await self.client.chat.completions.parse(**chat_params)
                else:
                    response = await self.client.chat.completions.create(**chat_params)

                log_ai_chat_response(self.name, response, logger)
                
                message = response.choices[0].message

                metadata = get_ai_token_stats(self.name, response)
                metadata["data_from"] = "ai_api"

                return ChatCompletionResult(
                    success=False if message.refusal else True,
                    content=message.parsed if hasattr(message, "parsed") else message.content,
                    refusal=message.refusal if hasattr(message, "refusal") else None,
                    metadata=metadata
                )
            except Exception as e:
                # Convert provider-specific errors to our retry framework
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    raise RateLimitError(f"{self.name} rate limit: {e}")
                elif any(keyword in error_str for keyword in ["server", "503", "502", "500"]):
                    raise ServerError(f"{self.name} server error: {e}")
                elif any(keyword in error_str for keyword in ["timeout", "connection"]):
                    raise NetworkError(f"{self.name} network error: {e}")
                else:
                    raise
                
        try:
            # Check cache first
            data_key = next((msg["content"] for msg in params.get("messages", []) if msg.get("role") == "user"), str(params))
            model_class = params.get("response_format", None)
            
            # Try to load from cache or storage
            loaded_response = await self.content_storage.load_ai_response(key=data_key, alias=self.name, model_class=model_class)
            if loaded_response:
                logger.info(f"[{self.name}] Loaded AI response from cache/storage for model_class: {model_class}")
                return loaded_response

            # Make AI chat completion request
            response: ChatCompletionResult = await chat_completion_request()

            # Save responses
            await self.content_storage.save_ai_response(key=data_key, data=response, alias=self.name, format="json")

            return response
        except Exception as e:
            log_ai_error(self.name, e, logger)
            raise
            
    async def close(self):
        await self._client.aclose()