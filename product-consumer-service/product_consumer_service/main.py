import asyncio

from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select

from product_consumer_service.consumers.consume_inventory import consume_inventory
from product_consumer_service.consumers.consume_products import consume_products

from product_consumer_service.models import Product
from product_consumer_service.setting import KAFKA_PRODUCT_CONFIRMATION_TOPIC
from product_consumer_service.db import create_tables, engine, get_session

from product_consumer_service.utils.topic import create_topic
from product_consumer_service.utils.logger import logger



@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    await create_topic(KAFKA_PRODUCT_CONFIRMATION_TOPIC)

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(consume_inventory()),
        loop.create_task(consume_products())
    ]
    
    yield

    for task in tasks:
        task.cancel()
        await task


app = FastAPI(lifespan=lifespan, title="Product Consumer Service", version='1.0.0')


@app.get("/products/", response_model=List[Product])
async def get_products():
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        return products


@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    with Session(engine) as session:
        product = session.exec(select(Product).where(Product.id == product_id)).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product