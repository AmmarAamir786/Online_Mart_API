from pydantic import BaseModel


class Product (BaseModel):
    name: str
    description: str
    price: float
    quantity: int


class ProductUpdate(Product):
    id: int