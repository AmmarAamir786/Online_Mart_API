from typing import Optional
from pydantic import Field
from sqlmodel import SQLModel


class Product (SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    description: str = Field()
    price: float = Field()
    quantity: int = Field()