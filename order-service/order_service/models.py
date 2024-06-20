from pydantic import BaseModel
from typing import Dict

class Order(BaseModel):
    product_quantities: Dict[int, int]  # Key: Product ID, Value: Quantity

class OrderUpdate(Order):
    id: int