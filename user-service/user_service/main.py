from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware

from user_service.models import CreateShippingDetails, ShippingDetails, UpdateShippingDetails, User
from user_service.models import Register_User
from user_service.auth import current_user, get_user_from_db, hash_password
from user_service.utils.logger import logger
from user_service.db import create_tables, get_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")
    yield

app = FastAPI(lifespan=lifespan, title="User Service", version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to allow specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_user():
    return {"message": "Welcome User"}

@app.post("/register")
async def register_user(new_user: Register_User, session: Session = Depends(get_session)):
    db_user = get_user_from_db(session, new_user.username, new_user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="User with current credentials already exists")
    
    hashed_password = hash_password(new_user.password)
    user = User(username=new_user.username, email=new_user.email, password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": f"User with the username {user.username} successfully added"}

@app.get("/me")
async def user_profile(current_user: User = Depends(current_user)):
    return current_user


@app.post("/shipping-details")
async def create_shipping_details(
    new_details: CreateShippingDetails, 
    current_user: User = Depends(current_user), 
    session: Session = Depends(get_session)
):
    shipping_details = ShippingDetails(
        user_id=current_user.id, 
        address=new_details.address, 
        city=new_details.city, 
        state=new_details.state, 
        postal_code=new_details.postal_code, 
        country=new_details.country
    )
    session.add(shipping_details)
    session.commit()
    session.refresh(shipping_details)
    return {"message": "Shipping details added successfully"}

@app.put("/shipping-details")
async def update_shipping_details(
    updated_details: UpdateShippingDetails, 
    current_user: User = Depends(current_user), 
    session: Session = Depends(get_session)
):
    statement = select(ShippingDetails).where(ShippingDetails.user_id == current_user.id)
    shipping_details = session.exec(statement).first()
    
    if not shipping_details:
        raise HTTPException(status_code=404, detail="Shipping details not found")
    
    if updated_details.address:
        shipping_details.address = updated_details.address
    if updated_details.city:
        shipping_details.city = updated_details.city
    if updated_details.state:
        shipping_details.state = updated_details.state
    if updated_details.postal_code:
        shipping_details.postal_code = updated_details.postal_code
    if updated_details.country:
        shipping_details.country = updated_details.country

    session.commit()
    session.refresh(shipping_details)
    return {"message": "Shipping details updated successfully"}