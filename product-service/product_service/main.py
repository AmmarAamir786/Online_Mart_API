from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import Depends, FastAPI

from product_service.proto import product_pb2, operation_pb2
from product_service.models import Product, ProductUpdate
from product_service.setting import KAFKA_PRODUCT_TOPIC

from product_service.utils.producer import create_kafka_producer
from product_service.utils.topic import create_topic
from product_service.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_topic(topic=KAFKA_PRODUCT_TOPIC)
    yield


app = FastAPI(lifespan=lifespan, title="Product Service", version='1.0.0')


@app.post('/products/')
async def create_product(
    product: Product,
    producer_dep: Annotated[tuple, Depends(create_kafka_producer)]):
    
    producer, protobuf_serializer = producer_dep
    product_proto = product_pb2.Product(
        name=product.name,
        product_id=product.product_id,
        price=product.price,
        category=product.category,
        description=product.description,
        operation=operation_pb2.OperationType.CREATE
    )

    logger.info(f"Received Message: {product_proto}")
    serialized_product = protobuf_serializer(product_proto, None)
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product": "Created"}


@app.put('/products')
async def edit_product(
    product: ProductUpdate, 
    id: int, 
    producer_dep: Annotated[tuple, Depends(create_kafka_producer)]):

    producer, protobuf_serializer = producer_dep
    logger.info(f"Received product data for update: {product}")

    product_proto = product_pb2.Product(
        id=id,
        product_id=product.product_id,
        name=product.name,
        price=product.price,
        category=product.category,
        description=product.description,
        operation=operation_pb2.OperationType.UPDATE
    )
    
    serialized_product = protobuf_serializer(product_proto, None)
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product": "Updated"}


@app.delete('/products/')
async def delete_product(
    id: int, 
    producer_dep: Annotated[tuple, Depends(create_kafka_producer)]):

    producer, protobuf_serializer = producer_dep

    product_proto = product_pb2.Product(
        id=id, 
        operation=operation_pb2.OperationType.DELETE
    )

    serialized_product = protobuf_serializer(product_proto, None)
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product": "Deleted"}