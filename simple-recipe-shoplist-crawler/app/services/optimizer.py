from typing import List, Dict


def choose_best_combination(shopping_list: List[Dict], offers: Dict) -> Dict:
    # For this prototype: choose cheapest product per item across shops independently.
    plan = []
    total = 0.0
    for item in shopping_list:
        name = item["name"]
        best = None
        best_shop = None
        for shop, shop_results in offers.items():
            # find item in shop_results
            for entry in shop_results:
                if entry["query"] == name and entry.get("matches"):
                    m = entry["matches"][0]
                    if best is None or m["price"] < best["price"]:
                        best = m
                        best_shop = shop
        if best is None:
            plan.append({"name": name, "shop": None, "product": None, "price": None})
        else:
            plan.append({"name": name, "shop": best_shop, "product": best["title"], "price": best["price"], "image": best.get("image"), "url": best.get("url")})
            total += float(best["price"])
            print(f"[optimizer] chose {name} from {best_shop} at {best['price']}")
    print(f"[optimizer] total estimated {round(total,2)}")
    return {"items": plan, "total": round(total, 2)}
