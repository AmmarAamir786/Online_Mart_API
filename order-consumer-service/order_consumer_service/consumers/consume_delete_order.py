from sqlmodel import select

from order_consumer_service.consumers.consumer import create_consumer
from order_consumer_service.setting import KAFKA_INVENTORY_UPDATE_TOPIC, KAFKA_ORDER_CONSUMER_GROUP_ID, KAFKA_ORDER_TOPIC
from order_consumer_service.proto import order_pb2
from order_consumer_service.models import Order
from order_consumer_service.db import get_session

from order_consumer_service.utils.logger import logger
from order_consumer_service.utils.producer import produce_to_inventory_update_topic


async def consume_delete_order():
    consumer = await create_consumer(KAFKA_ORDER_TOPIC, KAFKA_ORDER_CONSUMER_GROUP_ID)
    if not consumer:
        logger.error("Failed to create kafka inventory consumer")
        return

    try:
        async for msg in consumer:
            try:
                order = order_pb2.Order()
                order.ParseFromString(msg.value)
                logger.info(f"Received Order Message: {order}")

                if order.operation == order_pb2.OperationType.DELETE:
                    with next(get_session()) as session:
                        existing_order = session.exec(select(Order).where(Order.order_id == order.order_id)).first()
                        
                        if existing_order:
                            # Prepare inventory update message
                            inventory_update_order = order_pb2.Order()
                            inventory_update_order.order_id = existing_order.order_id
                            inventory_update_order.operation = order_pb2.OperationType.DELETE
                            
                            for product in existing_order.products:
                                order_product_proto = order_pb2.OrderProduct()
                                order_product_proto.product_id = product.product_id
                                order_product_proto.quantity = product.quantity
                                inventory_update_order.products.append(order_product_proto)
                            
                            serialized_inventory_update_order = inventory_update_order.SerializeToString()
                            await produce_to_inventory_update_topic(serialized_inventory_update_order)
                            logger.info(f"Sent inventory update message for order {existing_order.order_id} to {KAFKA_INVENTORY_UPDATE_TOPIC}")

                            # Delete the order from order_db
                            session.delete(existing_order)
                            session.commit()
                            logger.info(f"Order with ID {order.order_id} deleted from order_db")

            except Exception as e:
                logger.error(f"Error processing order message: {e}")

    finally:
        await consumer.stop()
        logger.info("Order consumer stopped")