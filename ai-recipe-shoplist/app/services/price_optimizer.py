"""Price optimization service using AI for intelligent shopping decisions."""

from dataclasses import dataclass

from ..models import Ingredient, OptimizationResult, ShoppingListItem, StoreSearchResult


@dataclass
class StoreVisit:
    """Represents a visit to a store with items to buy."""
    store_name: str
    items: list[ShoppingListItem]
    total_cost: float
    travel_cost: float = 0.0  # Future: add travel cost optimization


class PriceOptimizer:
    """Optimizes shopping across multiple stores to minimize total cost."""
    
    def __init__(self):
        self.store_travel_costs = {
            "coles": 2.0,      # Estimated travel cost in AUD
            "woolworths": 2.5,
            "aldi": 3.0,       # Typically further away
            "iga": 1.5,        # Local convenience
        }
        self.minimum_order_thresholds = {
            "coles": 0.0,      # No minimum for pickup
            "woolworths": 0.0,
            "aldi": 0.0,
            "iga": 0.0,
        }
    
    async def optimize_shopping(self, ingredients: list[Ingredient], 
                              store_results: dict[str, list[StoreSearchResult]]) -> OptimizationResult:
        """Find the optimal combination of stores and products."""
        print("[PriceOptimizer] Starting optimization")
        
        # Build shopping list items with best products per store
        shopping_items = self._build_shopping_items(ingredients, store_results)
        
        if not shopping_items:
            return OptimizationResult(
                items=[],
                total_cost=0.0,
                stores_breakdown={},
                savings=0.0
            )
        
        # Strategy 1: Single store (baseline)
        single_store_options = await self._calculate_single_store_options(shopping_items)
        
        # Strategy 2: Multi-store optimization
        multi_store_option = await self._calculate_multi_store_optimization(shopping_items)
        
        # Strategy 3: AI-enhanced optimization (if available)
        try:
            from .ai_service import get_ai_service
            ai_service = get_ai_service()
            ai_enhanced_option = await self._calculate_ai_enhanced_optimization(
                shopping_items, ai_service
            )
        except Exception as e:
            print(f"[PriceOptimizer] AI optimization not available: {e}")
            ai_enhanced_option = None
        
        # Choose best option
        all_options = [multi_store_option] + list(single_store_options.values())
        if ai_enhanced_option:
            all_options.append(ai_enhanced_option)
        
        best_option = min(all_options, key=lambda x: x.total_cost)
        
        # Calculate savings vs single best store
        best_single_store_cost = min(opt.total_cost for opt in single_store_options.values())
        savings = best_single_store_cost - best_option.total_cost
        
        print(f"[PriceOptimizer] Best option: ${best_option.total_cost:.2f} "
              f"(savings: ${savings:.2f})")
        
        best_option.savings = max(0, savings)
        return best_option
    
    def _build_shopping_items(self, ingredients: list[Ingredient], 
                             store_results: dict[str, list[StoreSearchResult]]) -> list[ShoppingListItem]:
        """Build shopping list items from ingredients and store results."""
        shopping_items = []
        
        for ingredient in ingredients:
            # Find best product for this ingredient across all stores
            best_products_by_store = {}
            
            for store_name, results in store_results.items():
                # Find results for this ingredient
                ingredient_result = next(
                    (r for r in results if r.ingredient_name == ingredient.name),
                    None
                )
                
                if ingredient_result and ingredient_result.products:
                    # Take the best (first) product from each store
                    best_products_by_store[store_name] = ingredient_result.products[0]
            
            if best_products_by_store:
                shopping_item = ShoppingListItem(
                    ingredient=ingredient,
                    selected_product=None,  # Will be set during optimization
                    quantity_needed=ingredient.quantity or 1.0,
                    estimated_cost=None,
                    store_options=best_products_by_store  # Include store options in constructor
                )
                shopping_items.append(shopping_item)
        
        return shopping_items
    
    async def _calculate_single_store_options(self, 
                                            shopping_items: list[ShoppingListItem]) -> dict[str, OptimizationResult]:
        """Calculate cost for shopping at each single store."""
        store_options = {}
        
        # Get all available stores
        available_stores = set()
        for item in shopping_items:
            if item.store_options:
                available_stores.update(item.store_options.keys())
        
        for store_name in available_stores:
            total_cost = 0.0
            optimized_items = []
            
            for item in shopping_items:
                if item.store_options and store_name in item.store_options:
                    product = item.store_options[store_name]
                    cost = product.price * item.quantity_needed
                    
                    optimized_item = ShoppingListItem(
                        ingredient=item.ingredient,
                        selected_product=product,
                        quantity_needed=item.quantity_needed,
                        estimated_cost=cost
                    )
                    optimized_items.append(optimized_item)
                    total_cost += cost
                else:
                    # Item not available at this store
                    optimized_item = ShoppingListItem(
                        ingredient=item.ingredient,
                        selected_product=None,
                        quantity_needed=item.quantity_needed,
                        estimated_cost=0.0
                    )
                    optimized_items.append(optimized_item)
            
            # Add travel cost
            travel_cost = self.store_travel_costs.get(store_name, 2.0)
            total_cost += travel_cost
            
            store_options[store_name] = OptimizationResult(
                items=optimized_items,
                total_cost=total_cost,
                stores_breakdown={store_name: total_cost - travel_cost, "travel": travel_cost}
            )
        
        return store_options
    
    async def _calculate_multi_store_optimization(self, 
                                                shopping_items: list[ShoppingListItem]) -> OptimizationResult:
        """Calculate optimal multi-store shopping strategy."""
        optimized_items = []
        stores_breakdown = {}
        total_cost = 0.0
        
        for item in shopping_items:
            if not item.store_options:
                # No products available for this ingredient
                optimized_item = ShoppingListItem(
                    ingredient=item.ingredient,
                    selected_product=None,
                    quantity_needed=item.quantity_needed,
                    estimated_cost=0.0
                )
                optimized_items.append(optimized_item)
                continue
            
            # Find cheapest product across all stores
            best_product = None
            best_cost = float('inf')
            best_store = None
            
            for store_name, product in item.store_options.items():
                cost = product.price * item.quantity_needed
                if cost < best_cost:
                    best_cost = cost
                    best_product = product
                    best_store = store_name
            
            if best_product:
                optimized_item = ShoppingListItem(
                    ingredient=item.ingredient,
                    selected_product=best_product,
                    quantity_needed=item.quantity_needed,
                    estimated_cost=best_cost
                )
                optimized_items.append(optimized_item)
                
                # Add to store breakdown
                if best_store not in stores_breakdown:
                    stores_breakdown[best_store] = 0.0
                stores_breakdown[best_store] += best_cost
                total_cost += best_cost
        
        # Add travel costs for each store visited
        travel_costs = 0.0
        for store_name in stores_breakdown.keys():
            if store_name != "travel":
                travel_cost = self.store_travel_costs.get(store_name, 2.0)
                travel_costs += travel_cost
        
        stores_breakdown["travel"] = travel_costs
        total_cost += travel_costs
        
        return OptimizationResult(
            items=optimized_items,
            total_cost=total_cost,
            stores_breakdown=stores_breakdown
        )
    
    async def _calculate_ai_enhanced_optimization(self, 
                                                shopping_items: list[ShoppingListItem],
                                                ai_service) -> OptimizationResult:
        """Use AI to enhance optimization with smart product substitutions."""
        print("[PriceOptimizer] Using AI enhancement")
        
        # Create a prompt for AI to optimize the shopping
        optimization_data = []
        for item in shopping_items:
            if item.store_options:
                item_data = {
                    "ingredient": item.ingredient.name,
                    "quantity": item.quantity_needed,
                    "options": []
                }
                
                for store_name, product in item.store_options.items():
                    item_data["options"].append({
                        "store": store_name,
                        "product": product.title,
                        "price": product.price,
                        "brand": product.brand,
                        "size": product.size
                    })
                
                optimization_data.append(item_data)
        
        # Use AI to suggest optimal combinations
        try:
            import json
            prompt = f"""
            Optimize this grocery shopping to minimize total cost while considering:
            1. Product quality and brand reputation
            2. Travel costs between stores ({self.store_travel_costs})
            3. Minimum order requirements
            4. Product substitutions that make sense
            
            Shopping data:
            {json.dumps(optimization_data, indent=2)}
            
            Return JSON with:
            - "selections": array of {{"ingredient": "name", "store": "store", "product": "title", "reason": "why"}}
            - "total_estimated_cost": number
            - "strategy": "explanation"
            
            Prefer fewer store visits to reduce travel costs.
            """
            
            messages = [
                {"role": "system", "content": "You are a grocery shopping optimization expert."},
                {"role": "user", "content": prompt}
            ]
            
            response = await ai_service.provider.complete_chat(messages, max_tokens=1500)
            ai_result = json.loads(response)
            
            # Convert AI recommendations to OptimizationResult
            optimized_items = []
            stores_breakdown = {}
            total_cost = 0.0
            
            ai_selections = {sel["ingredient"]: sel for sel in ai_result.get("selections", [])}
            
            for item in shopping_items:
                ingredient_name = item.ingredient.name
                
                if ingredient_name in ai_selections:
                    selection = ai_selections[ingredient_name]
                    selected_store = selection["store"]
                    
                    if (item.store_options and 
                        selected_store in item.store_options):
                        
                        product = item.store_options[selected_store]
                        cost = product.price * item.quantity_needed
                        
                        optimized_item = ShoppingListItem(
                            ingredient=item.ingredient,
                            selected_product=product,
                            quantity_needed=item.quantity_needed,
                            estimated_cost=cost
                        )
                        optimized_items.append(optimized_item)
                        
                        if selected_store not in stores_breakdown:
                            stores_breakdown[selected_store] = 0.0
                        stores_breakdown[selected_store] += cost
                        total_cost += cost
                    else:
                        # Fallback if AI selection invalid
                        optimized_items.append(ShoppingListItem(
                            ingredient=item.ingredient,
                            selected_product=None,
                            quantity_needed=item.quantity_needed,
                            estimated_cost=0.0
                        ))
                else:
                    # No AI selection for this ingredient
                    optimized_items.append(ShoppingListItem(
                        ingredient=item.ingredient,
                        selected_product=None,
                        quantity_needed=item.quantity_needed,
                        estimated_cost=0.0
                    ))
            
            # Add travel costs
            travel_costs = 0.0
            for store_name in stores_breakdown.keys():
                if store_name != "travel":
                    travel_cost = self.store_travel_costs.get(store_name, 2.0)
                    travel_costs += travel_cost
            
            stores_breakdown["travel"] = travel_costs
            total_cost += travel_costs
            
            print(f"[PriceOptimizer] AI strategy: {ai_result.get('strategy', 'Not provided')}")
            
            return OptimizationResult(
                items=optimized_items,
                total_cost=total_cost,
                stores_breakdown=stores_breakdown
            )
            
        except Exception as e:
            print(f"[PriceOptimizer] AI enhancement failed: {e}")
            # Fallback to multi-store optimization
            return await self._calculate_multi_store_optimization(shopping_items)
    
    async def suggest_meal_planning_optimization(self, recipes: list[str]) -> dict[str, any]:
        """Suggest optimization across multiple recipes for meal planning."""
        # Future enhancement: optimize across multiple recipes
        return {
            "suggestion": "Meal planning optimization not yet implemented",
            "bulk_discounts": [],
            "weekly_optimization": {}
        }


# Global optimizer instance
price_optimizer = PriceOptimizer()