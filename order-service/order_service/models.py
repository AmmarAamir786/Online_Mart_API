from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import uuid4
from sqlmodel import Field

class OrderProduct(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    products: List[OrderProduct]

class Order(BaseModel):
    order_id: str = Field(default_factory=lambda: str(uuid4()))
    products: List[OrderProduct]

class OrderUpdate(BaseModel):
    order_id: str
    products: Optional[List[OrderProduct]] = None