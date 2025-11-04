"""Base AI provider abstract class and common utilities."""

import json
from abc import ABC, abstractmethod

from app.manager.cache_manager import CacheManager
from app.manager.storage_manager import StorageManager

from ..config.logging_config import get_logger
from ..config.store_config import StoreConfig
from ..models import ChatCompletionResult, Ingredient, Product, Recipe
from ..utils.ai_helpers import (
    get_ai_token_stats,
    log_ai_chat_query,
    log_ai_chat_response,
)

# Get module logger
logger = get_logger(__name__)

from ..config.pydantic_config import (
    AI_SERVICE_SETTINGS,
    CACHE_SETTINGS,
    STORAGE_SETTINGS,
)
from ..services.tokenizer_service import TokenizerService  # Import TokenizerService
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
        self.tokenizer = TokenizerService()
        self.cache_manager = CacheManager(ttl=CACHE_SETTINGS.ai_ttl)  # Separate TTL for AI responses
        self.content_storage = StorageManager(STORAGE_SETTINGS.base_path / "ai_cache") # Separate storage path for AI responses

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

    def truncate_to_max_tokens(self, text: str) -> str:
        """Truncate text to fit within the provider's max token limit."""

        return self.tokenizer.truncate_to_token_limit(text, self.max_tokens)

    def _load_from_cache_or_storage(self, key: str, model_class: type = None) -> ChatCompletionResult | None:
        """Load AI response from cache or storage."""
        
        # Try cache first
        cached_response = self.cache_manager.load(key=key, alias=self.name)
        if cached_response:
            logger.info(f"[{self.name}] Loaded ai response from cache")
            return self._build_chat_result(cached_response, model_class)

        # Try storage if cache miss
        disk_data = self.content_storage.load(key=key, alias=self.name, model_class=ChatCompletionResult)
        if disk_data:
            logger.info(f"[{self.name}] Loaded ai response from storage")
            return self._build_chat_result(disk_data, model_class)

        return None
    
    def _build_chat_result(self, data: dict, model_class: type = None) -> ChatCompletionResult:
        """Build ChatCompletionResult from cached/stored data."""
        data_from = data["data_from"]
        chat_result = data["data"]
        
        content = chat_result.content
        if model_class:
            content = model_class(**content)
            
        return chat_result.model_copy(update={
            "content": content,
            "metadata": {"data_from": data_from}
        })

    async def complete_chat(self, params: any, **kwargs) -> ChatCompletionResult:
        """Complete a chat conversation."""

        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)

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
                    content=message.parsed if message.parsed else message.content,
                    refusal=message.refusal if message.refusal else None,
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
            cached_response = self._load_from_cache_or_storage(data_key, model_class=model_class)
            if cached_response:
                return cached_response
            
            # Make AI chat completion request
            response: ChatCompletionResult = await chat_completion_request()

            # Save responses
            self.cache_manager.save(key=data_key, obj=response, alias=self.name)
            self.content_storage.save(key=data_key, obj=response, alias=self.name, format="json")

            return response
        except Exception as e:
            logger.error(f"[{self.name}] OpenAI API error: {e}")
            raise
            
    async def extract_recipe_data(self, html_content: str) -> ChatCompletionResult[Recipe]:
        """Extract structured recipe data from HTML using AI."""

        logger.info(f"[{self.name}] Extracting recipe data using AI")

        # Set system message
        system = """You are an AI assistant specialized in extracting structured recipe data from web pages.
Your task is to analyze the provided HTML content and return a valid JSON object containing the recipe's title, ingredients (with normalized names and quantities), and instructions.

Guidelines:
- Output strictly valid JSON, with no extra text or comments.
- Normalize ingredient names and quantities.
- Include the recipe title, a list of ingredients (with name and quantity), and step-by-step instructions.
- No ingredient should be missing or duplicated.
"""

        # Use centralized prompt template
        prompt = f"""Please extract the recipe details from the following HTML content and return only a valid JSON object.

HTML content:
{html_content}
"""

        # Truncate prompt if too long
        prompt = self.truncate_to_max_tokens(prompt)

        chat_params = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "response_format": Recipe
        }
        
        try:
            return await self.complete_chat(chat_params)
        except Exception as e:
            logger.error(f"[{self.name}] Error in extract_recipe_data: {e}")
            raise Exception("Failed to extract recipe data using AI provider.") from e

    async def search_best_match_products(self, ingredient: Ingredient, store: StoreConfig, fetch_content: list[dict]) -> ChatCompletionResult[Product]:
        """Search grocery products for an ingredient using AI."""

        logger.info(f"[{self.name}] Searching grocery products for {ingredient.name} in {store.name}")

        store_content = json.dumps(fetch_content, separators=(",", ":"))

        if not store_content or store_content == "[]":
            logger.warning(f"[{self.name}] No store content available to search for products.")
            raise ValueError("No store content available to search for products.")

        # Set system message
        system = """You are an AI assistant specialized in searching and comparing grocery products online.
Your task is to analyze the provided grocery store and ingredients, then return a structured JSON object containing the best-matched products.

Guidelines:
- Search the store for the listed ingredient, considering quantity and unit.
- Return the best-matched product with the quantity needed based on the ingredient.
- Round up quantities as needed to meet ingredient requirements.
- Prioritize name similarity, product relevance, brand quality, and value (price per unit).
- Include organic or premium options where applicable.
- Output strictly valid JSON with no extra text or comments.
- If no suitable match is found, clearly indicate this in the output.
"""

        # Use centralized prompt template
        prompt = f"""Extract grocery the best-matched product from the store content.

Store to search:
{store.display_name} ({store.product_url_template})

Ingredients:
{ingredient}

Store content:
{store_content}
"""

        # Truncate prompt if too long
        prompt = self.truncate_to_max_tokens(prompt)

        chat_params = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "response_format": Product
        }
        
        try:
            return await self.complete_chat(chat_params, max_tokens=500)
        except Exception as e:
            logger.error(f"[{self.name}] Error in search_grocery_products: {e}")
            raise Exception("Failed to extract product data using AI provider.") from e

    # async def match_products(self, ingredient: str, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    #     """Match and rank products for an ingredient using AI."""

    #     logger.info(f"[{self.name}] Matching products for ingredient")

    #     if not products:
    #         return []
        
    #     # Set system message
    #     system = PRODUCT_MATCHING_SYSTEM
        
    #     # Use centralized prompt template
    #     prompt = format_ai_prompt(
    #         PRODUCT_MATCHING_PROMPT,
    #         ingredient=ingredient,
    #         products_json=json.dumps(products, indent=2)
    #     )

    #     logger.debug(f"[{self.name}] System message: {system}")
    #     logger.debug(f"[{self.name}] User message: {prompt}")

    #     chat_params = {
    #         "messages": [
    #             {"role": "system", "content": system},
    #             {"role": "user", "content": prompt}
    #         ]
    #     }
        
    #     try:
    #         response = await self.complete_chat(chat_params)
    #         response = response.content

    #         # Use centralized JSON parsing
    #         ranked_products = safe_json_parse(response, fallback=products)
    #         return ranked_products if isinstance(ranked_products, list) else products
    #     except Exception as e:
    #         logger.error(f"[{self.name}] Error ranking products: {e}")
    #         # Only log response if it was defined
    #         try:
    #             logger.debug(f"[{self.name}] Raw response that failed to parse: {response[:500]}...")
    #         except NameError:
    #             logger.debug(f"[{self.name}] No response received due to earlier error")
    #         # Fallback: return original products with default scores
    #         for i, product in enumerate(products):
    #             product["match_score"] = 100 - (i * 10)  # Simple scoring
    #         return products
        

    async def close(self):
        await self._client.aclose()