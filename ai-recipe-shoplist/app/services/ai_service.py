"""AI service for intelligent web crawling and grocery search optimization."""

import logging
from enum import Enum
from functools import partial
from typing import Optional

from app.services.web_data_service import get_web_data_service

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
from ..models import ChatCompletionResult, Ingredient, Product, Recipe, ShopphingCart
from ..utils.ai_helpers import (
    RECIPE_SHOPPING_ASSISTANT_PROMPT,
    RECIPE_SHOPPING_ASSISTANT_SYSTEM,
    format_ai_prompt,
)
from ..web_extractor.html_extractor import clean_html, clean_html_with_selectors

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
        self.name = "AIService"
        self.provider_name = provider or AI_SERVICE_SETTINGS.provider
        self.provider = self._create_provider(self.provider_name)
        self.web_data_service = get_web_data_service()
    
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
            print(f"[{self.name}] Error initializing {provider_name} provider: {e}")
            raise

    async def extract_recipe_intelligently(self, url: str) -> dict:
        """Extract recipe data using AI intelligence."""
        print(f"[{self.name}] Extracting recipe using {self.provider_name} provider")
        
        try:
            # Get html extractor
            html_extractor = clean_html

            # Use web data service to fetch and process content
            fetch_result = await self.web_data_service.fetch_and_process(url, html_extractor, data_format="html")

            if logger.isEnabledFor(logging.DEBUG):
                if isinstance(fetch_result, dict):
                    logger.debug(f"[{self.name}] Fetched result data keys: {list(fetch_result.keys())}")
                logger.debug(f"[{self.name}] Fetched result data: {str(fetch_result)[:100]}")

            if "data" not in fetch_result:
                raise ValueError("No data found in fetched result for recipe extraction")
            
            # Extract recipe using AI provider
            fetch_data_processed = fetch_result.get("data")
            ia_response: ChatCompletionResult[Recipe] = await self.provider.extract_recipe_data(fetch_data_processed)

            # Parse AI response into Recipe model
            recipe = ia_response.content if isinstance(ia_response.content, Recipe) else Recipe(**ia_response.content)

            return {
                "recipe": recipe,
                "num_items": len(recipe.ingredients),
                "message": f"Successfully extracted recipe: {recipe.title}",
                "ai_info": {
                    "data_from": fetch_result.get("data_from", None),
                    "data_size": fetch_result.get("data_size", None),
                    "data_format": fetch_result.get("data_format", None),
                    "timestamp": fetch_result.get("timestamp", None),
                    **(ia_response.metadata or {})
                }
            }
        except Exception as e:
            logger.error(f"[{self.name}] Error extracting recipe: {e}")
            # Fallback to basic parsing
            return {
                "recipe": Recipe.default(),
                "message": f"Failed in extracting recipe",
            }

    async def search_grocery_products_intelligently(self, ingredient: Ingredient, stores: list[StoreConfig] = []) -> dict:
        """Search grocery stores for deals on ingredients using AI."""
        logger.info(f"[{self.name}] Searching {ingredient.name} in {stores} by using {self.provider_name} AI provider")

        try:
            # Fetch the products search results
            store_fetch_results = {}

            # Iterate over stores to fetch search results
            for store in stores:
                try:
                    # Fetch search page content
                    logger.info(f"[{self.name}] Searching products in store {store.name} from ingredient {ingredient.name}")

                    # Get html extractor
                    if store.search_type == "html" and store.html_selectors:
                        data_extractor = partial(clean_html_with_selectors, selectors=store.html_selectors)
                    else:
                        data_extractor = clean_html

                    # Use web data service to fetch and process content
                    url = store.get_search_url(ingredient.name)
                    fetch_result = await self.web_data_service.fetch_and_process(url, data_extractor, data_format=store.search_type)

                    if "data" not in fetch_result:
                        raise ValueError("No data found in fetched result for ingredient extraction")
                    
                    store_fetch_results[store.store_id] = fetch_result
                except Exception as e:
                    logger.error(f"[{self.name}] Error searching products in store {store.name}: {e}")
                    continue

            # Search for best match products using AI provider
            fetch_data_processed = []
            for fetch in store_fetch_results.values():
                if fetch.get("data"):
                    fetch_data_processed.extend(fetch.get("data"))
            ia_response: ChatCompletionResult[Product] = await self.provider.search_best_match_products(ingredient, store, fetch_data_processed)

            # Parse AI response into Product model
            product = ia_response.content if isinstance(ia_response.content, Product) else Product(**ia_response.content)

            return {
                "product": product,
                "ingredient": ingredient.name,
                "ai_info": {
                    **(ia_response.metadata or {})
                }
            }
        except Exception as e:
            logger.error(f"[{self.name}] Error extracting products: {e}")
            # Fallback to basic parsing
            return {
                "recipe": Recipe.default(),
                "message": f"Failed in getting products for ingredient",
            }
    
    # async def optimize_product_matching(self, ingredient: Ingredient, 
    #                                   store_results: dict[str, list[Product]]) -> dict[str, list[Product]]:
    #     """Use AI to optimize product matching and ranking."""
    #     print(f"[{self.name}] Optimizing product matching for '{ingredient.name}'")
        
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
    #             print(f"[{self.name}] Error optimizing products for {store_name}: {e}")
    #             optimized_results[store_name] = products
        
    #     return optimized_results
    
    # async def suggest_alternatives(self, ingredient: Ingredient) -> str:
    #     """Suggest alternative ingredients using AI."""
    #     system = "You are a culinary expert. Suggest ingredient alternatives."
        
    #     # Use centralized prompt template
    #     prompt = format_ai_prompt(ALTERNATIVES_PROMPT, ingredient=ingredient.name)

    #     if logger.isEnabledFor(logging.DEBUG):
    #         logger.debug(f"[{self.name}] [suggest_alternatives] System message: {system}")
    #         logger.debug(f"[{self.name}] [suggest_alternatives] User message: {prompt}")

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
    #         logger.error(f"[{self.name}] Error suggesting alternatives: {e}")
    #         logger.debug(f"[{self.name}] Raw response that failed to parse: {response[:200]}...")
    #         return []

    async def shopping_assistant(self, url: str) -> list[Product]:
        """Generate a structured shopping list using AI."""

        logger.info(f"[{self.name}] Generating shopping list for recipe URL: {url}")

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
            logger.error(f"[{self.name}] Error generating shopping list: {e}")
            return ""


# Global AI service instance
ai_service = None

def get_ai_service() -> AIService:
    """Get or create the global AI service instance."""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service