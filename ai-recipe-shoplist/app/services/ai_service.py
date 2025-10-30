"""AI service for intelligent web crawling and grocery search optimization."""

import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from ..config.logging_config import get_logger
from ..config.pydantic_config import AI_SERVICE_SETTINGS
from ..config.store_config import StoreConfig
from ..ia_provider import (
    AzureProvider,
    BaseAIProvider,
    GitHubProvider,
    OllamaProvider,
    OpenAIProvider,
    StubProvider,
)
from ..models import Ingredient, Product, Recipe, ShopphingCart
from ..utils.ai_helpers import (
    RECIPE_SHOPPING_ASSISTANT_PROMPT,
    RECIPE_SHOPPING_ASSISTANT_SYSTEM,
    format_ai_prompt,
)

# Get module logger
logger = get_logger(__name__)


class AIProvider(str, Enum):
    """Available AI providers."""
    OPENAI = "openai"
    AZURE = "azure"
    OLLAMA = "ollama"
    GITHUB = "github"
    STUB = "stub"


class AIService:
    """Main AI service that manages different providers."""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider_name = provider or AI_SERVICE_SETTINGS.provider
        self.provider = self._create_provider(self.provider_name)
    
    def _create_provider(self, provider_name: str) -> BaseAIProvider:
        """Create AI provider based on configuration."""        
        provider_map = {
            AIProvider.OPENAI: OpenAIProvider,
            AIProvider.AZURE: AzureProvider,
            AIProvider.OLLAMA: OllamaProvider,
            AIProvider.GITHUB: GitHubProvider,
            AIProvider.STUB: StubProvider,
        }
        
        if provider_name not in provider_map:
            raise ValueError(f"Unknown AI provider: {provider_name}")
        
        try:
            return provider_map[provider_name]()
        except Exception as e:
            print(f"[AIService] Error initializing {provider_name} provider: {e}")
            raise
    
    async def extract_recipe_intelligently(self, html_content: str, url: str) -> Recipe:
        """Extract recipe data using AI intelligence."""
        print(f"[AIService] Extracting recipe using {self.provider_name} provider")
        
        try:
            recipe: Recipe = await self.provider.extract_recipe_data(html_content, url)
            return recipe
        except Exception as e:
            print(f"[AIService] Error extracting recipe: {e}")
            # Fallback to basic parsing
            return Recipe.default()
    
    # async def optimize_product_matching(self, ingredient: Ingredient, 
    #                                   store_results: Dict[str, List[Product]]) -> Dict[str, List[Product]]:
    #     """Use AI to optimize product matching and ranking."""
    #     print(f"[AIService] Optimizing product matching for '{ingredient.name}'")
        
    #     optimized_results = {}
        
    #     for store_name, products in store_results.items():
    #         if not products:
    #             optimized_results[store_name] = []
    #             continue
            
    #         try:
    #             # Convert products to dict format for AI processing
    #             products_data = []
    #             for product in products:
    #                 products_data.append({
    #                     "title": product.title,
    #                     "price": product.price,
    #                     "brand": product.brand,
    #                     "size": product.size,
    #                     "store": product.store
    #                 })
                
    #             # Use AI to rank products
    #             ranked_products = await self.provider.match_products(
    #                 ingredient.name, products_data
    #             )
                
    #             # Convert back to Product objects and update with scores
    #             optimized_products = []
    #             for i, ranked_data in enumerate(ranked_products):
    #                 # Find original product
    #                 original_product = next(
    #                     (p for p in products if p.title == ranked_data.get("title")),
    #                     None
    #                 )
    #                 if original_product:
    #                     # Create new product with AI score
    #                     optimized_products.append(Product(
    #                         title=original_product.title,
    #                         price=original_product.price,
    #                         store=original_product.store,
    #                         url=original_product.url,
    #                         image_url=original_product.image_url,
    #                         brand=original_product.brand,
    #                         size=original_product.size,
    #                         unit_price=original_product.unit_price,
    #                         availability=original_product.availability
    #                     ))
                
    #             optimized_results[store_name] = optimized_products
                
    #         except Exception as e:
    #             print(f"[AIService] Error optimizing products for {store_name}: {e}")
    #             optimized_results[store_name] = products
        
    #     return optimized_results
    
    # async def suggest_alternatives(self, ingredient: Ingredient) -> str:
    #     """Suggest alternative ingredients using AI."""
    #     system = "You are a culinary expert. Suggest ingredient alternatives."
        
    #     # Use centralized prompt template
    #     prompt = format_ai_prompt(ALTERNATIVES_PROMPT, ingredient=ingredient.name)

    #     if logger.isEnabledFor(logging.DEBUG):
    #         logger.debug(f"[AIService] [suggest_alternatives] System message: {system}")
    #         logger.debug(f"[AIService] [suggest_alternatives] User message: {prompt}")

    #     messages = [
    #         {"role": "system", "content": system},
    #         {"role": "user", "content": prompt}
    #     ]
        
    #     try:
    #         response = await self.provider.complete_chat(messages, max_tokens=200)
            
    #         # Use centralized JSON parsing
    #         alternatives = safe_json_parse(response, fallback=[])
    #         return alternatives if isinstance(alternatives, list) else []
    #     except Exception as e:
    #         logger.error(f"[AIService] Error suggesting alternatives: {e}")
    #         logger.debug(f"[AIService] Raw response that failed to parse: {response[:200]}...")
    #         return []

    async def shopping_assistant(self, url: str) -> List[Product]:
        """Generate a structured shopping list using AI."""

        logger.info(f"[AIService] Generating shopping list for recipe URL: {url}")

        prompt = format_ai_prompt(RECIPE_SHOPPING_ASSISTANT_PROMPT, url=url)

        chat_params = {
            "messages": [
                {"role": "system", "content": RECIPE_SHOPPING_ASSISTANT_SYSTEM},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = await self.provider.complete_chat(chat_params, max_tokens=10000)
            return response.content

        except Exception as e:
            logger.error(f"[AIService] Error generating shopping list: {e}")
            return ""

    async def search_grocery_products_intelligently(self, ingredients: List[Ingredient], stores: List[StoreConfig] = []) -> List[ShopphingCart]:
        """Search grocery stores for deals on ingredients using AI."""
        logger.info(f"[AIService] Searching grocery products for ingredients using {self.provider_name} provider")

        try:
            carts: List[ShopphingCart] = await self.provider.search_grocery_products(ingredients, stores)
            return carts
        except Exception as e:
            print(f"[AIService] Error extracting products: {e}")
            return [ShopphingCart.default()]

# Global AI service instance
ai_service = None

def get_ai_service() -> AIService:
    """Get or create the global AI service instance."""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service