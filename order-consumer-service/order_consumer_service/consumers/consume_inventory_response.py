from sqlmodel import select

from order_consumer_service.consumers.consumer import create_consumer
from order_consumer_service.setting import KAFKA_INVENTORY_UPDATE_TOPIC, KAFKA_INVENTORY_RESPONSE_TOPIC, KAFKA_ORDER_CONFIRMATION_CONSUMER_GROUP_ID
from order_consumer_service.proto import order_pb2, operation_pb2
from order_consumer_service.models import Order, OrderProduct
from order_consumer_service.db import get_session

from order_consumer_service.utils.producer import produce_to_inventory_update_topic
from order_consumer_service.utils.logger import logger


async def consume_inventory_response():
    consumer = await create_consumer(KAFKA_INVENTORY_RESPONSE_TOPIC, KAFKA_ORDER_CONFIRMATION_CONSUMER_GROUP_ID)
    if not consumer:
        logger.error("Failed to create kafka inventory response consumer")
        return

    try:
        async for msg in consumer:
            try:
                order = order_pb2.Order()
                order.ParseFromString(msg.value)
                logger.info(f"Received Order Message: {order}")

                with next(get_session()) as session:
                    if order.operation == operation_pb2.OperationType.CREATE:
                        existing_order = session.exec(select(Order).where(Order.order_id == order.order_id)).first()
                        
                        if existing_order:
                            logger.error(f"Order with ID {order.order_id} already exists. Order creation failed.")
                        else:
                            new_order = Order(order_id=order.order_id, products=[
                                OrderProduct(product_id=product.product_id, quantity=product.quantity)
                                for product in order.products
                            ])
                            session.add(new_order)
                            session.commit()
                            logger.info(f"Order with ID {order.order_id} added to order_db")

                            serialized_order = order.SerializeToString()
                            await produce_to_inventory_update_topic(serialized_order)
                            logger.info(f"Sent order {order.order_id} to {KAFKA_INVENTORY_UPDATE_TOPIC}")

                    elif order.operation == operation_pb2.OperationType.UPDATE:
                        existing_order = session.exec(select(Order).where(Order.order_id == order.order_id)).first()
                        
                        if not existing_order:
                            logger.error(f"Order with ID {order.order_id} does not exist. Order update failed.")
                        else:
                            # Prepare inventory update message with quantity adjustments
                            inventory_update_order = order_pb2.Order()
                            inventory_update_order.order_id = order.order_id
                            inventory_update_order.operation = operation_pb2.OperationType.UPDATE

                            # Revert quantities of existing products in the order
                            for existing_product in existing_order.products:
                                inventory_update_order.products.append(order_pb2.OrderProduct(
                                    product_id=existing_product.product_id,
                                    quantity=-existing_product.quantity
                                ))

                            # Update existing order with new quantities and prepare the new order message
                            new_order_products = []
                            for product in order.products:
                                inventory_update_order.products.append(order_pb2.OrderProduct(
                                    product_id=product.product_id,
                                    quantity=product.quantity
                                ))
                                new_order_products.append(OrderProduct(
                                    product_id=product.product_id,
                                    quantity=product.quantity,
                                    order_id=order.order_id
                                ))

                            existing_order.products = new_order_products
                            session.commit()
                            logger.info(f"Order with ID {order.order_id} updated in order_db")

                            serialized_inventory_update_order = inventory_update_order.SerializeToString()
                            await produce_to_inventory_update_topic(serialized_inventory_update_order)
                            logger.info(f"Sent inventory update message for order {order.order_id} to {KAFKA_INVENTORY_UPDATE_TOPIC}")

            except Exception as e:
                logger.error(f"Error processing order message: {e}")

    finally:
        await consumer.stop()
        logger.info("Inventory response consumer stopped")