import asyncio
from contextlib import asynccontextmanager
import logging
from typing import Annotated, AsyncGenerator
from fastapi import Depends, FastAPI

from inventory_service import inventory_pb2

from inventory_service.models import InventoryUpdate, Inventory
from inventory_service.setting import BOOTSTRAP_SERVER, KAFKA_INVENTORY_TOPIC
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
            topic_list = [NewTopic(name=KAFKA_INVENTORY_TOPIC,
                                num_partitions=2, 
                                replication_factor=1)]
            try:
                await admin_client.create_topics(new_topics=topic_list, validate_only=False)
                print(f"Topic '{KAFKA_INVENTORY_TOPIC}' created successfully")
            except Exception as e:
                print(f"Failed to create topic '{KAFKA_INVENTORY_TOPIC}': {e}")
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


app = FastAPI(lifespan=lifespan, title="Inventory Service", version='1.0.0')


# @app.get('/')
# async def root() -> Any:
#     return {"message": "Welcome to products section test"}


# logging.basicConfig(level= logging.INFO)
# logger = logging.getLogger(__name__)


@app.post('/inventory/')
async def create_inventory(
    inventory: Inventory,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    
    inventory_proto = inventory_pb2.Inventory()
    inventory_proto.product_id = inventory.product_id
    inventory_proto.stock_level = inventory.stock_level
    inventory_proto.operation = inventory_pb2.OperationType.CREATE

    # logger.info(f"Received Message: {inventory_proto}")

    serialized_inventory = inventory_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_inventory)

    return {"Inventory" : "Created"}


@app.put('/inventory/')
async def edit_inventory(inventory: InventoryUpdate, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    # logger.info(f"Received product data for update: {product}")

    inventory_proto = inventory_pb2.Inventory()
    inventory_proto.id = inventory.id
    inventory_proto.product_id = inventory.product_id
    inventory_proto.stock_level = inventory.stock_level
    inventory_proto.operation = inventory_pb2.OperationType.UPDATE
        
    serialized_inventory = inventory_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_inventory)

    return {"Inventory": "Updated"}
    

@app.delete('/inventory/')
async def delete_inventory(id: int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):
    inventory_proto = inventory_pb2.inventory()
    inventory_proto.id = id
    inventory_proto.operation = inventory_pb2.OperationType.DELETE

    serialized_inventory = inventory_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_inventory)

    return {"Inventory" : "Deleted"}