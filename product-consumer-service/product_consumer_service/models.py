from typing import Optional
from pydantic import Field
from sqlmodel import SQLModel


class Product (SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str
    price: float
    quantity: int