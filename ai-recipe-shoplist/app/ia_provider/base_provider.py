"""Base AI provider abstract class and common utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..config.logging_config import get_logger, log_function_call
from ..config.store_config import StoreConfig
from ..models import Ingredient, Product, Recipe, ShopphingCart
from ..utils.ai_helpers import (
    log_ai_chat_query,
    log_ai_chat_response,
    safe_json_parse,
)

# Get module logger
logger = get_logger(__name__)

from ..config.pydantic_config import AI_SERVICE_SETTINGS
from ..services.tokenizer_service import TokenizerService  # Import TokenizerService
from ..utils.retry_utils import (
    AIRetryConfig,
    NetworkError,
    RateLimitError,
    ServerError,
    with_ai_retry,
)


@dataclass
class ChatMessageResult:
    content: str
    parsed: Any = None
    refusal: Any = None

class BaseAIProvider(ABC):
    """Complete a chat conversation using AI Models with tenacity retry logic."""

    def __init__(self):
        self.tokenizer = TokenizerService()

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

    async def complete_chat(self, params: any, **kwargs) -> ChatMessageResult:
        """Complete a chat conversation."""

        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)

        @with_ai_retry(self.retry_config)
        async def chat_completion_request():            
            try:
                chat_params = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **params
                }

                log_ai_chat_query(self.name, chat_params, logger)

                if "response_format" in chat_params:
                    response = await self.client.chat.completions.parse(**chat_params)
                else:
                    response = await self.client.chat.completions.create(**chat_params)

                log_ai_chat_response(self.name, response, logger)
                
                message = response.choices[0].message

                return ChatMessageResult(
                    content=message.content or None,
                    parsed=getattr(message, "parsed", None),
                    refusal=getattr(message, "refusal", None)
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
                
        if AI_SERVICE_SETTINGS.provider_chat_enabled:
            try:
                return await chat_completion_request()
            except Exception as e:
                logger.error(f"[{self.name}] OpenAI API error: {e}")
                raise
        else:
            logger.info(f"[{self.name}] AI provider chat calls are disabled. Skipping API call.")
            return ChatMessageResult(
                content="",
                parsed=None,
                refusal="AI provider chat calls are disabled."
            )
            
    async def extract_recipe_data(self, html_content: str, url: str) -> Recipe:
        """Extract structured recipe data from HTML using AI."""

        logger.info(f"[{self.name}] Extracting recipe data from URL: {url}")

        # Set system message
        system = """
        You are an AI assistant specialized in extracting structured recipe data from web pages.
        Your task is to analyze the provided HTML content and return a valid JSON object containing the recipe's title, ingredients (with normalized names and quantities), and instructions.

        Guidelines:
        - Output strictly valid JSON, with no extra text or comments.
        - Normalize ingredient names and quantities.
        - Include the recipe title, a list of ingredients (with name and quantity), and step-by-step instructions.
        """

        # Use centralized prompt template
        prompt = f"""
        Please extract the recipe details from the following HTML content and return only a valid JSON object.

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
            response = await self.complete_chat(chat_params)
            return response.parsed if response.parsed else Recipe.default()
        except Exception as e:
            logger.error(f"[{self.name}] Error in extract_recipe_data: {e}")
            
            # Return minimal structure if parsing fails
            return Recipe.default()

    async def search_best_match_products(self, ingredient: Ingredient, store: StoreConfig, fetch_content: list[dict]) -> list[Product]:
        """Search grocery products for an ingredient using AI."""

        logger.info(f"[{self.name}] Searching grocery products for {ingredient.name} in {store.name}")

        # Set system message
        system = f"""
        You are an AI assistant specialized in searching and comparing grocery products online.
        Your task is to analyze the provided list of grocery stores and ingredients, then return a structured JSON object containing the best-matched products for each ingredient.

        Guidelines:
        - Search each store for the listed ingredients, considering quantity and unit.
        - Prioritize name similarity, product relevance, brand quality, and value for money (price per unit) or (price vs size).
        - Include organic or premium options where available.
        - Round up quantities as needed to fulfill ingredient requirements.
        - Output strictly valid JSON with no extra text or comments.
        - If no good match is found for an ingredient, indicate it clearly in the output.
        """

        # Use centralized prompt template
        prompt = f"""
        Extract grocery product information from the grocery website for a list of ingredients.

        Store to search:
        {store.name}

        Ingredients:
        {ingredient}

        Products content:
        {fetch_content}
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
            response = await self.complete_chat(chat_params, max_tokens=500)
            return response.parsed if response.parsed else []
        except Exception as e:
            logger.error(f"[{self.name}] Error in search_grocery_products: {e}")

            # Return minimal structure if parsing fails
            return []


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