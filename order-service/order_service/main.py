import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Annotated, AsyncGenerator
from uuid import uuid4
from fastapi import Depends, FastAPI

from order_service.proto import order_pb2, operation_pb2

from order_service.models import OrderCreate, OrderUpdate, Order, OrderProduct
from order_service.setting import BOOTSTRAP_SERVER, KAFKA_ORDER_TOPIC
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from aiokafka.admin import AIOKafkaAdminClient, NewTopic


logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


MAX_RETRIES = 5
RETRY_INTERVAL = 10


async def create_topic():
    admin_client = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVER)

    retries = 0

    while retries < MAX_RETRIES:
        try:
            await admin_client.start()
            topic_list = [NewTopic(name=KAFKA_ORDER_TOPIC,
                                num_partitions=2, 
                                replication_factor=1)]
            try:
                await admin_client.create_topics(new_topics=topic_list, validate_only=False)
                print(f"Topic '{KAFKA_ORDER_TOPIC}' created successfully")
            except Exception as e:
                print(f"Failed to create topic '{KAFKA_ORDER_TOPIC}': {e}")
            finally:
                await admin_client.close()
            return
        
        except KafkaConnectionError:
            retries += 1 
            print(f"Kafka connection failed. Retrying {retries}/{MAX_RETRIES}...")
            await asyncio.sleep(RETRY_INTERVAL)
        
    raise Exception("Failed to connect to kafka broker after several retries")


async def kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_topic()
    yield


app = FastAPI(lifespan=lifespan, title="Order Service", version='1.0.0')


@app.post('/orders/')
async def create_order(
    order: OrderCreate,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    order_id = str(uuid4())
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
    order: OrderUpdate,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    order_proto = order_pb2.Order()
    order_proto.order_id = order.order_id
    order_proto.operation = operation_pb2.OperationType.UPDATE

    if order.products:
        for product in order.products:
            order_product_proto = order_pb2.OrderProduct()
            order_product_proto.product_id = product.product_id
            order_product_proto.quantity = product.quantity
            order_proto.products.append(order_product_proto)

    logger.info(f"Sending order {order_proto} to kafka")

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