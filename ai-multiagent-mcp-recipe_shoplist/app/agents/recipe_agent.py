import re
from typing import List
from bs4 import BeautifulSoup
from mcp_tools.mcp_http_fetch import MCPHTTPTool
from models import Ingredient
import json

class RecipeReaderAgent:
    def __init__(self):
        self.http = MCPHTTPTool(user_agent="RecipeReader/1.0")

    async def fetch_html(self, url: str) -> str:
        return await self.http.fetch_text(url)

    def extract_ld_json(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all('script', type='application/ld+json')
        items = []
        for s in scripts:
            try:
                data = json.loads(s.string)
                # sometimes it's a list
                if isinstance(data, list):
                    for d in data:
                        items.append(d)
                else:
                    items.append(data)
            except Exception:
                continue
        return items

    def parse_ingredients_from_ld(self, ld_objects) -> List[Ingredient]:
        res = []
        for obj in ld_objects:
            recipe = None
            if isinstance(obj, dict) and obj.get('@type', '').lower() == 'recipe':
                recipe = obj
            elif isinstance(obj, dict) and obj.get('@type') == 'Recipe':
                recipe = obj
            if recipe:
                ings = recipe.get('recipeIngredient') or recipe.get('ingredients')
                if ings:
                    for it in ings:
                        res.append(self.simple_parse_ingredient(it))
        return res

    def simple_parse_ingredient(self, text: str) -> Ingredient:
        # heurística muy simple
        text = text.strip()
        m = re.match(r"^\s*([\d\/\.]+)\s*([a-zA-Z]+)?\s*(.*)$", text)
        if m:
            qty_raw, unit, rest = m.groups()
            try:
                if '/' in qty_raw:
                    a,b = qty_raw.split('/')
                    qty = float(a)/float(b)
                else:
                    qty = float(qty_raw)
            except Exception:
                qty = None
            return Ingredient(name=rest.strip(), qty=qty, unit=(unit or None), raw_text=text)
        return Ingredient(name=text, raw_text=text)

    def parse_ingredients_from_html(self, html: str) -> List[Ingredient]:
        soup = BeautifulSoup(html, 'html.parser')
        # buscar secciones que contengan la palabra "ingredient"
        possible = []
        for header in soup.find_all(['h2','h3','h4']):
            if 'ingredient' in header.get_text(strip=True).lower():
                sib = header.find_next_sibling()
                if sib and sib.name in ['ul','ol']:
                    possible.append(sib)
        items = []
        if not possible:
            # fallback: buscar cualquier li en el documento que parezca un ingrediente (heurística)
            lis = soup.find_all('li')
            for li in lis:
                text = li.get_text(strip=True)
                if len(text) > 2 and re.search(r"\d", text):
                    items.append(self.simple_parse_ingredient(text))
        else:
            for p in possible:
                for li in p.find_all('li'):
                    items.append(self.simple_parse_ingredient(li.get_text(strip=True)))
        return items

    async def extract(self, url: str) -> List[Ingredient]:
        html = await self.fetch_html(url)
        ld = self.extract_ld_json(html)
        if ld:
            res = self.parse_ingredients_from_ld(ld)
            if res:
                return res
        # fallback to html parsing
        return self.parse_ingredients_from_html(html)