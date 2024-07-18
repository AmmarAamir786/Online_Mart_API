from aiokafka import AIOKafkaProducer

from product_service.setting import BOOTSTRAP_SERVER, KAFKA_SCHEMA_REGISTRY_URL


async def kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)

    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()