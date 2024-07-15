from sqlmodel import select

from inventory_consumer_service.consumers.consumer import create_consumer
from inventory_consumer_service.models import Inventory
from inventory_consumer_service.setting import KAFKA_INVENTORY_VALIDATION_GROUP_ID, KAFKA_ORDER_TOPIC, KAFKA_INVENTORY_RESPONSE_TOPIC
from inventory_consumer_service.proto import  operation_pb2, order_pb2
from inventory_consumer_service.db import get_session

from inventory_consumer_service.utils.logger import logger
from inventory_consumer_service.utils.producer import produce_to_confirmation_topic


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