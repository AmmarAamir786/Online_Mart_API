from aiokafka import AIOKafkaProducer
from product_consumer_service.setting import KAFKA_PRODUCT_CONFIRMATION_TOPIC
from product_consumer_service.setting import BOOTSTRAP_SERVER


async def produce_to_confirmation_topic(message):
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        await producer.send_and_wait(KAFKA_PRODUCT_CONFIRMATION_TOPIC, message)
    finally:
        await producer.stop()