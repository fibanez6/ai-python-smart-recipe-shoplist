import os
import httpx
from typing import List
from models import Product, Ingredient

SPOONACULAR_KEY = os.getenv('SPOONACULAR_KEY')
SERPAPI_KEY = os.getenv('SERPAPI_KEY')

class SpoonacularProvider:
    BASE = 'https://api.spoonacular.com'
    def __init__(self, api_key: str = None):
        self.key = api_key or SPOONACULAR_KEY

    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        if not self.key:
            return []
        url = f"{self.BASE}/food/products/search"
        params = {"query": query, "number": limit, "apiKey": self.key}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, params=params)
            if r.status_code != 200:
                return []
            data = r.json()
        items = []
        for it in data.get('products', []):
            price = None
            # spoonacular may not have price per product consistently
            try:
                price = float(it.get('price', 0))
            except Exception:
                price = None
            items.append(Product(
                id=str(it.get('id')),
                name=it.get('title'),
                price=price,
                quantity=None,
                unit=None,
                url=it.get('link') or it.get('sourceUrl'),
                vendor=it.get('brand') or 'Spoonacular'
            ))
        return items

class SerpApiProvider:
    BASE = 'https://serpapi.com/search.json'
    def __init__(self, api_key: str = None, engine: str = 'walmart'):
        self.key = api_key or SERPAPI_KEY
        self.engine = engine

    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        if not self.key:
            return []
        params = {"engine": self.engine, "q": query, "api_key": self.key}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(self.BASE, params=params)
            if r.status_code != 200:
                return []
            js = r.json()
        products = []
        for item in js.get('organic_results', [])[:limit]:
            title = item.get('title') or item.get('product_title')
            link = item.get('link')
            price = None
            try:
                if 'pricing' in item and item['pricing'].get('price'):
                    price = float(item['pricing']['price'].replace('$','').replace(',',''))
            except Exception:
                price = None
            products.append(Product(
                id=item.get('position') or title,
                name=title,
                price=price,
                quantity=None,
                unit=None,
                url=link,
                vendor=self.engine
            ))
        return products


class GrocerySearchAgent:
    def __init__(self, providers: List = None):
        self.providers = providers or [SpoonacularProvider(), SerpApiProvider()]

    async def search(self, ingredient: Ingredient) -> List[Product]:
        query = ingredient.name
        merged = []
        for prov in self.providers:
            try:
                res = await prov.search_products(query)
            except Exception:
                res = []
            if res:
                merged.extend(res)
            if len(merged) >= 6:
                break
        unique = {}
        for p in merged:
            key = (p.name or '').lower()
            if key not in unique:
                unique[key] = p
        return list(unique.values())