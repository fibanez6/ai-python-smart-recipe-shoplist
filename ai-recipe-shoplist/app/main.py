"""Main FastAPI application for the AI Recipe Shoplist Crawler."""

import asyncio
import json
import logging
import os
import pprint
import traceback
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config.store_config import StoreConfig

# Load environment variables
load_dotenv()

# Setup logging first
from app.config.logging_config import setup_logging
from app.config.pydantic_config import (
    AI_SERVICE_SETTINGS,
    LOG_SETTINGS,
    SERVER_SETTINGS,
    get_config_summary,
)

# Initialize logging with file support if needed
logger = setup_logging(
    file_logging_enabled=LOG_SETTINGS.file_enabled,
    log_file=LOG_SETTINGS.file_path
)

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
from app.services.store_crawler import SimpleStoreCrawler
from app.services.web_fetcher import get_web_fetcher

# Initialize global variables
recipe_cache = {}
store_crawler = SimpleStoreCrawler()

# Try to import Jinja2Templates, make it optional
try:
    templates_path = os.path.join(os.path.dirname(__file__), "templates")
    templates = Jinja2Templates(directory=templates_path)
except ImportError:
    templates = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for FastAPI startup and shutdown events."""
    logger.info("[App] Starting AI Recipe Shoplist")

    logger.info("[App] Initializing Store Crawler...")
    logger.debug(get_config_summary())
    
    # Test AI service initialization
    try:
        ai_service = get_ai_service()
        logger.info(f"[App] AI service initialized with provider: {ai_service.provider_name}")
    except Exception as e:
        logger.info(f"[App] Warning: AI service initialization failed: {e}")
    
    logger.info("[App] Application startup complete")
    yield

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="AI Recipe Shoplist Crawler",
    description="AI-powered recipe ingredient crawler with grocery store price optimization",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Startup logic moved to lifespan context manager above.

class RecipeURL(BaseModel):
    """Model for recipe URL input."""
    url: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>AI Recipe Shoplist</title></head>
            <body>
                <h1>AI Recipe Shoplist</h1>
                <p>API is running! Visit <a href="/api/docs">/api/docs</a> for API documentation.</p>
                <form action="/api/process-recipe" method="post">
                    <input type="url" name="url" placeholder="Enter recipe URL" required style="width: 400px; padding: 10px;">
                    <button type="submit" style="padding: 10px 20px;">Process Recipe</button>
                </form>
            </body>
        </html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "ai_provider": AI_SERVICE_SETTINGS.provider
    }


@app.post("/api/process-recipe")
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

@app.post("/api/process-recipe-ai")
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
        logger.error("Stack trace:\n" + pprint.pformat(traceback.format_exc()))
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

@app.post("/api/search-stores")
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

        product_results = []
        ia_stats = []
        for ingredient in ingredients:
            logger.info(f"[API] Searching stores for ingredient: {ingredient.name}")

            # Search for products using AI
            response = await ai_service.search_grocery_products_intelligently(ingredient, stores)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug((f"[API] AI search for ingredient '{ingredient.name}' - output:", response))

            # Process the AI response for this ingredient
            product: Product = response.get("product")
            if product:
                product_results.append(product)
            
            ai_info = response.get("ai_info", {})
            if ai_info:
                ia_stats.append(ai_info)

            # Be polite to avoid rate limits
            await asyncio.sleep(0.5)

        logger.info(f"[API] Completed store search for {len(ingredients)} ingredients")

        # if logger.isEnabledFor(logging.DEBUG):
        #     logger.debug(stores)
        #     logger.debug(product_results)

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

# @app.post("/api/optimize-shopping")
# async def optimize_shopping(recipe_url: str = Form(...)):
#     """Complete end-to-end optimization: recipe -> ingredients -> stores -> optimization."""
#     try:
#         logger.info(f"Starting complete optimization for: {recipe_url}")
        
#         # Step 1: Get or process recipe
#         if recipe_url in recipe_cache:
#             recipe = recipe_cache[recipe_url]
#             logger.info("Using cached recipe")
#         else:
#             web_fetcher = get_web_fetcher()
#             ai_service = get_ai_service()
            
#             # Fetch recipe content using the web fetcher service
#             fetch_result = await web_fetcher.fetch_html(recipe_url, clean_html=True)
            
#             # Log fetch details
#             if logger.isEnabledFor(logging.DEBUG):
#                 logger.debug(f"Fetched content from cache: {fetch_result.get('from_cache', False)}")
#                 logger.debug(f"Content size: {fetch_result.get('size', 0)} bytes")
#                 logger.debug(f"Final URL: {fetch_result.get('url', recipe_url)}")
            
#             # Use cleaned content for AI processing
#             html_content = fetch_result.get("cleaned_content", fetch_result["content"])

#             recipe = await ai_service.extract_recipe_intelligently(html_content, recipe_url)
#             recipe_cache[recipe_url] = recipe
        
#         if not recipe.ingredients:
#             raise HTTPException(status_code=400, detail="No ingredients found in recipe")
        
#         # Step 2: Search stores
#         store_results = await store_crawler.search_all_stores(recipe.ingredients)
        
#         # Step 3: Optimize shopping
#         optimization_result = await price_optimizer.optimize_shopping(
#             recipe.ingredients, store_results
#         )
        
#         # Cache optimization result
#         optimization_cache[recipe_url] = optimization_result
        
#         logger.info(f"Optimization complete. Total cost: ${optimization_result.total_cost:.2f}")
        
#         return APIResponse(
#             success=True,
#             data={
#                 "recipe": recipe.dict(),
#                 "optimization": optimization_result.dict(),
#                 "summary": {
#                     "total_cost": optimization_result.total_cost,
#                     "stores_count": len(optimization_result.stores_breakdown),
#                     "items_found": len([item for item in optimization_result.items if item.selected_product]),
#                     "items_total": len(optimization_result.items),
#                     "savings": optimization_result.savings or 0
#                 }
#             },
#             timestamp=datetime.now().isoformat()
#         )
        
#     except Exception as e:
#         logger.error(f"Error in complete optimization: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/generate-bill")
# async def generate_bill(recipe_url: str = Form(...), format: str = Form("pdf")):
#     """Generate a shopping bill."""
#     try:
#         logger.info(f"[API]Generating {format} bill for: {recipe_url}")
        
#         # Get cached recipe and optimization
#         if recipe_url not in recipe_cache:
#             raise HTTPException(status_code=400, detail="Recipe not found. Process recipe first.")
        
#         if recipe_url not in optimization_cache:
#             raise HTTPException(status_code=400, detail="Optimization not found. Run optimization first.")
        
#         recipe = recipe_cache[recipe_url]
#         optimization_result = optimization_cache[recipe_url]
        
#         # Generate bill
#         bill = await bill_generator.generate_bill(recipe, optimization_result, format)
        
#         # Get file path
#         file_path = bill_generator.get_bill_path(bill.id, format)
        
#         if not file_path:
#             raise HTTPException(status_code=500, detail="Bill generation failed")
        
#         return APIResponse(
#             success=True,
#             data={
#                 "bill": bill.dict(),
#                 "file_path": file_path,
#                 "download_url": f"/api/download-bill/{bill.id}?format={format}",
#                 "summary": await bill_generator.generate_receipt_summary(bill)
#             },
#             timestamp=datetime.now().isoformat()
#         )
        
#     except Exception as e:
#         logger.info(f"[API]Error generating bill: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/download-bill/{bill_id}")
# async def download_bill(bill_id: str, format: str = "pdf"):
#     """Download a generated bill."""
#     file_path = bill_generator.get_bill_path(bill_id, format)
    
#     if not file_path or not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="Bill not found")
    
#     filename = f"shopping_bill_{bill_id}.{format}"
    
#     return FileResponse(
#         path=file_path,
#         filename=filename,
#         media_type="application/octet-stream"
#     )

# @app.get("/api/suggest-alternatives/{ingredient_name}")
# async def suggest_alternatives(ingredient_name: str):
#     """Get AI-suggested alternatives for an ingredient."""
#     try:
#         ai_service = get_ai_service()
        
#         # Create a temporary ingredient object
#         ingredient = Ingredient(name=ingredient_name, original_text=ingredient_name)
        
#         alternatives = await ai_service.suggest_alternatives(ingredient)
        
#         return APIResponse(
#             success=True,
#             data={
#                 "ingredient": ingredient_name,
#                 "alternatives": alternatives
#             },
#             timestamp=datetime.now().isoformat()
#         )
        
#     except Exception as e:
#         logger.info(f"[API]Error suggesting alternatives: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fetcher")
async def get_fetcher_content(recipe_url: str = Form(...)):
    """Get web fetcher content."""

    web_fetcher = get_web_fetcher()
    fetch_result = await web_fetcher.fetch_html(recipe_url, clean_html=True)

    return APIResponse(
        success=True,
        data={
            "fetch_result": {k: v for k, v in fetch_result.items() if k != "content"}
        },
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/fetcher-stats")
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

@app.post("/api/clear-fetcher-cache")
async def clear_fetcher_cache():
    """Clear the web fetcher cache."""
    web_fetcher = get_web_fetcher()
    web_fetcher.clear_cache()
    
    return APIResponse(
        success=True,
        data={"message": "Fetcher cache cleared successfully"},
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/clear-content-files")
async def clear_content_files():
    """Clear saved content files."""
    web_fetcher = get_web_fetcher()
    web_fetcher.clear_cache(clear_file_cache=False, clear_content_files=True)
    
    return APIResponse(
        success=True,
        data={"message": "Content files cleared successfully"},
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/stores")
async def get_available_stores():
    """Get list of available grocery stores with detailed information."""
    stores = store_crawler.get_available_stores()
    
    # Create basic store info since get_all_stores_info() doesn't exist
    store_info = {
        store: {
            "name": store.title(),
            "display_name": store.title(),
            "available": True,
            "type": "grocery"
        } for store in stores
    }
    
    return APIResponse(
        success=True,
        data={
            "stores": stores,
            "store_details": store_info,
            "count": len(stores),
            "region": "AU"  # Default region since no region property exists
        },
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/stores/{store_id}")
async def get_store_details(store_id: str):
    """Get detailed information for a specific store."""
    available_stores = store_crawler.get_available_stores()
    
    if store_id not in available_stores:
        raise HTTPException(status_code=404, detail=f"Store '{store_id}' not found")
    
    # Create basic store info since get_store_info() doesn't exist
    store_info = {
        "id": store_id,
        "name": store_id.title(),
        "display_name": store_id.title(),
        "available": True,
        "type": "grocery",
        "region": "AU"
    }
    
    return APIResponse(
        success=True,
        data={
            "store": store_info,
            "sample_urls": {
                "search_tomato": f"https://{store_id}.com.au/search?q=tomato",
                "product_example": f"https://{store_id}.com.au/product/example-product-123"
            }
        },
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/demo")
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
    
    # Cache demo recipe
    recipe_cache[sample_url] = demo_recipe
    
    return APIResponse(
        success=True,
        data={
            "recipe": demo_recipe.dict(),
            "message": "Demo recipe loaded. Use /api/optimize-shopping to continue.",
            "next_step": f"/api/optimize-shopping (POST with recipe_url={sample_url})"
        },
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    port = SERVER_SETTINGS.port
    host = SERVER_SETTINGS.host

    print(f"Starting server on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )