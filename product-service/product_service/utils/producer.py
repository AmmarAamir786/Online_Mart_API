from aiokafka import AIOKafkaProducer
from aiokafka.helpers import ConfluentSchemaRegistry
from product_service.setting import BOOTSTRAP_SERVER, KAFKA_SCHEMA_REGISTRY_URL


async def kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER,
                                schema_registry=ConfluentSchemaRegistry(url=KAFKA_SCHEMA_REGISTRY_URL))
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()