from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import Depends, FastAPI
from aiokafka import AIOKafkaProducer

from inventory_service.proto import inventory_pb2, operation_pb2
from inventory_service.models import InventoryUpdate, Inventory
from inventory_service.setting import KAFKA_INVENTORY_TOPIC

from inventory_service.utils.topic import create_topic
from inventory_service.utils.logger import logger
from inventory_service.utils.producer import kafka_producer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_topic(topic=KAFKA_INVENTORY_TOPIC)
    yield


app = FastAPI(lifespan=lifespan, title="Inventory Service", version='1.0.0')



@app.post('/inventory/')
async def create_inventory(
    inventory: Inventory,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    
    inventory_proto = inventory_pb2.Inventory()
    inventory_proto.product_id = inventory.product_id
    inventory_proto.stock_level = inventory.stock_level
    inventory_proto.operation = operation_pb2.OperationType.CREATE

    logger.info(f"Received Message: {inventory_proto}")

    serialized_inventory = inventory_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_inventory)

    return {"Inventory" : "Created"}


@app.put('/inventory/')
async def edit_inventory(inventory: InventoryUpdate, product_id: int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    logger.info(f"Received product data for update: {inventory}")

    inventory_proto = inventory_pb2.Inventory()
    inventory_proto.product_id = product_id
    inventory_proto.stock_level = inventory.stock_level
    inventory_proto.operation = operation_pb2.OperationType.UPDATE
        
    serialized_inventory = inventory_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_inventory)

    return {"Inventory": "Updated"}
    

@app.delete('/inventory/')
async def delete_inventory(id: int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):
    inventory_proto = inventory_pb2.Inventory()
    inventory_proto.id = id
    inventory_proto.operation = operation_pb2.OperationType.DELETE

    serialized_inventory = inventory_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_INVENTORY_TOPIC, serialized_inventory)

    return {"Inventory" : "Deleted"}