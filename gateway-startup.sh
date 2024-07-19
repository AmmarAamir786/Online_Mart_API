#!/bin/bash

# Wait until Kong is fully up
until $(curl --output /dev/null --silent --head --fail http://localhost:8001); do
    echo "Waiting for Kong to be up..."
    sleep 5
done

# Add services and routes to Kong
services=("product-service:8011" "product-consumer-service:8012" "order-service:8013" "order-consumer-service:8014" "inventory-service:8015" "inventory-consumer-service:8016")
routes=("products" "products" "orders" "orders" "inventory" "inventory")

for i in "${!services[@]}"; do
    service="${services[$i]}"
    route="${routes[$i]}"
    method=""

    if [[ "$route" == "products" ]]; then
        if [[ "$service" == "product-service:8011" ]]; then
            method="POST,PUT,DELETE"
        else
            method="GET"
        fi
    elif [[ "$route" == "orders" ]]; then
        if [[ "$service" == "order-service:8013" ]]; then
            method="POST,PUT,DELETE"
        else
            method="GET"
        fi
    elif [[ "$route" == "inventory" ]]; then
        if [[ "$service" == "inventory-service:8015" ]]; then
            method="POST,PUT,DELETE"
        else
            method="GET"
        fi
    fi

    # Add service
    curl -i -X POST http://localhost:8001/services/ \
        --data "name=${route}-${service}" \
        --data "url=http://${service}"

    # Add route
    curl -i -X POST http://localhost:8001/services/${route}-${service}/routes \
        --data "paths[]=/api/${route}" \
        --data "methods[]=${method}" \
        --data "strip_path=false"
done