import asyncio
import os
from typing import List, Dict

# Get base URL prefix for static files
STAGE = os.getenv("STAGE", "")
PREFIX = f"/{STAGE}" if STAGE else ""

class BaseAdapter:
    name = "base"

    async def search_bulk(self, shopping_list: List[Dict]) -> List[Dict]:
        raise NotImplementedError()


class MockColes(BaseAdapter):
    name = "coles"

    async def search_bulk(self, shopping_list: List[Dict]) -> List[Dict]:
        await asyncio.sleep(0.05)
        out = []
        for item in shopping_list:
            out.append({
                "query": item["name"],
                "matches": [
                    {"title": f"{item['name'].title()} - Coles Brand", "price": 2.5, "image": f"{PREFIX}/static/img/coles.png", "url": "https://coles.example/product"}
                ],
            })
        return out


class MockWoolworths(BaseAdapter):
    name = "woolworths"

    async def search_bulk(self, shopping_list: List[Dict]) -> List[Dict]:
        await asyncio.sleep(0.05)
        out = []
        for item in shopping_list:
            out.append({
                "query": item["name"],
                "matches": [
                    {"title": f"{item['name'].title()} - Woolworths", "price": 2.75, "image": f"{PREFIX}/static/img/woolworths.png", "url": "https://woolworths.example/product"}
                ],
            })
        return out


class MockAldi(BaseAdapter):
    name = "aldi"

    async def search_bulk(self, shopping_list: List[Dict]) -> List[Dict]:
        await asyncio.sleep(0.05)
        out = []
        for item in shopping_list:
            out.append({
                "query": item["name"],
                "matches": [
                    {"title": f"{item['name'].title()} - ALDI Special", "price": 2.25, "image": f"{PREFIX}/static/img/aldi.png", "url": "https://aldi.example/product"}
                ],
            })
        return out


def get_adapters():
    return [MockColes(), MockWoolworths(), MockAldi()]


def get_adapter_names():
    return [a.name for a in get_adapters()]
