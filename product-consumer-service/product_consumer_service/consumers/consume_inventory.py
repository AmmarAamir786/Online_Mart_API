import asyncio
import logging

from aiokafka import AIOKafkaProducer
from product_consumer_service.consumers.consumer import create_consumer
from product_consumer_service.models import Product
from product_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_INVENTORY_PRODUCT_CONSUMER_GROUP_ID, KAFKA_INVENTORY_TOPIC, KAFKA_PRODUCT_CONFIRMATION_TOPIC
from sqlmodel import Session, select
from product_consumer_service.proto import inventory_pb2, operation_pb2
from product_consumer_service.db import engine
from aiokafka.errors import KafkaConnectionError
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


MAX_RETRIES = 5
RETRY_INTERVAL = 10

async def create_topic():
    admin_client = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVER)

    retries = 0

    while retries < MAX_RETRIES:
        try:
            await admin_client.start()
            topic_list = [NewTopic(name=KAFKA_PRODUCT_CONFIRMATION_TOPIC,
                                num_partitions=2, 
                                replication_factor=1)]
            try:
                await admin_client.create_topics(new_topics=topic_list, validate_only=False)
                print(f"Topic '{KAFKA_PRODUCT_CONFIRMATION_TOPIC,}' created successfully")
            except Exception as e:
                print(f"Failed to create topic '{KAFKA_PRODUCT_CONFIRMATION_TOPIC}': {e}")
            finally:
                await admin_client.close()
            return
        
        except KafkaConnectionError:
            retries += 1 
            print(f"Kafka connection failed. Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
        
    raise Exception("Failed to connect to kafka broker after several retries")


async def produce_to_confirmation_topic(message):
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        await producer.send_and_wait(KAFKA_PRODUCT_CONFIRMATION_TOPIC, message)
    finally:
        await producer.stop()


async def consume_inventory():
    consumer = await create_consumer(KAFKA_INVENTORY_TOPIC, KAFKA_INVENTORY_PRODUCT_CONSUMER_GROUP_ID)
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
                            logger.info(f"Valid Inventory message forwarded to {KAFKA_PRODUCT_CONFIRMATION_TOPIC}")
                        else:
                            logger.error(f"Product with ID {inventory.product_id} does not exist. Inventory creation rejected.")

            except Exception as e:
                logger.error(f"Error processing inventory message: {e}")

    finally:
        await consumer.stop()
        logger.info("Inventory consumer stopped")