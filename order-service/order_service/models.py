from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import uuid4
from sqlmodel import Field


class OrderProduct(BaseModel):
    product_id: int
    quantity: int


class Order(BaseModel):
    products: List[OrderProduct]
    order_id: Optional[str] = Field(default_factory=lambda: str(uuid4()), exclude=True)


class OrderUpdate(BaseModel):
    order_id: str
    products: Optional[List[OrderProduct]] = None