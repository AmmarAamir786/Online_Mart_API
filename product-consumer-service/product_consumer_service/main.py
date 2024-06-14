import asyncio
from contextlib import asynccontextmanager
import logging

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI
# from product_consumer_service.models import Product
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Session, select
from product_consumer_service import product_pb2
from product_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_CONSUMER_GROUP_ID, KAFKA_PRODUCT_TOPIC
from product_consumer_service.db import create_tables, engine, get_session
from aiokafka.errors import KafkaConnectionError


logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


class Product (SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str
    price: float
    quantity: int


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
                group_id=KAFKA_CONSUMER_GROUP_ID
            )

            await consumer.start()
            logger.info("CONSUMER STARTED LETSS GOOOOOOOO....")
            try:
                async for msg in consumer:
                    try:
                        product = product_pb2.Product()
                        product.ParseFromString(msg.value)
                        logger.info(f"Received Message: {product}")

                        with Session(engine) as session:
                            if product.operation == product_pb2.OperationType.CREATE:
                                new_product = Product(
                                    id=product.id,
                                    name=product.name,
                                    description=product.description,
                                    price=product.price,
                                    quantity=product.quantity
                                )
                                session.add(new_product)
                                session.commit()
                                session.refresh(new_product)
                                logger.info(f'Product added to db: {new_product}')
                            
                            elif product.operation == product_pb2.OperationType.UPDATE:
                                existing_product = session.exec(select(Product).where(Product.id == product.id)).first()
                                if existing_product:
                                    existing_product.name = product.name
                                    existing_product.description = product.description
                                    existing_product.price = product.price
                                    existing_product.quantity = product.quantity
                                    session.add(existing_product)
                                    session.commit()
                                    session.refresh(existing_product)
                                    logger.info(f'Product updated in db: {existing_product}')
                                else:
                                    logger.warning(f"Product with ID {product.id} not found")

                            elif product.operation == product_pb2.OperationType.DELETE:
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
        
        except KafkaConnectionError:
            retries += 1 
            print(f"Kafka connection failed. Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
        
    raise Exception("Failed to connect to Kafka broker after several retries")


app = FastAPI(lifespan=lifespan, title="Product Consumer Service", version='1.0.0')