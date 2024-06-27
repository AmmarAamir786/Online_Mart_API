import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Annotated, AsyncGenerator
from fastapi import Depends, FastAPI

from order_service import order_pb2

from order_service.models import Order, OrderUpdate
from order_service.setting import BOOTSTRAP_SERVER, KAFKA_ORDER_TOPIC
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from aiokafka.admin import AIOKafkaAdminClient, NewTopic


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


@app.get('/')
async def root():
    return {"message": "Welcome to orders section"}


logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


@app.post('/orders/')
async def create_order(
    order: Order,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    
    order_proto = order_pb2.Order()
    order_proto.product_id = order.product_id
    order_proto.quantity = order.quantity

    order_proto.operation = order_pb2.OrderOperationType.CREATE

    logger.info(f"Received Message: {order_proto}")

    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order" : "Created"}


# @app.put('/orders/')
# async def edit_order(order: OrderUpdate, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

#     order_proto = order_pb2.Order()
#     order_proto.id = order.id
#     order_proto.product_id = order.product_id
#     order_proto.quantity = order.quantity

#     order_proto.operation = order_pb2.OrderOperationType.UPDATE

#     logger.info(f"Received order data for update: {order_proto}")
        
#     serialized_order = order_proto.SerializeToString()
#     await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

#     return {"Order": "Updated"}
    

@app.delete('/orders/')
async def delete_order(id: int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):
    order_proto = order_pb2.Order()
    order_proto.id = id
    order_proto.operation = order_pb2.OrderOperationType.DELETE

    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order" : "Deleted"}