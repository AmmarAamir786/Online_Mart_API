from aiokafka import AIOKafkaProducer
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.serialization import ProtobufSerializer

from product_service.setting import BOOTSTRAP_SERVER, KAFKA_SCHEMA_REGISTRY_URL


async def create_kafka_producer():
    schema_registry_client = SchemaRegistryClient({'url': KAFKA_SCHEMA_REGISTRY_URL})
    schema = schema_registry_client.get_latest_version('product-schema')
    protobuf_serializer = ProtobufSerializer(schema_registry_client)

    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVER)
    await producer.start()

    try:
        yield producer, protobuf_serializer
    finally:
        await producer.stop()