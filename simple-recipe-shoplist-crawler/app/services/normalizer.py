import re
from collections import defaultdict
from typing import List, Dict

# Very simple quantity parser and normalizer for prototype purposes.


def _split_qty_name(text: str):
    # match patterns like "1 cup sugar", "2-3 cloves garlic", "250g butter"
    m = re.match(r"^\s*([\d/\.\-]+)\s*([a-zA-Z]+)?\s*(.*)$", text)
    if m:
        qty = m.group(1)
        unit = m.group(2) or ""
        name = m.group(3)
        return qty + (" " + unit if unit else ""), name.strip()
    # fallback: try to find number inside
    m = re.search(r"([\d/\.]+)\s*(.*)", text)
    if m:
        return m.group(1), m.group(2).strip()
    return "", text.strip()


def normalize_recipe(recipe: Dict) -> Dict:
    normalized_ingredients = []
    for ing in recipe.get("ingredients", []):
        qty, name = _split_qty_name(ing)
        # simple cleanup
        name = re.sub(r"\(.*?\)", "", name).strip().lower()
        name = re.sub(r"[^a-z0-9 \-\&]", "", name)
        normalized_ingredients.append({"raw": ing, "qty": qty, "name": name})
    print(f"[normalizer] normalized {len(normalized_ingredients)} ingredients")
    return {**recipe, "ingredients": normalized_ingredients}


def build_shopping_list(normalized_recipe: Dict) -> List[Dict]:
    merged = defaultdict(lambda: {"name": "", "qtys": [], "raws": []})
    for ing in normalized_recipe.get("ingredients", []):
        key = ing.get("name") or ing.get("raw")
        merged[key]["name"] = key
        merged[key]["qtys"].append(ing.get("qty") or "")
        merged[key]["raws"].append(ing.get("raw"))
    out = []
    for k, v in merged.items():
        out.append({"name": v["name"], "qtys": v["qtys"], "raws": v["raws"]})
    print(f"[normalizer] built shopping list with {len(out)} items")
    return out
