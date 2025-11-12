from models import Match
from typing import List
from jinja2 import Environment, FileSystemLoader
import os

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'templates')
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

class OutputAgent:
    def render_html(self, matches: List[Match]) -> str:
        tpl = env.get_template('receipt.html')
        return tpl.render(matches=matches)

    def render_text(self, matches: List[Match]) -> str:
        lines = []
        for m in matches:
            chosen = m.chosen
            if chosen:
                lines.append(f"{m.ingredient.name:20} -> {chosen.name} | ${chosen.price if chosen.price else 'N/A'} | {chosen.quantity or ''}{chosen.unit or ''} | {chosen.vendor}")
            else:
                lines.append(f"{m.ingredient.name:20} -> NO MATCH")
        return '\n'.join(lines)