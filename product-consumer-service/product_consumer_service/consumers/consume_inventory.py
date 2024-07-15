from product_consumer_service.consumers.consumer import create_consumer

from product_consumer_service.models import Product
from product_consumer_service.setting import KAFKA_INVENTORY_PRODUCT_CONSUMER_GROUP_ID, KAFKA_INVENTORY_TOPIC, KAFKA_PRODUCT_CONFIRMATION_TOPIC
from product_consumer_service.proto import inventory_pb2, operation_pb2
from product_consumer_service.db import engine

from product_consumer_service.utils.producer import produce_to_confirmation_topic
from product_consumer_service.utils.logger import logger

from sqlmodel import Session, select


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