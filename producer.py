import pika
import json

def publish(method, body):
    params = pika.URLParameters('amqp://harouna:Usherbrooke77@10.106.0.2:5673?heartbeat=30')

    # create connection
    connection = pika.BlockingConnection(params)

    # create channel
    channel = connection.channel()

    # declare queue where to send event
    channel.queue_declare(queue='provider_worker', durable=True)
    properties = pika.BasicProperties(method, delivery_mode=2)
    channel.basic_publish(
        exchange='',
        routing_key='provider_worker',
        body=json.dumps(body), 
        properties=properties)
    channel.close()
    connection.close()
