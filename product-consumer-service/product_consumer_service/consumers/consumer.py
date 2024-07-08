import asyncio
from aiokafka import AIOKafkaConsumer
from product_consumer_service.setting import BOOTSTRAP_SERVER

import logging

logging.basicConfig(level= logging.INFO)
logger = logging.getLogger(__name__)


MAX_RETRIES = 5
RETRY_INTERVAL = 10


async def create_consumer(topic: str, group_id: str):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=BOOTSTRAP_SERVER,
                group_id=group_id,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=5000
            )
            await consumer.start()
            logger.info(f"Consumer for topic {topic} started successfully.")
            return consumer
        except Exception as e:
            retries += 1
            logger.error(f"Error starting consumer for topic {topic}, retry {retries}/{MAX_RETRIES}: {e}")
            if retries < MAX_RETRIES:
                await asyncio.sleep(RETRY_INTERVAL)
            else:
                logger.error(f"Max retries reached. Could not start consumer for topic {topic}.")
                return None