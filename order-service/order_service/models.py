from pydantic import BaseModel
from typing import List, Optional
from order_service.utils.uuid import short_uuid
from sqlmodel import Field

class OrderProduct(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    products: List[OrderProduct]

class Order(BaseModel):
    order_id: str = Field(default_factory=lambda: str(short_uuid()))
    products: List[OrderProduct]
