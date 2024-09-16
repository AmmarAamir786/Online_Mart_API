from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from order_consumer_service.utils.uuid import short_uuid

class Order(SQLModel, table=True):
    order_id: str = Field(default_factory=lambda: str(short_uuid()), primary_key=True)
    products: List["OrderProduct"] = Relationship(back_populates="order")
    order_status: str = Field(default="order created")

class OrderProduct(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: str = Field(foreign_key="order.order_id")
    product_id: int
    quantity: int
    order: Optional[Order] = Relationship(back_populates="products")

class OrderCreate(BaseModel):
    products: List[OrderProduct]

