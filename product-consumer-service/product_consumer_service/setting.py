from starlette.config import Config
from starlette.datastructures import Secret


try:
    config = Config(".env")

except FileNotFoundError:
    config = Config()

BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)

KAFKA_PRODUCT_TOPIC = config("KAFKA_PRODUCT_TOPIC", cast=str)
KAFKA_PRODUCT_CONSUMER_GROUP_ID = config("KAFKA_PRODUCT_CONSUMER_GROUP_ID", cast=str)

# KAFKA_INVENTORY_TOPIC = config("KAFKA_INVENTORY_TOPIC", cast=str)
# KAFKA_INVENTORY_PRODUCT_CONSUMER_GROUP_ID = config("KAFKA_INVENTORY_PRODUCT_CONSUMER_GROUP_ID", cast=str)

KAFKA_PRODUCT_CONFIRMATION_TOPIC = config("KAFKA_PRODUCT_CONFIRMATION_TOPIC", cast=str)

DATABASE_URL = config("DATABASE_URL", cast=Secret)
TEST_DATABASE_URL = config("TEST_DATABASE_URL", cast=Secret)