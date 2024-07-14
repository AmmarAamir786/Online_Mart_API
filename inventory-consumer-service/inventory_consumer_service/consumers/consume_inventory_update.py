import logging
from inventory_consumer_service.proto import inventory_pb2
from inventory_consumer_service.consumers.consumer import create_consumer
from inventory_consumer_service.models import Inventory
from inventory_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_INVENTORY_CONSUMER_GROUP_ID, KAFKA_INVENTORY_UPDATE_TOPIC, KAFKA_INVENTORY_VALIDATION_GROUP_ID, KAFKA_ORDER_TOPIC, KAFKA_INVENTORY_RESPONSE_TOPIC
from sqlmodel import Session, select
from inventory_consumer_service.proto import  operation_pb2, order_pb2
from inventory_consumer_service.db import engine, get_session
from aiokafka.errors import KafkaConnectionError
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


async def consume_inventory_update():
    consumer = await create_consumer(KAFKA_INVENTORY_UPDATE_TOPIC, KAFKA_INVENTORY_CONSUMER_GROUP_ID)
    if not consumer:
        logger.error("Failed to create kafka inventory update consumer")
        return

    try:
        async for msg in consumer:
            try:
                order = inventory_pb2.Order()
                order.ParseFromString(msg.value)
                logger.info(f"Received Inventory Update Message: {order}")

                with next(get_session()) as session:
                    if order.operation == inventory_pb2.OperationType.CREATE:
                        for order_product in order.products:
                            product_id = order_product.product_id
                            required_quantity = order_product.quantity

                            existing_product = session.exec(select(Inventory).where(Inventory.product_id == product_id)).first()

                            if existing_product:
                                if existing_product.quantity < required_quantity:
                                    logger.error(f"Insufficient quantity for product ID {product_id}. Inventory update failed.")
                                else:
                                    existing_product.quantity -= required_quantity
                                    session.add(existing_product)
                                    logger.info(f"Updated inventory for product ID {product_id}, deducted quantity: {required_quantity}")
                            else:
                                logger.error(f"Product with ID {product_id} does not exist in inventory. Inventory update failed.")

                        session.commit()

                    elif order.operation == inventory_pb2.OperationType.UPDATE:
                        for order_product in order.products:
                            product_id = order_product.product_id
                            quantity_change = order_product.quantity

                            existing_product = session.exec(select(Inventory).where(Inventory.product_id == product_id)).first()

                            if existing_product:
                                existing_product.quantity += quantity_change
                                session.add(existing_product)
                                logger.info(f"Updated inventory for product ID {product_id}, change in quantity: {quantity_change}")
                            else:
                                logger.error(f"Product with ID {product_id} does not exist in inventory. Inventory update failed.")

                        session.commit()

                    elif order.operation == inventory_pb2.OperationType.DELETE:
                        for order_product in order.products:
                            product_id = order_product.product_id
                            added_quantity = order_product.quantity

                            existing_product = session.exec(select(Inventory).where(Inventory.product_id == product_id)).first()

                            if existing_product:
                                existing_product.quantity += added_quantity
                                session.add(existing_product)
                                logger.info(f"Updated inventory for product ID {product_id}, added back quantity: {added_quantity}")
                            else:
                                logger.error(f"Product with ID {product_id} does not exist in inventory. Inventory update failed.")

                        session.commit()

            except Exception as e:
                logger.error(f"Error processing inventory update message: {e}")

    finally:
        await consumer.stop()
        logger.info("Inventory update consumer stopped")