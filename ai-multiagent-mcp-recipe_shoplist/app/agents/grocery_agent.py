
import httpx

class GroceryAgent:
    async def search(self, ingredient: str):
        url = f"https://api.fakegrocerystore.com/search?q={ingredient}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
        # Simulated response
        return [{"name": ingredient, "price": 1.99, "quantity": "1kg"}]
