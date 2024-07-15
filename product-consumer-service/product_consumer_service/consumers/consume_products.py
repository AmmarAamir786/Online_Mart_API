from product_consumer_service.consumers.consumer import create_consumer

from product_consumer_service.models import Product
from product_consumer_service.db import engine
from product_consumer_service.proto import product_pb2, operation_pb2
from product_consumer_service.setting import KAFKA_PRODUCT_CONSUMER_GROUP_ID, KAFKA_PRODUCT_TOPIC
from product_consumer_service.utils.logger import logger

from sqlmodel import Session, select


async def consume_products():
    consumer = await create_consumer(KAFKA_PRODUCT_TOPIC, KAFKA_PRODUCT_CONSUMER_GROUP_ID)
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
                        existing_product = session.exec(select(Product).where(Product.product_id == product.product_id)).first()
                        if existing_product:
                            logger.warning(f'Product with ID {product.product_id} already exists')
                        else:
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
                            existing_product.product_id = product.product_id
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