"""AI service for intelligent web crawling and grocery search optimization."""

import logging
import traceback

import rich

from app.client.ai_chat_client import get_chat_client
from app.scrapers.html_scraper import get_html_scraper
from app.scrapers.scraper_factory import ScraperFactory

from ..config.logging_config import get_logger
from ..config.store_config import StoreConfig
from ..models import ChatCompletionResult, Ingredient, Product, Recipe, ShoppingListItem

# Get module logger
logger = get_logger(__name__)

class AIService:
    """AI Service for intelligent recipe extraction and grocery product search."""
    
    def __init__(self):
        self.name = "AIService"
        self.web_scraper = get_html_scraper()
        self.ai_chat_client = get_chat_client()
    
    async def extract_recipe_intelligently(self, url: str) -> dict:
        """Extract recipe data using AI intelligence."""
        print(f"[{self.name}] Extracting recipe using AI from URL: {url}")
        
        try:
            # Use web scraper to fetch and process content
            fetch_result = await self.web_scraper.fetch_and_process(url, html_selectors=None, data_format="html")

            if logger.isEnabledFor(logging.DEBUG):
                if isinstance(fetch_result, dict):
                    logger.debug(f"[{self.name}] Fetched result data keys: {list(fetch_result.keys())}")
                logger.debug(f"[{self.name}] Fetched result data: {str(fetch_result)[:100]}")

            if "data" not in fetch_result:
                raise ValueError("No data found in fetched result for recipe extraction")
            
            # Extract recipe using AI provider
            fetch_data_processed = fetch_result.get("data")
            ia_response: ChatCompletionResult[Recipe] = await self.ai_chat_client.extract_recipe_data(fetch_data_processed)

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
            logger.error(f"[{self.name}] Full stack trace: {traceback.format_exc()}")
            # Fallback to basic parsing
            return {
                "recipe": Recipe.default(),
                "message": f"Failed in extracting recipe",
            }

    async def _scrape_grocery_product(self, ingredient: Ingredient, store: StoreConfig) -> dict:
        """Scrape grocery product for an ingredient from a specific store."""
        # Fetch search page content
        logger.info((f"[{self.name}] Searching products", {
            "store_id": store.store_id,
            "ingredient": ingredient.name,
            "scraper_type": store.search_type
        }))

        # Use web scraper to fetch and process content
        scraper = ScraperFactory.create_scraper(store)
        fetch_result = await scraper.query_products(ingredient.name, store)

        if "data" not in fetch_result:
            raise ValueError("No data found in fetched result for ingredient extraction")
        
        # Store the fetched results
        results = fetch_result.get("data", [])
        
        if metadata := store.get_search_metadata():
            results["metadata"] = metadata

        return results

    async def search_grocery_products_intelligently(self, ingredient: Ingredient, stores: list[StoreConfig] = []) -> dict:
        """Search grocery stores for deals on ingredients using AI."""
        logger.info(f"[{self.name}] Searching {ingredient.name} in {stores} stores using AI")

        try:
            # Fetch the products search results
            store_fetch_results = {}

            # Iterate over stores to fetch search results
            for store in stores:
                try:
                    # Save fetch results per store
                    store_fetch_results[store.store_id] = await self._scrape_grocery_product(ingredient, store)
                except Exception as e:
                    logger.error(f"[{self.name}] Error searching products in store {store.name}: {e}")
                    continue

            # # Search for best match products using AI provider
            # fetch_data_processed = []
            # for fetch in store_fetch_results.values():
            #     if fetch.get("data"):
            #         fetch_data_processed.extend(fetch.get("data"))


            # Iterate over store fetch results to get best match products
            best_product_per_store = {}
            for store_id, store_fetch_results in store_fetch_results.items():
                try:
                     # Use AI to find the best match products
                    ia_response_best_product: ChatCompletionResult[Product] = await self.ai_chat_client.search_best_match_products(ingredient, store_fetch_results)
                    product = ia_response_best_product.content if isinstance(ia_response_best_product.content, Product) else Product(**ia_response_best_product.content)
                    best_product_per_store[store_id] = product
                except Exception as e:
                    logger.error(f"[{self.name}] Error awaiting fetch for store {store_id}: {e}")

            # Use AI to find the best match products
            # If there is only one store, set the best product as the shopping item directly
            ia_response: ChatCompletionResult[ShoppingListItem] = await self.ai_chat_client.choose_best_product_in_stores(ingredient, best_product_per_store)
            shoppingItem = ia_response.content if isinstance(ia_response.content, ShoppingListItem) else ShoppingListItem(**ia_response.content)
            
            return {
                "shoppingItem": shoppingItem,
                "ai_info": {
                    **(ia_response.metadata or {})
                }
            }
        except Exception as e:
            logger.error(f"[{self.name}] Error extracting products: {e}")
            logger.error(f"[{self.name}] Full stack trace: {traceback.format_exc()}")
            # Fallback to basic parsing
            return {
                "recipe": Recipe.default(),
                "message": f"Failed in getting products for ingredient",
            }
    
# Global AI service instance
ai_service = None

def get_ai_service() -> AIService:
    """Get or create the global AI service instance."""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service