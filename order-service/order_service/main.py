from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import Depends, FastAPI

from order_service.utils.producer import kafka_producer
from order_service.utils.topic import create_topic
from order_service.utils.logger import logger
from order_service.utils.uuid import short_uuid

from order_service.proto import order_pb2, operation_pb2
from order_service.models import OrderCreate, OrderUpdate
from order_service.setting import KAFKA_ORDER_TOPIC

from aiokafka import AIOKafkaProducer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_topic(topic=KAFKA_ORDER_TOPIC)
    yield


app = FastAPI(lifespan=lifespan, title="Order Service", version='1.0.0')


@app.post('/orders/')
async def create_order(
    order: OrderCreate,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    order_id = str(short_uuid())
    order_proto = order_pb2.Order()
    order_proto.order_id = order_id
    order_proto.operation = operation_pb2.OperationType.CREATE

    for product in order.products:
        order_product_proto = order_pb2.OrderProduct()
        order_product_proto.product_id = product.product_id
        order_product_proto.quantity = product.quantity
        order_proto.products.append(order_product_proto)

    logger.info(f"Sending order {order_proto} to kafka")

    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order": "Created", "order_id": order_id}


@app.put('/orders/')
async def edit_order(
    order_id: str,
    order_update: OrderUpdate,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    order_proto = order_pb2.Order()
    order_proto.order_id = order_id
    order_proto.operation = operation_pb2.OperationType.UPDATE

    if order_update.products:
        for product in order_update.products:
            order_product_proto = order_pb2.OrderProduct()
            order_product_proto.product_id = product.product_id
            order_product_proto.quantity = product.quantity
            order_proto.products.append(order_product_proto)

    logger.info(f"Sending order {order_proto} update to kafka")

    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order": "Updated"}


@app.delete('/orders/')
async def delete_order(
    order_id: str,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    order_proto = order_pb2.Order()
    order_proto.order_id = order_id
    order_proto.operation = operation_pb2.OperationType.DELETE

    logger.info(f"Sending order {order_proto} to kafka")

    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order": "Deleted"}