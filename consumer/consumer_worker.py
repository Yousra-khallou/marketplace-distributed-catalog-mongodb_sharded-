import os
import json
import pika
from pymongo import MongoClient

# donnees de connexion RabbitMQ
rabbit_host = os.getenv("", "")
rabbit_port = int(os.getenv("T", ))

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        credentials=pika.PlainCredentials('guest', 'guest')
    )
)

channel = connection.channel()
channel.queue_declare(queue='', durable=True)

# donnees de connexion MongoDB
mongos_host = os.getenv("","")
mongos_port = int(os.getenv("", ))
mongo_db_name = os.getenv("", "")

mongo_client = MongoClient(f"mongodb://{mongos_host}:{mongos_port}")
db = mongo_client[mongo_db_name]
collection = db.products

# Callback
def callback(ch, method, properties, body):
    product = json.loads(body)
    collection.insert_one(product)
    print(f"Produit insere: {product}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='queue name', on_message_callback=callback)

print('En attente des produits depuis RabbitMQ...')
channel.start_consuming()
