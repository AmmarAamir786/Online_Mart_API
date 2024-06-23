from typing import Optional
from sqlmodel import SQLModel, Field


class Product (SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    price: float
    category: strftime(format)