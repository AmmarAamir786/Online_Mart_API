FROM alpine:latest

RUN apk add --no-cache curl bash

WORKDIR /app

COPY gateway-startup.sh .
RUN chmod +x gateway-startup.sh

ENTRYPOINT ["/bin/sh", "/app/gateway-startup.sh"]
