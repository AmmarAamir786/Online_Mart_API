from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import Depends, FastAPI

from product_service.proto import product_pb2, operation_pb2

from product_service.models import Product, ProductUpdate
from product_service.setting import KAFKA_PRODUCT_TOPIC
from aiokafka import AIOKafkaProducer
from product_service.utils.producer import kafka_producer
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
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    
    product_proto = product_pb2.Product()
    product_proto.name = product.name
    product_proto.product_id = product.product_id
    product_proto.price = product.price
    product_proto.category = product.category
    product_proto.description = product.description
    product_proto.operation = operation_pb2.OperationType.CREATE

    logger.info(f"Received Message: {product_proto}")

    serialized_product = product_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product" : "Created"}


@app.put('/products')
async def edit_product(product: ProductUpdate, id:int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    logger.info(f"Received product data for update: {product}")

    product_proto = product_pb2.Product()
    product_proto.id = id
    product_proto.product_id = product.product_id
    product_proto.name = product.name
    product_proto.price = product.price
    product_proto.category = product.category
    product_proto.description = product.description
    product_proto.operation = operation_pb2.OperationType.UPDATE
        
    serialized_product = product_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product": "Updated"}
    

@app.delete('/products/')
async def delete_product(id: int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):
    product_proto = product_pb2.Product()
    product_proto.id = id
    product_proto.operation = operation_pb2.OperationType.DELETE

    serialized_product = product_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product" : "Deleted"}