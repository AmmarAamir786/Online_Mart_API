#!/bin/sh

# Check if .env file exists and load environment variables
if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

# Define Kong admin URL
KONG_ADMIN_URL="http://localhost:8001"

# Wait for Kong to be ready
until curl --output /dev/null --silent --head --fail $KONG_ADMIN_URL; do
    printf '.'
    sleep 5
done

# Register services and add routes

# Service: product-service
curl -i -X POST $KONG_ADMIN_URL/services/ \
    --data "name=product-service" \
    --data "url=http://host.docker.internal:8011"

curl -i -X POST $KONG_ADMIN_URL/services/product-service/routes \
    --data "paths[]=/product-service" \
    --data "strip_path=true"

# Service: product-consumer-service
curl -i -X POST $KONG_ADMIN_URL/services/ \
    --data "name=product-consumer-service" \
    --data "url=http://host.docker.internal:8012"

curl -i -X POST $KONG_ADMIN_URL/services/product-consumer-service/routes \
    --data "paths[]=/product-consumer-service" \
    --data "strip_path=true"

# Service: order-service
curl -i -X POST $KONG_ADMIN_URL/services/ \
    --data "name=order-service" \
    --data "url=http://host.docker.internal:8013"

curl -i -X POST $KONG_ADMIN_URL/services/order-service/routes \
    --data "paths[]=/order-service" \
    --data "strip_path=true"

# Service: order-consumer-service
curl -i -X POST $KONG_ADMIN_URL/services/ \
    --data "name=order-consumer-service" \
    --data "url=http://host.docker.internal:8014"

curl -i -X POST $KONG_ADMIN_URL/services/order-consumer-service/routes \
    --data "paths[]=/order-consumer-service" \
    --data "strip_path=true"

# Service: inventory-service
curl -i -X POST $KONG_ADMIN_URL/services/ \
    --data "name=inventory-service" \
    --data "url=http://host.docker.internal:8015"

curl -i -X POST $KONG_ADMIN_URL/services/inventory-service/routes \
    --data "paths[]=/inventory-service" \
    --data "strip_path=true"

# Service: inventory-consumer-service
curl -i -X POST $KONG_ADMIN_URL/services/ \
    --data "name=inventory-consumer-service" \
    --data "url=http://host.docker.internal:8016"

curl -i -X POST $KONG_ADMIN_URL/services/inventory-consumer-service/routes \
    --data "paths[]=/inventory-consumer-service" \
    --data "strip_path=true"

# Service: user-service
curl -i -X POST $KONG_ADMIN_URL/services/ \
    --data "name=user-service" \
    --data "url=http://host.docker.internal:8017"

curl -i -X POST $KONG_ADMIN_URL/services/user-service/routes \
    --data "paths[]=/user-service" \
    --data "strip_path=true"

echo "All services and routes have been registered successfully."