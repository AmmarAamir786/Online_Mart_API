import asyncio
import logging

from aiokafka import AIOKafkaProducer
from inventory_consumer_service.consumers.consumer import create_consumer
from inventory_consumer_service.models import Inventory
from product_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_INVENTORY_TOPIC, KAFKA_INVENTORY_CONSUMER_GROUP_ID, KAFKA_PRODUCT_CONFIRMATION_TOPIC, KAFKA_INVENTORY_CONFIRMATION__CONSUMER_GROUP_ID, KAFKA_INVENTORY_VALIDATION_GROUP_ID, KAFKA_ORDER_TOPIC, KAFKA_INVENTORY_RESPONSE_TOPIC
from sqlmodel import Session, select
from inventory_consumer_service.proto import  operation_pb2, order_pb2
from inventory_consumer_service.db import engine, get_session
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
            topic_list = [NewTopic(name=KAFKA_INVENTORY_RESPONSE_TOPIC,
                                num_partitions=2, 
                                replication_factor=1)]
            try:
                await admin_client.create_topics(new_topics=topic_list, validate_only=False)
                print(f"Topic '{KAFKA_INVENTORY_RESPONSE_TOPIC,}' created successfully")
            except Exception as e:
                print(f"Failed to create topic '{KAFKA_INVENTORY_RESPONSE_TOPIC}': {e}")
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
        await producer.send_and_wait(KAFKA_INVENTORY_RESPONSE_TOPIC, message)
    finally:
        await producer.stop()


async def consume_validation():
    consumer = await create_consumer(KAFKA_ORDER_TOPIC, KAFKA_INVENTORY_VALIDATION_GROUP_ID)
    if not consumer:
        logger.error("Failed to create Kafka inventory consumer")
        return

    try:
        async for msg in consumer:
            try:
                order = order_pb2.Order()
                order.ParseFromString(msg.value)
                logger.info(f"Received Order Message: {order}")

                if order.operation in (operation_pb2.OperationType.CREATE, operation_pb2.OperationType.UPDATE):
                    valid_order = True

                    with next(get_session()) as session:
                        for order_product in order.products:
                            product_id = order_product.product_id
                            required_quantity = order_product.quantity

                            existing_product = session.exec(select(Inventory).where(Inventory.product_id == product_id)).first()

                            if not existing_product:
                                valid_order = False
                                logger.error(f"Product with ID {product_id} does not exist. Order validation failed.")
                                break

                            if existing_product.quantity < required_quantity:
                                valid_order = False
                                logger.error(f"Insufficient quantity for product ID {product_id}. Order validation failed.")
                                break

                    if valid_order:
                        await produce_to_confirmation_topic(msg.value)
                        logger.info(f"Valid Order message forwarded to {KAFKA_INVENTORY_RESPONSE_TOPIC}")

            except Exception as e:
                logger.error(f"Error processing order message: {e}")

    finally:
        await consumer.stop()
        logger.info("Order consumer stopped")