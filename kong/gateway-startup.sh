#!/bin/sh

echo "Starting gateway setup..."

# Check if .env file exists and load environment variables
if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

# Define Kong admin URL
KONG_ADMIN_URL="http://localhost:8001"

# Wait for Kong to be ready
echo "Waiting for Kong to be ready..."
until curl --output /dev/null --silent --head --fail $KONG_ADMIN_URL; do
    printf '.'
    sleep 5
done

echo "Kong is ready!"

# Register services and add JWT plugin to each service
echo "Registering product-service..."
curl -i -v -X POST $KONG_ADMIN_URL/services/ \
    --data "name=product-service" \
    --data "url=http://host.docker.internal:8011"

echo "Adding route for product-service..."
curl -i -v -X POST $KONG_ADMIN_URL/services/product-service/routes \
    --data "paths[]=/products" \
    --data "strip_path=true"

echo "Registering product-consumer-service..."
curl -i -v -X POST $KONG_ADMIN_URL/services/ \
    --data "name=product-consumer-service" \
    --data "url=http://host.docker.internal:8012"

echo "Adding route for product-consumer-service..."
curl -i -v -X POST $KONG_ADMIN_URL/services/product-consumer-service/routes \
    --data "paths[]=/products" \
    --data "strip_path=true"

echo "Gateway setup complete."
