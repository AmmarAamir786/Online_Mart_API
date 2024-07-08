import logging

from inventory_consumer_service.consumers.consumer import create_consumer
from inventory_consumer_service.setting import KAFKA_PRODUCT_CONFIRMATION_TOPIC, KAFKA_INVENTORY_CONFIRMATION__CONSUMER_GROUP_ID
from inventory_consumer_service.proto import inventory_pb2, operation_pb2
from inventory_consumer_service.db import engine
from inventory_consumer_service.models import Inventory
from inventory_consumer_service.db import engine
from sqlmodel import Session

logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


async def consume_product_confirmation():
    consumer = await create_consumer(KAFKA_PRODUCT_CONFIRMATION_TOPIC, KAFKA_INVENTORY_CONFIRMATION__CONSUMER_GROUP_ID)
    if not consumer:
        logger.error("Failed to create kafka confirmation consumer")
        return

    try:
        async for msg in consumer:
            try:
                inventory = inventory_pb2.Inventory()
                inventory.ParseFromString(msg.value)
                logger.info(f"Received Inventory Message: {inventory}")

                with Session(engine) as session:
                    if inventory.operation == operation_pb2.OperationType.CREATE:
                        new_inventory = Inventory(
                            product_id=inventory.product_id,
                            stock_level=inventory.stock_level
                        )
                        session.add(new_inventory)
                        session.commit()
                        session.refresh(new_inventory)
                        logger.info(f'Inventory added to db: {new_inventory}')

            except Exception as e:
                logger.error(f"Error processing inventory message: {e}")

    finally:
        await consumer.stop()
        logger.info("Inventory consumer stopped")