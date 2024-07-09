alright this is what i have ended up with
class OrderProduct(BaseModel):
    product_id: int
    quantity: int


class Order(BaseModel):
    order_id: str = Field(default_factory=lambda: str(uuid4()))
    products: List[OrderProduct]
    

class OrderUpdate(BaseModel):
    order_id: str
    products: Optional[List[OrderProduct]] = None


and this is my proto file
syntax = "proto3";

enum OperationType {
  CREATE = 0;
  UPDATE = 1;
  DELETE = 2;
}

message OrderProduct {
  optional int32 product_id = 1;
  optional int32 quantity = 2;
}


message Order {
  optional string order_id = 1;  
  optional repeated OrderProduct products = 2;
  optional OperationType operation = 3;
}


what i have planned is that during post method the user will only write product_ids and its quantities in one order
in edit order they will enter their order_id and then can change product_ids or their products or remove or add products in their orders. and similarly when the user deletes, we ask they the order_id and then it deletes it

these are my post put and delete functions which needed to be updated to my new models.py file and my requirements
@app.post('/orders/')
async def create_order(
    order: Order,
    producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]
):
    
    order_proto = order_pb2.Order()
    order_proto.product_id = order.product_id
    order_proto.quantity = order.quantity

    order_proto.operation = operation_pb2.OperationType.CREATE

    logger.info(f"Received Message: {order_proto}")

    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order" : "Created"}


@app.put('/orders/')
async def edit_order(order: OrderUpdate, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):

    order_proto = order_pb2.Order()
    order_proto.id = order.id
    order_proto.product_id = order.product_id
    order_proto.quantity = order.quantity

    order_proto.operation = operation_pb2.OperationType.UPDATE

    logger.info(f"Received order data for update: {order_proto}")
        
    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order": "Updated"}
    

@app.delete('/orders/')
async def delete_order(id: int, producer: Annotated[AIOKafkaProducer, Depends(kafka_producer)]):
    order_proto = order_pb2.Order()
    order_proto.id = id
    order_proto.operation = operation_pb2.OperationType.DELETE

    serialized_order = order_proto.SerializeToString()
    await producer.send_and_wait(KAFKA_ORDER_TOPIC, serialized_order)

    return {"Order" : "Deleted"}


no need to write other functions just fix post put and delete with respect to my new models.py and order.proto file and my requirements


