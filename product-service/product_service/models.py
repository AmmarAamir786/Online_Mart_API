from pydantic import BaseModel


class Product (BaseModel):
    product_id: int
    name: str
    description: str
    price: float
    category: str


class ProductUpdate(Product):
    id: int
    