import asyncio
from contextlib import asynccontextmanager
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from inventory_consumer_service.consumers.consume_inventory import consume_inventory
from inventory_consumer_service.consumers.consume_product_confirmation import consume_product_confirmation
from inventory_consumer_service.consumers.consume_validation import consume_validation, create_topic
from inventory_consumer_service.models import Inventory
from sqlmodel import Session, select
from inventory_consumer_service.db import create_tables, engine, get_session


logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    await create_topic()

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(consume_inventory()),
        loop.create_task(consume_product_confirmation()),
        loop.create_task(consume_validation())
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


@app.get("/inventory/{inventory_id}", response_model=Inventory)
async def get_product(inventory_id: int):
    with Session(engine) as session:
        inventory = session.exec(select(Inventory).where(Inventory.id == inventory_id)).first()
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory not found")
        return inventory
    
