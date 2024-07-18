from starlette.config import Config

try:
    config = Config(".env")

except FileNotFoundError:
    config = Config()

BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)
KAFKA_PRODUCT_TOPIC = config("KAFKA_PRODUCT_TOPIC", cast=str)

KAFKA_SCHEMA_REGISTRY_URL = config("KAFKA_SCHEMA_REGISTRY_URL", cast=str)
