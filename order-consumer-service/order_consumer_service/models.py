from typing import Optional, Dict
from sqlmodel import SQLModel, Field, Column, JSON

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int
    quantity: int