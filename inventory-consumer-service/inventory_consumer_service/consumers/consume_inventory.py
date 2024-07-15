from sqlmodel import Session, select

from inventory_consumer_service.consumers.consumer import create_consumer
from inventory_consumer_service.setting import KAFKA_INVENTORY_CONSUMER_GROUP_ID, KAFKA_INVENTORY_TOPIC
from inventory_consumer_service.db import engine
from inventory_consumer_service.models import Inventory
from inventory_consumer_service.proto import inventory_pb2, operation_pb2
from inventory_consumer_service.utils.logger import logger


async def consume_inventory():
    consumer = await create_consumer(KAFKA_INVENTORY_TOPIC, KAFKA_INVENTORY_CONSUMER_GROUP_ID)
    if not consumer:
        logger.error("Failed to create kafka inventory consumer")
        return

    try:
        async for msg in consumer:
            try:
                inventory = inventory_pb2.Inventory()
                inventory.ParseFromString(msg.value)
                logger.info(f"Received Inventory Message: {inventory}")

                with Session(engine) as session:
                    
                    if inventory.operation == operation_pb2.OperationType.UPDATE:
                        existing_inventory = session.exec(select(Inventory).where(Inventory.product_id == inventory.product_id)).first()
                        if existing_inventory:
                            existing_inventory.stock_level = inventory.stock_level
                            session.add(existing_inventory)
                            session.commit()
                            session.refresh(existing_inventory)
                            logger.info(f'Inventory updated in db: {existing_inventory}')
                        else:
                            logger.warning(f"Inventory with ID {inventory.id} not found")

                    elif inventory.operation == operation_pb2.OperationType.DELETE:
                        existing_inventory = session.exec(select(Inventory).where(Inventory.id == inventory.id)).first()
                        if existing_inventory:
                            session.delete(existing_inventory)
                            session.commit()
                            logger.info(f"Inventory with ID {inventory.id} successfully deleted")
                        else:
                            logger.warning(f"Inventory with ID {inventory.id} not found for deletion")

            except Exception as e:
                logger.error(f"Error processing inventory message: {e}")

    finally:
        await consumer.stop()
        logger.info("Inventory consumer stopped")