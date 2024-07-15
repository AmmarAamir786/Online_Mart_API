from aiokafka import AIOKafkaProducer
from order_service.setting import BOOTSTRAP_SERVER


async def kafka_producer():
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        yield producer
    finally:
        await producer.stop()