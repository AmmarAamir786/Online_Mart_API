from typing import Optional
from pydantic import Field
from sqlmodel import SQLModel


class Product (SQLModel, table=True):
    id: int = Field(default=None)
    name: str = Field(primary_key=True)
    description: str = Field()
    price: float = Field()
    quantity: int = Field()