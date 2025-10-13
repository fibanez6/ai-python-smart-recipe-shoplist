from bs4 import BeautifulSoup
from typing import Dict, List


def parse(html: str, url: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1")
    title_text = title.get_text(strip=True) if title else url

    # Find ingredients: common patterns
    ingredients = []
    for sel in [".ingredients", ".ingredient-list", "ul.ingredients", "ul.recipe-ingredients"]:
        node = soup.select_one(sel)
        if node:
            for li in node.find_all(["li", "p"]):
                text = li.get_text(separator=" ", strip=True)
                if text:
                    ingredients.append(text)
            break

    # fallback: any <li> that looks like ingredient (contains a number or unit)
    if not ingredients:
        for li in soup.find_all("li"):
            txt = li.get_text(strip=True)
            if any(u in txt.lower() for u in ["cup", "tbsp", "tsp", "g", "kg", "oz", "ml"]) or any(ch.isdigit() for ch in txt):
                ingredients.append(txt)
                if len(ingredients) > 60:
                    break

    # Instructions
    instructions = []
    for sel in [".instructions", ".method", ".directions", "ol.instructions"]:
        node = soup.select_one(sel)
        if node:
            for li in node.find_all(["li", "p"]):
                text = li.get_text(separator=" ", strip=True)
                if text:
                    instructions.append(text)
            break

    if not instructions:
        # try paragraphs under article
        for p in soup.find_all("p")[:20]:
            txt = p.get_text(strip=True)
            if len(txt) > 40:
                instructions.append(txt)
                if len(instructions) >= 6:
                    break

    print(f"[parser] parsed title={title_text!r}, ingredients={len(ingredients)}, instructions={len(instructions)}")
    return {"url": url, "title": title_text, "ingredients": ingredients, "instructions": instructions}
