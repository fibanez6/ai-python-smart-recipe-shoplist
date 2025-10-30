"""Data models for the recipe shoplist application."""

from enum import Enum
from typing import Any, Optional

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
    name: str = Field(..., description="Normalised name of the ingredient without adjectives")
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
        name_str = f"{self.name}"
        qty_str = f": {self.quantity} " if self.quantity is not None else "1 "
        unit_str = f"{self.unit.value} " if self.unit is not None else "unit "
        brand_str = f" (Preference brand: {self.brand_preference}) " if self.brand_preference else ""
        return f"{name_str}{qty_str}{unit_str}{brand_str}"

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
            title="Recipe Title",
            url="http://example.com/recipe",
            ingredients=[],
            instructions=[]
        )

class Product(BaseModel):
    """Represents a grocery store product."""
    name: str = Field(..., description="Full product name from the store")
    ingredient: str = Field(..., description="Associated ingredient name")
    price: float = Field(..., description="Product price")
    store: str = Field(..., description="Store name")
    url: Optional[str] = Field(None, description="Product URL")
    image_url: Optional[str] = Field(None, description="Product image URL")
    brand: Optional[str] = Field(None, description="Product brand")
    size: Optional[str] = Field(None, description="Product size/weight")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    availability: Optional[bool] = Field(True, description="Product availability")
    ia_reasoning: Optional[str] = Field(None, description="AI reasoning for product selection")

    @staticmethod
    def default() -> "Product":
        """Returns a default example product."""
        return Product(
            name="Example Product",
            ingredient="Example Ingredient",
            price=0.0,
            store="Example Store"
        )

    def display(self) -> dict:
        """Return a dict with only selected fields."""
        return {
            "name": self.name,
            "price": self.price,
            "url": self.url,
            "image_url": self.image_url,
            "brand": self.brand,
            "unit_price": self.unit_price,
        }

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

class StoreSearchResult(BaseModel):
    """Result from searching a store for an ingredient."""
    ingredient_name: str = Field(..., description="Searched ingredient name")
    store_name: str = Field(..., description="Store that was searched")
    products: list[Product] = Field(default_factory=list, description="Found products")
    search_time: Optional[float] = Field(None, description="Search duration in seconds")


class ShoppingListItem(BaseModel):
    """An item in the shopping list with selected product."""
    ingredient: Ingredient = Field(..., description="Original ingredient")
    selected_product: Optional[Product] = Field(None, description="Selected product")
    quantity_needed: float = Field(..., description="Quantity needed for recipe")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")
    store_options: Optional[dict[str, Product]] = Field(None, description="Available products from different stores")


class OptimizationResult(BaseModel):
    """Result of price optimization across stores."""
    items: list[ShoppingListItem] = Field(..., description="Optimized shopping list")
    total_cost: float = Field(..., description="Total estimated cost")
    stores_breakdown: dict[str, float] = Field(..., description="Cost per store")
    savings: Optional[float] = Field(None, description="Savings vs. single store")


class Bill(BaseModel):
    """Generated shopping bill."""
    id: str = Field(..., description="Unique bill identifier")
    recipe_title: str = Field(..., description="Recipe name")
    generated_at: str = Field(..., description="Generation timestamp")
    items: list[ShoppingListItem] = Field(..., description="Bill items")
    subtotal: float = Field(..., description="Subtotal before tax")
    tax_rate: float = Field(0.1, description="Tax rate")
    tax_amount: float = Field(..., description="Tax amount")
    total: float = Field(..., description="Total amount")
    stores: list[str] = Field(..., description="Stores to visit")
    stores_breakdown: Optional[dict[str, float]] = Field(None, description="Cost breakdown by store")


class ProcessRecipeRequest(BaseModel):
    """Request to process a recipe URL."""
    url: str = Field(..., description="Recipe URL to process")
    servings_adjustment: Optional[int] = Field(None, description="Adjust servings")


class GenerateBillRequest(BaseModel):
    """Request to generate a shopping bill."""
    recipe: Recipe = Field(..., description="Recipe information")
    optimization_result: OptimizationResult = Field(..., description="Optimization result")
    format: str = Field("pdf", description="Output format: pdf or html")


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: str = Field(..., description="Response timestamp")