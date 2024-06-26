from pydantic import BaseModel
from typing import Optional

class Inventory(BaseModel):
    product_id: int
    stock_level: int

class InventoryUpdate(Inventory):
    id: int