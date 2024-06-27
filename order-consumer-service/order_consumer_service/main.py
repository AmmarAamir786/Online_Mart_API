import asyncio
from contextlib import asynccontextmanager
import logging
from typing import List

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from order_consumer_service.models import OrderItem
from order_consumer_service import order_pb2
from order_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_CONSUMER_GROUP_ID, KAFKA_ORDER_TOPIC
from order_consumer_service.db import create_tables, engine, get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    loop = asyncio.get_event_loop()
    task = loop.create_task(consume_orders())
    
    yield

    task.cancel()
    await task

MAX_RETRIES = 5
RETRY_INTERVAL = 10

async def consume_orders():
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                KAFKA_ORDER_TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVER,
                group_id=KAFKA_CONSUMER_GROUP_ID,
                auto_offset_reset='earliest',  # Start from the earliest message if no offset is committed
                enable_auto_commit=True,       # Enable automatic offset committing
                auto_commit_interval_ms=5000   # Interval for automatic offset commits
            )

            await consumer.start()
            logger.info("Consumer started successfully.")
            break
        except Exception as e:
            retries += 1
            logger.error(f"Error starting consumer, retry {retries}/{MAX_RETRIES}: {e}")
            if retries < MAX_RETRIES:
                await asyncio.sleep(RETRY_INTERVAL)
            else:
                logger.error("Max retries reached. Could not start consumer.")
                return

    try:
        async for msg in consumer:
            try:
                order = order_pb2.Order()
                order.ParseFromString(msg.value)
                logger.info(f"Received Message: {order}")

                with Session(engine) as session:
                    if order.operation == order_pb2.OrderOperationType.CREATE:
                        new_order = OrderItem(
                            product_id=order.product_id,
                            quantity=order.quantity
                        )
                        session.add(new_order)
                        session.commit()
                        session.refresh(new_order)
                        logger.info(f'Order added to db: {new_order}')
                    
                    # elif order.operation == order_pb2.OrderOperationType.UPDATE:
                    #     existing_order = session.exec(select(OrderItem).where(OrderItem.id == order.id)).first()
                    #     if existing_order:
                    #         existing_order.product_id = order.product_id
                    #         existing_order.quantity = order.quantity
                    #         session.add(existing_order)
                    #         session.commit()
                    #         session.refresh(existing_order)
                    #         logger.info(f'Order updated in db: {existing_order}')
                    #     else:
                    #         logger.warning(f"Order with ID {order.id} not found")

                    elif order.operation == order_pb2.OrderOperationType.DELETE:
                        existing_order = session.exec(select(OrderItem).where(OrderItem.id == order.id)).first()
                        if existing_order:
                            session.delete(existing_order)
                            session.commit()
                            logger.info(f"Order with ID {order.id} successfully deleted")
                        else:
                            logger.warning(f"Order with ID {order.id} not found for deletion")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    finally:
        await consumer.stop()
        logger.info("Consumer stopped")
    return

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
