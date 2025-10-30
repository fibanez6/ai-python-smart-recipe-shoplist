"""Stub AI Provider for testing and development.

This provider serves mock/stub responses instead of making real AI API calls.
Useful for development, testing, and demonstrations without API costs.
"""

import json
import random
from pathlib import Path
from typing import Any

from ..config.logging_config import get_logger
from .base_provider import BaseAIProvider

# Get module logger
logger = get_logger(__name__)


class StubProvider(BaseAIProvider):
    """Stub AI provider that serves mock responses for development and testing."""

    def __init__(self, STUB_RESPONSES_PATH: str = "stub_responses"):
        """
        Initialize the stub provider.
        
        Args:
            STUB_RESPONSES_PATH: Path to the mock responses directory
        """
        logger.debug("Initializing Stub provider...")
        
        self.base_path = Path(STUB_RESPONSES_PATH)
        self.response_cache = {}
        self._load_responses()
        
        logger.info(f"Stub provider initialized - Mock responses path: {self.base_path}")
        logger.info(f"Loaded {len(self.response_cache)} response categories")
    
    def _load_responses(self):
        """Load all mock responses into memory."""
        if not self.base_path.exists():
            logger.warning(f"Mock responses directory not found: {self.base_path}")
            return
        
        for category_dir in self.base_path.iterdir():
            if category_dir.is_dir():
                category_name = category_dir.name
                self.response_cache[category_name] = {}
                
                for response_file in category_dir.glob("*.json"):
                    try:
                        with open(response_file, 'r', encoding='utf-8') as f:
                            response_data = json.load(f)
                            response_name = response_file.stem
                            self.response_cache[category_name][response_name] = response_data
                            logger.debug(f"Loaded mock response: {category_name}/{response_name}")
                    except Exception as e:
                        logger.error(f"Error loading mock response {response_file}: {e}")
    
    async def complete_chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Complete a chat conversation using stub responses."""
        logger.debug(f"Stub chat completion - Messages: {len(messages)}")
        
        # Extract the last user message for context
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                break
        
        # Return contextual stub responses
        if "recipe" in user_message or "ingredient" in user_message:
            return json.dumps(self._get_recipe_stub_response())
        elif "shop" in user_message or "store" in user_message:
            return json.dumps(self._get_shopping_stub_response())
        elif "bill" in user_message or "cost" in user_message:
            return json.dumps(self._get_bill_stub_response())
        else:
            return json.dumps({"response": "This is a stub response for development/testing"})
    
    async def extract_recipe_data(self, html_content: str, url: str) -> dict[str, Any]:
        """Extract structured recipe data using stub responses."""
        logger.debug(f"Stub recipe extraction - URL: {url}")
        
        responses = self.response_cache.get("recipe_analysis", {})
        
        if not responses:
            return self._get_default_recipe_analysis()
        
        # Try to match based on URL or content keywords
        content_lower = html_content.lower()
        url_lower = url.lower()
        
        # Check for specific recipes
        if "carbonara" in content_lower or "carbonara" in url_lower or "spaghetti" in content_lower:
            if "spaghetti_carbonara" in responses:
                return responses["spaghetti_carbonara"]["output"]
        
        if "stir fry" in content_lower or "chicken" in content_lower:
            if "chicken_stir_fry" in responses:
                return responses["chicken_stir_fry"]["output"]
        
        # Return a random response if no specific match
        if responses:
            random_response = random.choice(list(responses.values()))
            return random_response["output"]
        
        return self._get_default_recipe_analysis()
    
    async def match_products(self, ingredient: str, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Match and rank products using stub responses."""
        logger.debug(f"Stub product matching - Ingredient: {ingredient}, Products: {len(products)}")
        
        responses = self.response_cache.get("bill_generation", {})
        
        if not responses:
            return self._get_default_product_matches(ingredient, products)
        
        # Try to match based on ingredient
        ingredient_lower = ingredient.lower()
        
        if "spaghetti" in ingredient_lower or "pasta" in ingredient_lower:
            if "carbonara_shopping_bill" in responses:
                return responses["carbonara_shopping_bill"]["output"].get("product_matches", 
                                                                        self._get_default_product_matches(ingredient, products))
        
        # Return a random response if no specific match
        if responses:
            random_response = random.choice(list(responses.values()))
            return random_response["output"].get("product_matches", 
                                               self._get_default_product_matches(ingredient, products))
        
        return self._get_default_product_matches(ingredient, products)
    
    def _get_recipe_stub_response(self) -> dict[str, Any]:
        """Get a stub response for recipe-related queries."""
        return {
            "recipe_name": "Stub Recipe",
            "servings": 4,
            "ingredients": ["1 cup stub ingredient", "2 tbsp stub seasoning"],
            "instructions": ["This is a stub instruction"],
            "prep_time": "15 minutes",
            "cook_time": "20 minutes"
        }
    
    def _get_shopping_stub_response(self) -> dict[str, Any]:
        """Get a stub response for shopping-related queries."""
        return {
            "shopping_plan": {
                "stores": ["Stub Grocery Store"],
                "total_cost": 25.99,
                "estimated_time": "30 minutes"
            }
        }
    
    def _get_bill_stub_response(self) -> dict[str, Any]:
        """Get a stub response for bill-related queries."""
        return {
            "total_cost": 25.99,
            "items": [
                {"name": "Stub Item", "price": 5.99, "quantity": 1}
            ],
            "tax": 2.08,
            "final_total": 28.07
        }
    
    def _get_default_recipe_analysis(self) -> dict[str, Any]:
        """Get a default recipe analysis response when no mock data is available."""
        return {
            "title": "Stub Recipe Analysis",
            "description": "This is a stub response for development/testing",
            "servings": 4,
            "prep_time": "15 minutes",
            "cook_time": "20 minutes",
            "ingredients": [
                "1 cup stub ingredient",
                "2 tbsp stub seasoning",
                "Salt and pepper to taste"
            ],
            "instructions": [
                "1. This is a stub instruction",
                "2. Mix all ingredients together",
                "3. Cook until done"
            ],
            "image_url": None
        }
    
    def _get_default_normalized_ingredients(self, ingredients: list[str]) -> list[dict[str, Any]]:
        """Get default normalized ingredients when no mock data is available."""
        normalized = []
        for ing in ingredients:
            normalized.append({
                "name": ing.strip(),
                "quantity": 1,
                "unit": "unit",
                "original_text": ing,
                "category": "stub_category",
                "notes": "Stub normalized ingredient"
            })
        return normalized
    
    def _get_default_product_matches(self, ingredient: str, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get default product matches when no mock data is available."""
        if not products:
            return [{
                "title": f"Stub {ingredient}",
                "price": 2.99,
                "brand": "Stub Brand",
                "size": "1 unit",
                "store": "Stub Store",
                "match_score": 95,
                "url": "https://stub.example.com",
                "availability": "in_stock"
            }]
        
        # Add stub match scores to existing products
        scored_products = []
        for i, product in enumerate(products):
            scored_product = product.copy()
            scored_product["match_score"] = 100 - (i * 5)  # Decreasing scores
            scored_product["stub_note"] = "Scored by stub provider"
            scored_products.append(scored_product)
        
        return scored_products
    
    def get_available_responses(self) -> dict[str, list[str]]:
        """
        Get a list of all available mock responses.
        
        Returns:
            Dictionary mapping category names to lists of response names
        """
        available = {}
        for category, responses in self.response_cache.items():
            available[category] = list(responses.keys())
        return available
    
    def reload_responses(self):
        """Reload all mock responses from disk."""
        self.response_cache.clear()
        self._load_responses()
        logger.info("Stub provider responses reloaded")