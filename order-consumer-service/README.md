Alright. Lets go with with this model file.
Now
As discussed before
We will hve two consumer groups
For now lets discuss the first consumer.
1st consumer will consume delete data coming from order_topic and will have consumer group id: "kafka_inventory_consumer_group_id". 
This will first check the order_db and check for order_id if it is in db or not. If it is available then 
1- fetches the order data. All the products that were ordered and their quantities.  And send to a new topic "inventory_update_topic". Keep in mind we are doing this because we will send data to inventory consumer service and add back the the quantities of the ordered products. But we will handle the inventory consumer service part later. But do keep in mind what we will be doing.
2- delete the order from order_db

Please write the consumer function the way i write code and keep in mind the order.proto file and way the data is being sent to the topic from order_service.