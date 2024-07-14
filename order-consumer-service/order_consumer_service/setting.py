from starlette.config import Config
from starlette.datastructures import Secret


try:
    config = Config(".env")

except FileNotFoundError:
    config = Config()

BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)

KAFKA_ORDER_TOPIC = config("KAFKA_ORDER_TOPIC", cast=str)
KAFKA_ORDER_CONSUMER_GROUP_ID = config("KAFKA_ORDER_CONSUMER_GROUP_ID", cast=str)

KAFKA_INVENTORY_RESPONSE_TOPIC = config("KAFKA_INVENTORY_RESPONSE_TOPIC", cast=str)
KAFKA_ORDER_CONFIRMATION_CONSUMER_GROUP_ID = config("KAFKA_ORDER_CONFIRMATION_CONSUMER_GROUP_ID", cast=str)

KAFKA_INVENTORY_UPDATE_TOPIC = config("KAFKA_INVENTORY_UPDATE_TOPIC", cast=str)

DATABASE_URL = config("DATABASE_URL", cast=Secret)
TEST_DATABASE_URL = config("TEST_DATABASE_URL", cast=Secret)