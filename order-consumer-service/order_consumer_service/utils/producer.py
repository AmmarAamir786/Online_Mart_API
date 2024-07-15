from aiokafka import AIOKafkaProducer
from order_consumer_service.setting import BOOTSTRAP_SERVER, KAFKA_INVENTORY_UPDATE_TOPIC


async def produce_to_inventory_update_topic(message):
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()
    try:
        await producer.send_and_wait(KAFKA_INVENTORY_UPDATE_TOPIC, message)
    finally:
        await producer.stop()