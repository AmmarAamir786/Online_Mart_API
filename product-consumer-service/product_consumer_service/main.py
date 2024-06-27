import asyncio
from contextlib import asynccontextmanager
import logging
from typing import List

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, HTTPException
from product_consumer_service.models import Product
from sqlmodel import Session, select
from product_consumer_service import product_pb2
from product_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_CONSUMER_GROUP_ID, KAFKA_PRODUCT_TOPIC
from product_consumer_service.db import create_tables, engine, get_session


logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info('Creating Tables')
    create_tables()
    logger.info("Tables Created")

    loop = asyncio.get_event_loop()
    task = loop.create_task(consume_products())
    
    yield

    task.cancel()
    await task


MAX_RETRIES = 5
RETRY_INTERVAL = 10

async def consume_products():
    retries = 0

    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                KAFKA_PRODUCT_TOPIC,
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
                product = product_pb2.Product()
                product.ParseFromString(msg.value)
                logger.info(f"Received Message: {product}")

                with Session(engine) as session:
                    if product.operation == product_pb2.ProductOperationType.CREATE:
                        new_product = Product(
                            name=product.name,
                            description=product.description,
                            price=product.price,
                            category=product.category
                        )
                        session.add(new_product)
                        session.commit()
                        session.refresh(new_product)
                        logger.info(f'Product added to db: {new_product}')
                    
                    elif product.operation == product_pb2.ProductOperationType.UPDATE:
                        existing_product = session.exec(select(Product).where(Product.id == product.id)).first()
                        if existing_product:
                            existing_product.name = product.name
                            existing_product.description = product.description
                            existing_product.price = product.price
                            existing_product.category = product.category
                            session.add(existing_product)
                            session.commit()
                            session.refresh(existing_product)
                            logger.info(f'Product updated in db: {existing_product}')
                        else:
                            logger.warning(f"Product with ID {product.id} not found")

                    elif product.operation == product_pb2.ProductOperationType.DELETE:
                        existing_product = session.exec(select(Product).where(Product.id == product.id)).first()
                        if existing_product:
                            session.delete(existing_product)
                            session.commit()
                            logger.info(f"Product with ID {product.id} successfully deleted")
                        else:
                            logger.warning(f"Product with ID {product.id} not found for deletion")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    finally:
        await consumer.stop()
        logger.info("Consumer stopped")
    return
        


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