from pydantic import BaseModel
from typing import Dict

class Order(BaseModel):
    product_id: int
    quantity: int

class OrderUpdate(Order):
    id: int