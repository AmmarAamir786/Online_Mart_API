import asyncio
from contextlib import asynccontextmanager
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from inventory_consumer_service.consumers.consume_inventory import consume_inventory
from inventory_consumer_service.consumers.consume_product_confirmation import consume_product_confirmation
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

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(consume_inventory()),
        loop.create_task(consume_product_confirmation()),
        # loop.create_task(consume_orders())
    ]
    
    yield

    for task in tasks:
        task.cancel()
        await task


# async def consume_orders():
#     consumer = await create_consumer(KAFKA_ORDER_TOPIC)
#     if not consumer:
#         logger.error("Failed to create Kafka order consumer")
#         return

#     try:
#         async for msg in consumer:
#             try:
#                 order = order_pb2.Order()
#                 order.ParseFromString(msg.value)
#                 logger.info(f"Received Order Message: {order}")

#                 with Session(engine) as session:
#                     existing_inventory = session.exec(select(Inventory).where(Inventory.product_id == order.product_id)).first()
#                     if existing_inventory:

#                         if order.operation == operation_pb2.OperationType.CREATE:
#                             existing_inventory.stock_level -= order.quantity

#                         # elif order.operation == operation_pb2.OperationType.UPDATE:
#                         #     existing_inventory.stock_level -= order.quantity

#                         elif order.operation == operation_pb2.OperationType.DELETE:
#                             existing_inventory.stock_level += order.quantity

#                         session.add(existing_inventory)
#                         session.commit()
#                         session.refresh(existing_inventory)
#                         logger.info(f'Inventory updated in db: {existing_inventory}')
#                     else:
#                         logger.warning(f"No inventory found for product ID {order.product_id}")

#             except Exception as e:
#                 logger.error(f"Error processing order message: {e}")

#     finally:
#         await consumer.stop()
#         logger.info("Order consumer stopped")


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
    
