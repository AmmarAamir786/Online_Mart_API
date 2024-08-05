from fastapi import Form
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Annotated, Optional

# User model
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str
    email: str
    password: str

# Model for user registration
class RegisterUser(BaseModel):
    username: Annotated[str, Form()]
    email: Annotated[str, Form()]
    password: Annotated[str, Form()]

# ShippingDetails model
class ShippingDetails(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    address: str
    city: str
    state: str
    postal_code: str
    country: str
    user: Optional[User] = Relationship(back_populates="shipping_details")

User.shipping_details = Relationship(back_populates="user")

# Model for creating new shipping details
class CreateShippingDetails(BaseModel):
    address: Annotated[str, Form()]
    city: Annotated[str, Form()]
    state: Annotated[str, Form()]
    postal_code: Annotated[str, Form()]
    country: Annotated[str, Form()]

# Model for updating shipping details
class UpdateShippingDetails(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

class TokenData(BaseModel):
    username: str
    email: str

# # Create the model for Roles
# class Role(SQLModel, table=True):
#     id: int = Field(default=None, primary_key=True)
#     name: str  # e.g., 'admin', 'user'

# # Create the model for User Roles (many-to-many relationship)
# class UserRole(SQLModel, table=True):
#     user_id: int = Field(foreign_key="user.id", primary_key=True)
#     role_id: int = Field(foreign_key="role.id", primary_key=True)

# # Create the model for adding a role to a user
# class AddRole(BaseModel):
#     role: Annotated[str, Form()]