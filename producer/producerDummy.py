import pika
import json
import requests
import time

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='',
        port= "",
        credentials=pika.PlainCredentials('guest', 'guest')
    )
)

channel = connection.channel()
channel.queue_declare(queue='queue_name', durable=True)

# DummyJSON pagination
limit = 30  # plus petit batch pour simuler flux
skip = 0

# Récupérer le total
total = requests.get("https://dummyjson.com/products?limit=1").json().get("total", 0)
print("Total produits DummyJSON:", total)

sent_count = 0

def generate_seller_id(product_id):
    return (product_id % 50) + 1

while True:  # boucle infinie pour simuler un flux continu
    url = f"https://dummyjson.com/products?limit={limit}&skip={skip}"
    response = requests.get(url)
    data = response.json()
    products = data.get("products", [])

    if not products:  # si fin du catalogue, recommencer
        skip = 0
        continue

    for product in products:
        mongo_product = {
            "seller_id": generate_seller_id(product["id"]),
            "title": product["title"],
            "price": product["price"],
            "category_id": product["category"],
            "description": product["description"],
            "image": product.get("thumbnail", ""),
            "status": "active"
        }

        # Envoi à RabbitMQ
        channel.basic_publish(
            exchange='',
            routing_key='queue_name',
            body=json.dumps(mongo_product),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(f"Produit envoyé: {mongo_product['title']}")
        sent_count += 1

        time.sleep(0.5)  # délai entre chaque produit pour simuler flux temps réel

    skip += limit
    time.sleep(1)  # délai entre chaque batch
