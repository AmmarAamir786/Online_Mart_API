import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Annotated, AsyncGenerator
from fastapi import Depends, FastAPI

from product_service import product_pb2

from product_service.models import Product, ProductUpdate
from product_service.setting import BOOTSTRAP_SERVER, KAFKA_PRODUCT_TOPIC
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
            topic_list = [NewTopic(name=KAFKA_PRODUCT_TOPIC,
                                num_partitions=2, 
                                replication_factor=1)]
            try:
                await admin_client.create_topics(new_topics=topic_list, validate_only=False)
                print(f"Topic '{KAFKA_PRODUCT_TOPIC}' created successfully")
            except Exception as e:
                print(f"Failed to create topic '{KAFKA_PRODUCT_TOPIC}': {e}")
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


app = FastAPI(lifespan=lifespan, title="Product Service", version='1.0.0')


# @app.get('/')
# async def root() -> Any:
#     return {"message": "Welcome to products section test"}


# logging.basicConfig(level= logging.INFO)
# logger = logging.getLogger(__name__)


@app.post('/products/')
async def create_product(
    product: Product,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    
    product_proto = product_pb2.Product()
    product_proto.name = product.name
    product_proto.price = product.price
    product_proto.quantity = product.quantity
    product_proto.description = product.description
    product_proto.operation = product_pb2.OperationType.CREATE

    # logger.info(f"Received Message: {product_proto}")

    serialized_product = product_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product" : "Created"}


@app.put('/products/')
async def edit_product(product: ProductUpdate, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    # logger.info(f"Received product data for update: {product}")

    product_proto = product_pb2.Product()
    product_proto.id = product.id
    product_proto.name = product.name
    product_proto.price = product.price
    product_proto.quantity = product.quantity
    product_proto.description = product.description
    product_proto.operation = product_pb2.OperationType.UPDATE
        
    serialized_product = product_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product": "Updated"}
    

@app.delete('/products/')
async def delete_product(id: int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):
    product_proto = product_pb2.Product()
    product_proto.id = id
    product_proto.operation = product_pb2.OperationType.DELETE

    serialized_product = product_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_PRODUCT_TOPIC, serialized_product)

    return {"Product" : "Deleted"}