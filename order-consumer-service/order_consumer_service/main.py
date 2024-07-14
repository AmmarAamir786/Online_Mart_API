import asyncio
from contextlib import asynccontextmanager
from typing import List

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from order_consumer_service.models import OrderItem
from order_consumer_service.proto import order_pb2, operation_pb2
from order_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_CONSUMER_GROUP_ID, KAFKA_ORDER_TOPIC
from order_consumer_service.db import create_tables, engine, get_session
from order_consumer_service.consumers.consume_delete_order import consume_delete_order
from order_consumer_service.consumers.consume_inventory_response import consume_inventory_response
from order_consumer_service.utils.logger import logger
from order_consumer_service.utils.topic import create_topic


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    await create_topic()

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(consume_delete_order()),
        loop.create_task(consume_inventory_response())
    ]
    
    yield

    for task in tasks:
        task.cancel()
        await task


app = FastAPI(lifespan=lifespan, title="Order Consumer Service", version='1.0.0')

@app.get("/orders/", response_model=List[OrderItem])
async def get_orders():
    with Session(engine) as session:
        orders = session.exec(select(OrderItem)).all()
        return orders

@app.get("/orders/{order_id}", response_model=OrderItem)
async def get_order(order_id: int):
    with Session(engine) as session:
        order = session.exec(select(OrderItem).where(OrderItem.id == order_id)).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
