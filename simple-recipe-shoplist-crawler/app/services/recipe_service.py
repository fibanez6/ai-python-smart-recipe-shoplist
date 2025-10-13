from . import fetcher, parser, normalizer, optimizer
from .shopper_service import search_shops as _search_shops


# keep a compatible name for callers
class ShopperProxy:
    @staticmethod
    async def search_shops(shopping_list):
        return await _search_shops(shopping_list)

shopper = ShopperProxy


async def process_recipe_url(url: str):
    print(f"[recipe_service] starting processing for {url}")
    html = await fetcher.fetch(url)
    recipe = parser.parse(html, url)
    normalized = normalizer.normalize_recipe(recipe)
    shopping_list = normalizer.build_shopping_list(normalized)
    # search products (mocked)
    offers = await shopper.search_shops(shopping_list)
    plan = optimizer.choose_best_combination(shopping_list, offers)
    print(f"[recipe_service] finished processing for {url}")
    return {"recipe": normalized, "shopping_list": shopping_list, "offers": offers, "plan": plan}
