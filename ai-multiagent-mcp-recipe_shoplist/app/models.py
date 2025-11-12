from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Ingredient(BaseModel):
    name: str
    qty: Optional[float] = None
    unit: Optional[str] = None
    raw_text: Optional[str] = None

class Product(BaseModel):
    id: str
    name: str
    price: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    url: Optional[HttpUrl] = None
    vendor: Optional[str] = None

class Match(BaseModel):
    ingredient: Ingredient
    chosen: Optional[Product]
    alternatives: List[Product] = []