"""Main FastAPI application for the AI Recipe Shoplist Crawler."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

# Import services
from app.services.ai_service import get_ai_service

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
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
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

# Import versioned API routers
from app.api import v1_router

# Startup logic moved to lifespan context manager above.

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
                <p>API is running! Visit <a href="/api/v1/docs">/api/v1/docs</a> for API documentation.</p>
                <form action="/api/v1/process-recipe" method="post">
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



# Include versioned API routers
app.include_router(v1_router)

# Legacy endpoints for backward compatibility (redirect to v1)
from fastapi.responses import RedirectResponse


@app.get("/api/docs")
async def redirect_legacy_docs():
    """Redirect legacy docs to v1 docs."""
    return RedirectResponse(url="/api/v1/docs", status_code=301)

@app.get("/api/redoc")
async def redirect_legacy_redoc():
    """Redirect legacy redoc to v1 redoc."""
    return RedirectResponse(url="/api/v1/redoc", status_code=301)

# Legacy API endpoint redirects
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def redirect_legacy_api(path: str, request: Request):
    """Redirect legacy API endpoints to v1."""
    # Preserve query parameters if any
    query_params = str(request.url.query)
    new_url = f"/api/v1/{path}"
    if query_params:
        new_url += f"?{query_params}"
    return RedirectResponse(url=new_url, status_code=301)

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