import asyncio
from contextlib import asynccontextmanager
import logging
from typing import List

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI, HTTPException
from product_consumer_service.models import Product
from sqlmodel import Session, select
from product_consumer_service.proto import product_pb2, operation_pb2, inventory_pb2
from product_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_CONSUMER_GROUP_ID, KAFKA_PRODUCT_TOPIC, KAFKA_INVENTORY_TOPIC, KAFKA_CONFIRMATION_TOPIC
from product_consumer_service.db import create_tables, engine, get_session
from aiokafka.errors import KafkaConnectionError
from aiokafka.admin import AIOKafkaAdminClient, NewTopic


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
        loop.create_task(consume_products())
    ]
    
    yield

    for task in tasks:
        task.cancel()
        await task


MAX_RETRIES = 5
RETRY_INTERVAL = 10

async def create_topic():
    admin_client = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVER)

    retries = 0

    while retries < MAX_RETRIES:
        try:
            await admin_client.start()
            topic_list = [NewTopic(name=KAFKA_CONFIRMATION_TOPIC,
                                num_partitions=2, 
                                replication_factor=1)]
            try:
                await admin_client.create_topics(new_topics=topic_list, validate_only=False)
                print(f"Topic '{KAFKA_CONFIRMATION_TOPIC}' created successfully")
            except Exception as e:
                print(f"Failed to create topic '{KAFKA_CONFIRMATION_TOPIC}': {e}")
            finally:
                await admin_client.close()
            return
        
        except KafkaConnectionError:
            retries += 1 
            print(f"Kafka connection failed. Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
        
    raise Exception("Failed to connect to kafka broker after several retries")


async def create_consumer(topic: str):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=BOOTSTRAP_SERVER,
                group_id=KAFKA_CONSUMER_GROUP_ID,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=5000
            )
            await consumer.start()
            logger.info(f"Consumer for topic {topic} started successfully.")
            return consumer
        except Exception as e:
            retries += 1
            logger.error(f"Error starting consumer for topic {topic}, retry {retries}/{MAX_RETRIES}: {e}")
            if retries < MAX_RETRIES:
                await asyncio.sleep(RETRY_INTERVAL)
            else:
                logger.error(f"Max retries reached. Could not start consumer for topic {topic}.")
                return None



async def consume_products():
    consumer = await create_consumer(KAFKA_PRODUCT_TOPIC)
    if not consumer:
        logger.error("Failed to create kafka product consumer")
        return

    try:
        async for msg in consumer:
            try:
                product = product_pb2.Product()
                product.ParseFromString(msg.value)
                logger.info(f"Received Message: {product}")

                with Session(engine) as session:
                    if product.operation == operation_pb2.OperationType.CREATE:
                        new_product = Product(
                            name=product.name,
                            product_id=product.product_id,
                            description=product.description,
                            price=product.price,
                            category=product.category
                        )
                        session.add(new_product)
                        session.commit()
                        session.refresh(new_product)
                        logger.info(f'Product added to db: {new_product}')
                    
                    elif product.operation == operation_pb2.OperationType.UPDATE:
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

                    elif product.operation == operation_pb2.OperationType.DELETE:
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
        

async def produce_to_confirmation_topic(message):
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        await producer.send_and_wait(KAFKA_CONFIRMATION_TOPIC, message)
    finally:
        await producer.stop()


async def consume_inventory():
    consumer = await create_consumer(KAFKA_INVENTORY_TOPIC)
    if not consumer:
        logger.error("Failed to create kafka inventory consumer")
        return

    try:
        async for msg in consumer:
            try:
                inventory = inventory_pb2.Inventory()
                inventory.ParseFromString(msg.value)
                logger.info(f"Received Inventory Message: {inventory}")

                if inventory.operation == operation_pb2.OperationType.CREATE:
                    # Check if product_id exists in the Product database
                    with Session(engine) as session:
                        existing_product = session.exec(select(Product).where(Product.product_id == inventory.product_id)).first()
                        if existing_product:
                            # If product exists, forward the message to confirmation topic
                            await produce_to_confirmation_topic(msg.value)
                            logger.info(f"Valid Inventory message forwarded to {KAFKA_CONFIRMATION_TOPIC}")
                        else:
                            logger.error(f"Product with ID {inventory.product_id} does not exist. Inventory creation rejected.")

            except Exception as e:
                logger.error(f"Error processing inventory message: {e}")

    finally:
        await consumer.stop()
        logger.info("Inventory consumer stopped")


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