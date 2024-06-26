import asyncio
from contextlib import asynccontextmanager
import logging
from typing import List

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, HTTPException
from inventory_consumer_service.models import Inventory
from sqlmodel import Session, select
from inventory_consumer_service import inventory_pb2
from inventory_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_CONSUMER_GROUP_ID, KAFKA_INVENTORY_TOPIC
from inventory_consumer_service.db import create_tables, engine, get_session


logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    loop = asyncio.get_event_loop()
    task = loop.create_task(consume_inventory())
    
    yield

    task.cancel()
    await task


MAX_RETRIES = 5
RETRY_INTERVAL = 10

async def consume_inventory():
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                KAFKA_INVENTORY_TOPIC,
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
                inventory = inventory_pb2.Inventory()
                inventory.ParseFromString(msg.value)
                logger.info(f"Received Message: {inventory}")

                with Session(engine) as session:
                    if inventory.operation == inventory_pb2.OperationType.CREATE:
                        new_inventory = Inventory(
                            product_id=inventory.product_id,
                            stock_level=inventory.stock_level
                        )
                        session.add(new_inventory)
                        session.commit()
                        session.refresh(new_inventory)
                        logger.info(f'Inventory added to db: {new_inventory}')
                    
                    elif inventory.operation == inventory_pb2.OperationType.UPDATE:
                        existing_inventory = session.exec(select(Inventory).where(Inventory.id == inventory.id)).first()
                        if existing_inventory:
                            existing_inventory.product_id = inventory.product_id
                            existing_inventory.stock_level = inventory.stock_level
                            session.add(existing_inventory)
                            session.commit()
                            session.refresh(existing_inventory)
                            logger.info(f'Inventory updated in db: {existing_inventory}')
                        else:
                            logger.warning(f"Inventory with ID {inventory.id} not found")

                    elif inventory.operation == inventory_pb2.OperationType.DELETE:
                        existing_inventory = session.exec(select(Inventory).where(Inventory.id == inventory.id)).first()
                        if existing_inventory:
                            session.delete(existing_inventory)
                            session.commit()
                            logger.info(f"Inventory with ID {inventory.id} successfully deleted")
                        else:
                            logger.warning(f"Inventory with ID {inventory.id} not found for deletion")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    finally:
        await consumer.stop()
        logger.info("Consumer stopped")
    return
        


app = FastAPI(lifespan=lifespan, title="Inventory Consumer Service", version='1.0.0')


@app.get("/inventory/", response_model=List[Inventory])
async def get_inventory():
    with Session(engine) as session:
        products = session.exec(select(Inventory)).all()
        return products


@app.get("/inventory/{inventory_id}", response_model=Inventory)
async def get_product(inventory_id: int):
    with Session(engine) as session:
        inventory = session.exec(select(Inventory).where(Inventory.id == inventory_id)).first()
        if not inventory:
            raise HTTPException(status_code=404, detail="Product not found")
        return inventory