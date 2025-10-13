from urllib import request
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import json
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .services import recipe_service
import os

# Get stage from environment variable (set by Lambda)
STAGE = os.getenv("STAGE", "")
PREFIX = f"/{STAGE}" if STAGE else ""

app = FastAPI(title="Recipe Shoplist Crawler")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # return templates.TemplateResponse("index.html", {"request": request, "base_url": PREFIX})
    return RedirectResponse(url=f"{PREFIX}/index.html")

@app.get("/index.html", response_class=HTMLResponse)
async def index_html(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "base_url": PREFIX})


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, url: str = Form(...)):
    print(f"[main] received URL to process: {url}")
    # Kick off pipeline
    result = await recipe_service.process_recipe_url(url)
    # pretty-print result as JSON for easier reading in logs
    try:
        pretty = json.dumps(result, indent=2, ensure_ascii=False)
    except Exception:
        # fallback to str() if any non-serializable objects are present
        pretty = str(result)
    print(f"[main] result=\n{pretty}")
    print(f"[main] completed processing for {url}")
    return templates.TemplateResponse("results.html", {"request": request, "result": result, "base_url": PREFIX})

@app.get("/sample-recipe")
async def sample_recipe(request: Request):
    # Redirect to the static sample page served under /static
    return RedirectResponse(url=f"{PREFIX}/static/sample-recipe.html")
