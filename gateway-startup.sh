#!/bin/sh

# Install curl
apk update
apk add --no-cache curl

# Wait until Kong is fully up
until $(curl --output /dev/null --silent --head --fail http://kong:8001); do
    echo "Waiting for Kong to be up..."
    sleep 5
done

# Add services and routes to Kong
declare -A services_and_routes
services_and_routes=(
    ["product-service:8011"]="products"
    ["product-consumer-service:8012"]="products"
    ["order-service:8013"]="orders"
    ["order-consumer-service:8014"]="orders"
    ["inventory-service:8015"]="inventory"
    ["inventory-consumer-service:8016"]="inventory"
)

for service in "${!services_and_routes[@]}"; do
    route="${services_and_routes[$service]}"
    # Add service
    curl -i -X POST http://kong:8001/services/ \
        --data "name=${service}" \
        --data "url=http://${service}"

    # Add route
    curl -i -X POST http://kong:8001/services/${service}/routes \
        --data "paths[]=/api/${route}" \
        --data "strip_path=false"
done