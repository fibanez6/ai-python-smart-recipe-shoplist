"""Data models for the recipe shoplist application."""

from enum import Enum
from typing import Any, Generic, Optional, TypeVar

import rich
from pydantic import BaseModel, Field


class QuantityUnit(str, Enum):
    """Standard quantity units for ingredients."""
    # Volume
    CUP = "cup"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"
    LITER = "l"
    MILLILITER = "ml"
    FLUID_OUNCE = "fl oz"
    
    # Weight
    KILOGRAM = "kg"
    GRAM = "g"
    POUND = "lb"
    OUNCE = "oz"
    
    # Count
    PIECE = "piece"
    ITEM = "item"
    CLOVE = "clove"
    SLICE = "slice"
    UNIT = "unit"
    
    # Containers
    CAN = "can"
    JAR = "jar"
    BOTTLE = "bottle"
    PACKAGE = "package"
    PACK = "pack"
    BAG = "bag"
    BOX = "box"
    CONTAINER = "container"
    
    # Special
    PINCH = "pinch"
    DASH = "dash"
    TO_TASTE = "to taste"

    DEFAULT = UNIT

class Ingredient(BaseModel):
    """Represents a recipe ingredient with quantity and unit."""
    name: str = Field(..., description="Normalised australian name of the ingredient without adjectives")
    quantity: Optional[float] = Field(None, description="Amount needed")
    unit: Optional[QuantityUnit] = Field(QuantityUnit.DEFAULT, description="Unit of measurement")
    original_text: str = Field(..., description="Original ingredient text from recipe")
    optional: bool = Field(False, description="Whether ingredient is optional")
    category: Optional[str] = Field(None, description="Ingredient category (e.g., dairy, produce)")
    alternatives: Optional[list[str]] = Field(None, description="List of alternative ingredient names")
    notes: Optional[str] = Field(None, description="Additional short note about the ingredient")
    quality: Optional[str] = Field(None, description="Quality descriptor (e.g., organic, fresh)")
    brand_preference: Optional[str] = Field(None, description="Preferred brand for the ingredient")

    def __str__(self) -> str:
        name_str = self.name
        qty_str = f": {self.quantity or 1} "
        unit_str = f"{self.unit.value} "
        brand_str = f"(Preference brand: {self.brand_preference}) " if self.brand_preference else ""
        category_str = f"({self.category})" if self.category else ""
        alternatives_str = f" Alternatives: {', '.join(self.alternatives)}." if self.alternatives else ""
        return f"{name_str}{qty_str}{unit_str}{brand_str}{category_str}{alternatives_str}".strip()
    
class Recipe(BaseModel):
    """Represents a parsed recipe."""
    title: str = Field(..., description="Recipe title")
    url: str = Field(..., description="Source URL")
    description: Optional[str] = Field(None, description="Recipe brief description")
    servings: Optional[int] = Field(None, description="Number of servings")
    prep_time: Optional[str] = Field(None, description="Preparation time")
    cook_time: Optional[str] = Field(None, description="Cooking time")
    ingredients: list[Ingredient] = Field(..., description="List of ingredients")
    instructions: list[str] = Field(default_factory=list, description="Cooking instructions")
    image_url: Optional[str] = Field(None, description="Recipe image URL")

    @staticmethod
    def default() -> "Recipe":
        """Returns a default example recipe."""
        return Recipe(
            title="Example Recipe",
            url="http://example.com/recipe",
            ingredients=[],
            instructions=[]
        )

class Product(BaseModel):
    """Represents a grocery store product."""
    name: str = Field(..., description="Full product name from the store")
    ingredient: str = Field(..., description="Associated ingredient name")
    price: float = Field(..., description="Product price")
    price_unit : str = Field(..., description="Price unit, e.g., 'per kg', 'per item'")
    store: str = Field(..., description="Store name")
    quantity: int = Field(1, description="Number of units")
    url: Optional[str] = Field(None, description="Product URL")
    image_url: Optional[str] = Field(None, description="Product image URL")
    brand: Optional[str] = Field(None, description="Product brand")
    size: Optional[str] = Field(None, description="Product size/weight")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    availability: Optional[bool] = Field(True, description="Product availability")
    ia_reasoning: Optional[str] = Field(None, description="Short AI reasoning for product selection")

    @staticmethod
    def default() -> "Product":
        """Returns a default example product."""
        return Product(
            name="Example Product",
            ingredient="Example Ingredient",
            price=0.0,
            store="Example Store"
        )

class Store(BaseModel):
    """Represents a grocery store."""
    name: str = Field(..., description="Store name")
    display_name: Optional[str] = Field(None, description="Store display name")
    region: Optional[str] = Field(None, description="Store region/country")
    base_url: Optional[str] = Field(None, description="Store base URL")

    @staticmethod
    def mapConfig(name: str, display_name: str, region: str, base_url: str) -> "Store":
        """Map to store config."""
        return Store (
            name = name,
            display_name = display_name,
            region = region,
            base_url = base_url
        )

class ShopphingCart(BaseModel):
    """Represents a shopping cart with products."""
    products: list[Product] = Field(..., description="List of products in the cart")
    total_price: float = Field(..., description="Total price of the cart")
    store: str = Field(..., description="Store name")

    @staticmethod
    def default() -> "ShopphingCart":
        """Returns a default example shopping cart."""
        return ShopphingCart(
            products=[],
            total_price=0.0,
            store="Example Store"
        )

class SearchStoresRequest(BaseModel):
    """Request to search stores for ingredients."""
    ingredients: list[Ingredient] = Field(..., description="Ingredients to search")
    stores: Optional[list[str]] = Field(None, description="Specific stores to search")

# class StoreSearchResult(BaseModel):
#     """Result from searching a store for an ingredient."""
#     ingredient_name: str = Field(..., description="Searched ingredient name")
#     store_name: str = Field(..., description="Store that was searched")
#     products: list[Product] = Field(default_factory=list, description="Found products")
#     search_time: Optional[float] = Field(None, description="Search duration in seconds")

class ShoppingListItem(BaseModel):
    """An item in the shopping list with selected product."""
    ingredient: Ingredient = Field(..., description="Original ingredient")
    selected_product: Optional[Product] = Field(None, description="Selected product by best price and matched criteria")
    quantity: float = Field(..., description="Number of units product needed to match ingredient")
    total_cost: Optional[float] = Field(None, description="Total cost is based on quantity plus product price")
    store_options: Optional[dict[str, Product]] = Field(None, description="Available products from different stores, only one per store")

# class OptimizationResult(BaseModel):
#     """Result of price optimization across stores."""
#     items: list[ShoppingListItem] = Field(..., description="Optimized shopping list")
#     total_cost: float = Field(..., description="Total estimated cost")
#     stores_breakdown: dict[str, float] = Field(..., description="Cost per store")
#     savings: Optional[float] = Field(None, description="Savings vs. single store")

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: str = Field(..., description="Response timestamp")

T = TypeVar('T')
class ChatCompletionResult(BaseModel, Generic[T]):
    """Response from an AI service, including raw content, parsed result, refusal info, and stats."""
    success: bool = Field(..., description="Whether the AI call was successful")
    content: Optional[T] = Field(..., description="Content returned by the AI service")
    refusal: Optional[Any] = Field(None, description="Refusal information if applicable")
    metadata: Optional[dict] = Field(None, description="Additional statistics or metadata")

class SearchStoresResponse(BaseModel):
    """Response for searching stores for products."""
    success: bool = Field(..., description="Whether the search was successful")
    stores: list[Store] = Field(default_factory=list, description="Stores that were searched")
    shopping_list_items: list[ShoppingListItem] = Field(default_factory=list, description="Shopping list items found")
    ia_stats: Optional[list[dict]] = Field(default_factory=list, description="Intelligent Assistant stats")
    timestamp: str = Field(..., description="Response timestamp")


class ChatCompletionRequest(BaseModel):
    """Request for AI chat completion calls."""
    system_message: Optional[str] = Field(None, description="System message for context", examples={"You are a funny sage assistant."})
    prompt: str = Field(..., description="The prompt to send to the AI service", examples={"if the sky is glue and apples are red, what colour is 'el caballo blanco de Franco'?"})
    # model: Optional[str] = Field(None, description="AI model to use")
    # temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    # max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    # response_format: Optional[str] = Field(None, description="Expected response format")
