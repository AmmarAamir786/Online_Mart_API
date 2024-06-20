from typing import Optional, Dict
from sqlmodel import SQLModel, Field, Column, JSON

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_quantities: Dict[int, int] = Field(sa_column=Column(JSON))