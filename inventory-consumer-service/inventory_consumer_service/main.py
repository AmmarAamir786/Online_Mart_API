import asyncio
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select

from inventory_consumer_service.consumers.consume_inventory import consume_inventory
from inventory_consumer_service.consumers.consume_product_confirmation import consume_product_confirmation
from inventory_consumer_service.consumers.consume_validation import consume_validation
from inventory_consumer_service.consumers.consume_inventory_update import consume_inventory_update

from inventory_consumer_service.models import Inventory
from inventory_consumer_service.db import create_tables, engine, get_session
from inventory_consumer_service.setting import KAFKA_INVENTORY_RESPONSE_TOPIC

from inventory_consumer_service.utils.logger import logger
from inventory_consumer_service.utils.topic import create_topic

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    await create_topic(topic=KAFKA_INVENTORY_RESPONSE_TOPIC)

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(consume_inventory()),
        loop.create_task(consume_product_confirmation()),
        loop.create_task(consume_validation()),
        loop.create_task(consume_inventory_update())
    ]
    
    yield

    for task in tasks:
        task.cancel()
        await task



app = FastAPI(lifespan=lifespan, title="Inventory Consumer Service", version='1.0.0')


@app.get("/inventory/", response_model=List[Inventory])
async def get_inventory():
    with Session(engine) as session:
        inventory = session.exec(select(Inventory)).all()
        return inventory


@app.get("/inventory/{product_id}", response_model=Inventory)
async def get_product(product_id: int):
    with Session(engine) as session:
        inventory = session.exec(select(Inventory).where(Inventory.product_id == product_id)).first()
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")
        return inventory
    
