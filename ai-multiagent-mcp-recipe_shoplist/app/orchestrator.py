import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from agents.recipe_agent import RecipeReaderAgent
from agents.grocery_agent_providers import GrocerySearchAgent
from agents.selector_agent import BestMatchAgent
from agents.output_agent import OutputAgent
from agents.cache_agent import CacheAgent
from models import Ingredient, Match

app = FastAPI()

recipe_agent = RecipeReaderAgent()
grocery_agent = GrocerySearchAgent()
selector = BestMatchAgent()
output = OutputAgent()
cache = CacheAgent(db_path=os.getenv('CACHE_DB', './data/cache.db'))

class ProcessRequest(BaseModel):
    recipe_url: str

@app.post('/process-recipe')
async def process_recipe(body: ProcessRequest):
    try:
        ingredients = await recipe_agent.extract(body.recipe_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting recipe: {e}")

    async def handle_ingredient(ing: Ingredient):
        key = cache.make_key(ing)
        cached = await cache.get(key)
        if cached:
            # cached is a list of product dicts; convert to models.Product if needed
            products = [p for p in cached]
        else:
            products = await grocery_agent.search(ing)
            # store as serializable dicts
            await cache.set(key, [p.dict() for p in products])
        chosen = selector.choose(ing, products)
        return Match(ingredient=ing, chosen=chosen, alternatives=products)

    tasks = [handle_ingredient(ing) for ing in ingredients]
    results = await asyncio.gather(*tasks)

    html = output.render_html(results)
    text = output.render_text(results)

    return {'html': html, 'text': text, 'matches': [r.dict() for r in results]}

# Para ejecutar:
# export SPOONACULAR_KEY=...
# export SERPAPI_KEY=...
# python -m uvicorn orchestrator:app --reload