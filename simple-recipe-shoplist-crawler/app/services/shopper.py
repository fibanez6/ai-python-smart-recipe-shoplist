import asyncio
from typing import List, Dict
from .shopper import adapters


async def search_shops(shopping_list: List[Dict]) -> Dict:
    # Parallel search across adapters
    tasks = []
    for shop in adapters.get_adapters():
        tasks.append(shop.search_bulk(shopping_list))
    results = await asyncio.gather(*tasks)
    # results is list per adapter
    offers = {name: res for name, res in zip(adapters.get_adapter_names(), results)}
    return offers
