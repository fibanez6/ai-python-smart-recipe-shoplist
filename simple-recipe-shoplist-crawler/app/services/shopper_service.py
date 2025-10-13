import asyncio
from typing import List, Dict

# shopper_service is a thin wrapper that uses the adapters in the
# `app.services.shopper` package (folder). This avoids naming collisions
# between a module named `shopper.py` and the `shopper` package.
from .shopper import adapters


async def search_shops(shopping_list: List[Dict]) -> Dict:
    # Parallel search across adapters
    tasks = []
    for shop in adapters.get_adapters():
        tasks.append(shop.search_bulk(shopping_list))
    results = await asyncio.gather(*tasks)
    # results is list per adapter
    names = adapters.get_adapter_names()
    offers = {name: res for name, res in zip(names, results)}
    for n, r in offers.items():
        print(f"[shopper_service] adapter={n} returned {len(r)} queries")
    return offers
