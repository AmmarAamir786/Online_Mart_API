#!/bin/sh

# Install curl
apk update
apk add --no-cache curl

# Wait until Kong is fully up
until curl --output /dev/null --silent --head --fail http://kong:8001; do
    echo "Waiting for Kong to be up..."
    sleep 5
done

# Add services and routes to Kong
services_and_routes="
product-service:8011,products
product-consumer-service:8012,products
"

for entry in $services_and_routes; do
    service=$(echo $entry | cut -d, -f1)
    route=$(echo $entry | cut -d, -f2)
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    # Add service
    curl -i -X POST http://kong:8001/services/ \
        --data "name=${name}" \
        --data "url=http://host.docker.internal:${port}"

    # Add route
    curl -i -X POST http://kong:8001/services/${name}/routes \
        --data "paths[]=/api/${route}" \
        --data "strip_path=false"
done
