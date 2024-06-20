from starlette.config import Config

try:
    config = Config(".env")

except FileNotFoundError:
    config = Config()

BOOTSTRAP_SERVER = config("BOOTSTRAP_SERVER", cast=str)
KAFKA_ORDER_TOPIC = config("KAFKA_ORDER_TOPIC", cast=str)

#BOOTSTRAP_SERVER = "broker:19092"
#KAFKA_ORDER_TOPIC = "order_topic"