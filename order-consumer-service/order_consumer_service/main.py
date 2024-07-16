import asyncio
from contextlib import asynccontextmanager
from typing import List
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from order_consumer_service.models import Order, OrderProduct
from order_consumer_service.db import create_tables, engine, get_session
from order_consumer_service.setting import KAFKA_INVENTORY_UPDATE_TOPIC

from order_consumer_service.consumers.consume_delete_order import consume_delete_order
from order_consumer_service.consumers.consume_inventory_response import consume_inventory_response

from order_consumer_service.utils.logger import logger
from order_consumer_service.utils.topic import create_topic


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    await create_topic(topic=KAFKA_INVENTORY_UPDATE_TOPIC)

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

@app.get("/orders/")
async def get_orders(session = Depends(get_session)):
    orders_query = session.exec(select(Order))
    orders = orders_query.all()

    result = []
    for order in orders:
        products_query = session.exec(select(OrderProduct).where(OrderProduct.order_id == order.order_id))
        products = products_query.all()

        order_dict = {
            "order_id": order.order_id,
            "products": [{"product_id": product.product_id, "quantity": product.quantity} for product in products]
        }
        result.append(order_dict)

    return result

@app.get("/orders/{order_id}")
async def get_order(order_id: str, session = Depends(get_session)):
    query = session.exec(select(Order).where(Order.order_id == order_id))
    order = query.first()
    if not order:
        return {"error": "Order not found"}

    products_query = session.exec(select(OrderProduct).where(OrderProduct.order_id == order_id))
    products = products_query.all()

    order_dict = {
        "order_id": order.order_id,
        "products": [{"product_id": product.product_id, "quantity": product.quantity} for product in products]
    }

    return order_dict
