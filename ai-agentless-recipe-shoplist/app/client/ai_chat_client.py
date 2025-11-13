"""AI Chat Client Module"""

import json
import logging
import traceback

import rich

from app.ia_provider.provider_factory import AIProvider
from app.services.tokenizer_service import TokenizerService

from ..config.logging_config import get_logger
from ..config.pydantic_config import AI_SERVICE_SETTINGS
from ..config.store_config import StoreConfig
from ..models import ChatCompletionResult, Ingredient, Product, Recipe, ShoppingListItem

# Get module logger
logger = get_logger(__name__)

class AIChatClient():
    """AI Chat Client for handling chat completions and recipe/product extraction."""

    def __init__(self, provider):
        self.name = "AIChatClient"
        self.provider = provider

        self.tokenizer = TokenizerService()
        # self.max_model_tokens = AI_SERVICE_SETTINGS.max_model_tokens
        # self.max_response_tokens = AI_SERVICE_SETTINGS.max_response_tokens
        # self.cache_manager = CacheManager(CACHE_SETTINGS)
        # self.storage_manager = BlobManager(BLOB_SETTINGS)

    def _truncate_to_max_tokens(self, text: str) -> str:
        """Truncate text to fit within the provider's max token limit."""

        return self.tokenizer.truncate_to_token_limit(text, self.provider.max_tokens)

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
        prompt = self._truncate_to_max_tokens(prompt)

        chat_params = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "response_format": Recipe
        }
        
        try:
            return await self.provider.complete_chat(chat_params)
        except Exception as e:
            logger.error(f"[{self.name}] Error in extract_recipe_data: {e}")
            logger.error(f"[{self.name}] Full stack trace: {traceback.format_exc()}")
            raise Exception("Failed to extract recipe data using AI provider.") from e

    async def search_best_match_products(self, ingredient: Ingredient, fetch_content: list[dict]) -> ChatCompletionResult[ShoppingListItem]:
        """Search grocery products for an ingredient using AI."""

        logger.info(f"[{self.name}] Searching grocery products for {ingredient.name} using AI")

        if logger.isEnabledFor(logging.DEBUG):
            rich.print(fetch_content)
            rich.print(ingredient)

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

Ingredient:
{ingredient}

Store content:
{store_content}
"""

        # Truncate prompt if too long
        prompt = self._truncate_to_max_tokens(prompt)

        chat_params = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "response_format": ShoppingListItem
            # "response_format": Product
        }
        
        try:
            return await self.provider.complete_chat(chat_params)
        except Exception as e:
            logger.error(f"[{self.name}] Error in search_grocery_products: {e}")
            raise Exception("Failed to extract product data using AI provider.") from e

    async def close(self):
        await self.provider.close()

# Global AI Chat Client instance
ai_chat_client = None

def get_chat_client() -> AIChatClient:
    """Get the global AI chat client instance."""
    global ai_chat_client
    if ai_chat_client is None:
        provider_name = AI_SERVICE_SETTINGS.provider
        provider = AIProvider.create_provider(provider_name)
        ai_chat_client = AIChatClient(provider=provider)
    return ai_chat_client
