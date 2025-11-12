from models import Ingredient, Product
from typing import List, Optional

class BestMatchAgent:
    def __init__(self):
        pass

    def cost_per_unit(self, product: Product) -> Optional[float]:
        if product.quantity and product.quantity > 0 and product.price:
            return product.price / product.quantity
        return None

    def choose(self, ingredient: Ingredient, candidates: List[Product]) -> Optional[Product]:
        scored = []
        for p in candidates:
            cpu = self.cost_per_unit(p)
            if cpu is not None:
                scored.append((cpu, p))
        if not scored and candidates:
            return min(candidates, key=lambda p: p.price if p.price is not None else float('inf'))
        if not scored:
            return None
        if ingredient.qty and ingredient.unit:
            filtered = [ (cpu,p) for cpu,p in scored if p.quantity and p.quantity >= ingredient.qty ]
            if filtered:
                return min(filtered, key=lambda t: t[0])[1]
        return min(scored, key=lambda t: t[0])[1]