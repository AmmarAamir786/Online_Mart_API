from aiokafka import AIOKafkaProducer
from inventory_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_INVENTORY_RESPONSE_TOPIC


async def produce_to_confirmation_topic(message):
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        await producer.send_and_wait(KAFKA_INVENTORY_RESPONSE_TOPIC, message)
    finally:
        await producer.stop()
