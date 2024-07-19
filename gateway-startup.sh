#!/bin/bash

# Wait until Kong is fully up
until $(curl --output /dev/null --silent --head --fail http://localhost:8001); do
    echo "Waiting for Kong to be up..."
    sleep 5
done

# Add product-service and routes
curl -i -X POST http://localhost:8001/services/ \
    --data "name=product-service" \
    --data "url=http://host.docker.internal:8011"

curl -i -X POST http://localhost:8001/services/product-service/routes \
    --data "paths[]=/products" \
    --data "methods[]=POST" \
    --data "methods[]=PUT" \
    --data "methods[]=DELETE" \
    --data "strip_path=false"

# Add product-consumer-service and routes
curl -i -X POST http://localhost:8001/services/ \
    --data "name=product-consumer-service" \
    --data "url=http://host.docker.internal:8012"

curl -i -X POST http://localhost:8001/services/product-consumer-service/routes \
    --data "paths[]=/products" \
    --data "methods[]=GET" \
    --data "strip_path=false"

# Add order-service and routes
curl -i -X POST http://localhost:8001/services/ \
    --data "name=order-service" \
    --data "url=http://host.docker.internal:8013"

curl -i -X POST http://localhost:8001/services/order-service/routes \
    --data "paths[]=/orders" \
    --data "methods[]=POST" \
    --data "methods[]=PUT" \
    --data "methods[]=DELETE" \
    --data "strip_path=false"

# Add order-consumer-service and routes
curl -i -X POST http://localhost:8001/services/ \
    --data "name=order-consumer-service" \
    --data "url=http://host.docker.internal:8014"

curl -i -X POST http://localhost:8001/services/order-consumer-service/routes \
    --data "paths[]=/orders" \
    --data "methods[]=GET" \
    --data "strip_path=false"

# Add inventory-service and routes
curl -i -X POST http://localhost:8001/services/ \
    --data "name=inventory-service" \
    --data "url=http://host.docker.internal:8015"

curl -i -X POST http://localhost:8001/services/inventory-service/routes \
    --data "paths[]=/inventory" \
    --data "methods[]=POST" \
    --data "methods[]=PUT" \
    --data "methods[]=DELETE" \
    --data "strip_path=false"

# Add inventory-consumer-service and routes
curl -i -X POST http://localhost:8001/services/ \
    --data "name=inventory-consumer-service" \
    --data "url=http://host.docker.internal:8016"

curl -i -X POST http://localhost:8001/services/inventory-consumer-service/routes \
    --data "paths[]=/inventory" \
    --data "methods[]=GET" \
    --data "strip_path=false"
