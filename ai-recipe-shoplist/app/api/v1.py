"""API v1 endpoints for the AI Recipe Shoplist Crawler."""

import asyncio
import json
import logging
import pprint
import traceback
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel

from app.config.logging_config import get_logger
from app.config.store_config import StoreConfig
from app.models import (
    APIResponse,
    Ingredient,
    Product,
    QuantityUnit,
    Recipe,
    SearchStoresRequest,
    SearchStoresResponse,
    Store,
)

# Import services
from app.services.ai_service import get_ai_service
from app.services.grocery_service import grocery_service
from app.services.web_fetcher import get_web_fetcher

# Get module logger
logger = get_logger(__name__)

# Create the v1 router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

class RecipeURL(BaseModel):
    """Model for recipe URL input."""
    url: str


@api_v1_router.post("/process-recipe")
async def process_recipe(url: str = Form(...)):
    """Process a recipe URL and extract ingredients."""
    try:
        logger.info(f"Processing recipe URL: {url}")
        
        # Use AI service for intelligent extraction
        ai_service = get_ai_service()
                
        # Extract recipe using AI
        response = await ai_service.extract_recipe_intelligently(url)

        logger.info(f"Extracted recipe: {response['recipe'].title} with {len(response['recipe'].ingredients)} ingredients")

        return APIResponse(
            success=True,
            data=response,
            timestamp=datetime.now().isoformat()
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in process_recipe: {e}")
        logger.error("Stack trace:\n" + pprint.pformat(traceback.format_exc()))
        raise HTTPException(
            status_code=422, 
            detail="AI response was not valid JSON. This may indicate an AI service error. Please try again."
        )
    except Exception as e:
        logger.error(f"Error processing recipe: {e}")
        # Provide more user-friendly error messages
        if "rate limit" in str(e).lower():
            detail = "AI service rate limit exceeded. Please try again in a few moments."
        elif "timeout" in str(e).lower():
            detail = "AI service timeout. Please try again with a shorter recipe or check your connection."
        elif "authentication" in str(e).lower() or "api key" in str(e).lower():
            detail = "AI service authentication error. Please check your configuration."
        else:
            detail = f"An error occurred while processing the recipe: {str(e)}"
        
        raise HTTPException(status_code=500, detail=detail)


@api_v1_router.post("/process-recipe-ai")
async def process_recipe_full_ai(recipe_url: str = Form(...)):
    """Process a recipe URL and extract ingredients."""
    try:
        logger.info(f"Processing recipe AI URL: {recipe_url}")

        # Use AI service for intelligent extraction
        ai_service = get_ai_service()
        
        # Extract recipe using AI
        recipe = await ai_service.shopping_assistant(recipe_url)

        return APIResponse(
            success=True,
            data={
                "url": recipe_url,
                "recipe": recipe,
            },
            timestamp=datetime.now().isoformat()
        )
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in process_recipe: {e}")
        raise HTTPException(
            status_code=422, 
            detail="AI response was not valid JSON. This may indicate an AI service error. Please try again."
        )
    except Exception as e:
        logger.error(f"Error processing recipe: {e}")
        # Provide more user-friendly error messages
        if "rate limit" in str(e).lower():
            detail = "AI service rate limit exceeded. Please try again in a few moments."
        elif "timeout" in str(e).lower():
            detail = "AI service timeout. Please try again with a shorter recipe or check your connection."
        elif "authentication" in str(e).lower() or "api key" in str(e).lower():
            detail = "AI service authentication error. Please check your configuration."
        else:
            detail = f"An error occurred while processing the recipe: {str(e)}"
        
        raise HTTPException(status_code=500, detail=detail)


@api_v1_router.post("/search-stores")
async def search_stores(request: SearchStoresRequest) -> SearchStoresResponse:
    """Search grocery stores for ingredients."""
    try:
        logger.info(f"[API] Searching stores for {len(request.ingredients)} ingredients in stores: {request.stores}")

        # Search all stores (or specified stores)
        stores_names = [store.lower() for store in request.stores]
        ingredients: list[Ingredient] = request.ingredients

        stores: list[StoreConfig] = grocery_service.get_stores(stores_names)

        # Use AI to optimize product matching
        ai_service = get_ai_service()

        async def search_ingredient(ingredient: Ingredient):
            """Search for a single ingredient."""
            logger.info(f"[API] Searching stores for ingredient: {ingredient.name}")

            # Search for products using AI
            response = await ai_service.search_grocery_products_intelligently(ingredient, stores)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug((f"[API] AI search for ingredient '{ingredient.name}' - output:", response))

            # Be polite to avoid rate limits
            await asyncio.sleep(0.5)
            
            return response

        # Process ingredients concurrently using asyncio.gather
        product_results = []
        ia_stats = []
        
        # Use asyncio.gather for concurrent async operations
        responses = await asyncio.gather(
            *[search_ingredient(ingredient) for ingredient in ingredients],
            return_exceptions=True
        )

        for response in responses:
            if isinstance(response, Exception):
                logger.error(f"[API] Error in ingredient search: {response}")
                continue
                
            # Process the AI response for this ingredient
            logger.debug(f"[API] AI response for ingredient search: {response}")    

            product: Product = response.get("product")
            if product:
                product_results.append(product)
            
            ai_info = response.get("ai_info", {})
            if ai_info:
                ia_stats.append(ai_info)

        logger.info(f"[API] Completed store search for {len(ingredients)} ingredients")

        return SearchStoresResponse(
            success=True,
            stores=[Store.mapConfig(store) for store in stores],
            products=product_results,
            ia_stats=ia_stats,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"[API] Error occurred while searching stores: {e}")
        logger.error("Stack trace:\n" + pprint.pformat(traceback.format_exc()))
        # Provide more user-friendly error messages
        if "rate limit" in str(e).lower():
            detail = "AI service rate limit exceeded. Please try again in a few moments."
        elif "timeout" in str(e).lower():
            detail = "AI service timeout. Please try again."
        elif "authentication" in str(e).lower() or "api key" in str(e).lower():
            detail = "AI service authentication error. Please check your configuration."
        else:
            detail = f"An error occurred while searching stores: {str(e)}"
        
        raise HTTPException(status_code=500, detail=detail)


@api_v1_router.post("/fetcher")
async def get_fetcher_content(recipe_url: str = Form(...)):
    """Get web fetcher content."""

    web_fetcher = get_web_fetcher()
    fetch_result = await web_fetcher.fetch_html_content(recipe_url, clean_html=True)

    return APIResponse(
        success=True,
        data={
            "fetch_result": {k: v for k, v in fetch_result.items() if k != "content"}
        },
        timestamp=datetime.now().isoformat()
    )


@api_v1_router.get("/fetcher-stats")
async def get_fetcher_stats():
    """Get web fetcher cache statistics."""
    web_fetcher = get_web_fetcher()
    stats = web_fetcher.get_cache_stats()

    return APIResponse(
        success=True,
        data={
            "cache_stats": stats,
            "settings": {
                "timeout": web_fetcher.timeout,
                "max_content_size": web_fetcher.max_content_size,
                "cache_ttl": web_fetcher.cache_ttl,
                "tmp_folder": str(web_fetcher.tmp_folder)
            }
        },
        timestamp=datetime.now().isoformat()
    )


@api_v1_router.post("/clear-fetcher-cache")
async def clear_fetcher_cache():
    """Clear the web fetcher cache."""
    web_fetcher = get_web_fetcher()
    web_fetcher.clear_cache()
    
    return APIResponse(
        success=True,
        data={"message": "Fetcher cache cleared successfully"},
        timestamp=datetime.now().isoformat()
    )


@api_v1_router.post("/clear-content-files")
async def clear_content_files():
    """Clear saved content files."""
    web_fetcher = get_web_fetcher()
    web_fetcher.clear_cache(clear_file_cache=False, clear_content_files=True)
    
    return APIResponse(
        success=True,
        data={"message": "Content files cleared successfully"},
        timestamp=datetime.now().isoformat()
    )


@api_v1_router.get("/demo")
async def demo_recipe():
    """Demo endpoint with a sample recipe."""
    sample_url = "https://www.allrecipes.com/recipe/213742/cheesy-chicken-broccoli-casserole/"
    
    # Create a mock recipe for demo
    demo_recipe = Recipe(
        title="Cheesy Chicken Broccoli Casserole",
        url=sample_url,
        description="A delicious comfort food casserole",
        servings=6,
        prep_time="15 minutes",
        cook_time="25 minutes",
        ingredients=[
            Ingredient(name="chicken breast", quantity=2, unit=QuantityUnit.PIECE, original_text="2 chicken breasts"),
            Ingredient(name="broccoli", quantity=2, unit=QuantityUnit.CUP, original_text="2 cups broccoli florets"),
            Ingredient(name="cheddar cheese", quantity=1, unit=QuantityUnit.CUP, original_text="1 cup shredded cheddar cheese"),
            Ingredient(name="rice", quantity=1, unit=QuantityUnit.CUP, original_text="1 cup cooked rice"),
            Ingredient(name="cream of mushroom soup", quantity=1, unit=QuantityUnit.CAN, original_text="1 can cream of mushroom soup")
        ],
        instructions=[
            "Preheat oven to 350°F",
            "Cook chicken and broccoli",
            "Mix all ingredients in casserole dish",
            "Bake for 25 minutes until bubbly"
        ]
    )
    
    return APIResponse(
        success=True,
        data={
            "recipe": demo_recipe.dict(),
            "message": "Demo recipe loaded. Use /api/v1/optimize-shopping to continue.",
            "next_step": f"/api/v1/optimize-shopping (POST with recipe_url={sample_url})"
        },
        timestamp=datetime.now().isoformat()
    )