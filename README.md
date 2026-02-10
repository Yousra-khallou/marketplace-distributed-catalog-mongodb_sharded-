🛒 Marketplace Distributed Catalog — MongoDB Sharded

Ce projet implémente un catalogue distribué pour une marketplace basé sur MongoDB Sharding, avec une architecture orientée Data Engineering intégrant des producers/consumers pour l’ingestion et le traitement des données produits à grande échelle.

Il s’inscrit dans une logique Big Data & scalabilité horizontale, adaptée aux plateformes e-commerce manipulant de gros volumes de données.

🚀 Objectifs du projet

Mettre en place un cluster MongoDB sharded

Distribuer les données produits sur plusieurs shards

Simuler un pipeline de données via des producteurs et consommateurs

Analyser et visualiser les données d’une marketplace

Appliquer des concepts clés de Data Engineering

🧠 Technologies utilisées

MongoDB (Sharding)

Docker & Docker Compose

Python

Architecture Producer / Consumer

Datasets e-commerce (Olist)

🏗️ Architecture globale
        CSV Datasets
             |
         Producer
             |
      MongoDB Router (mongos)
             |
   ┌─────────┼─────────┐
   |         |         |
 Shard 1   Shard 2   Shard 3


Producer : ingestion et envoi des données produits

Consumer : traitement et insertion dans MongoDB

MongoDB Sharded Cluster : distribution horizontale des données

📁 Structure du projet
marketplace-distributed-catalog-mongodb_sharded/
│
├── consumer/
│   └── consumer_worker.py        # Traitement des données consommées
│
├── producer/
│   └── (scripts producer)        # Envoi des données vers MongoDB
│
├── docker-compose.yml             # Déploiement du cluster MongoDB sharded
├── listproduit.py                 # Gestion / listing des produits
├── marketplace_dashboard.py       # Visualisation / dashboard marketplace
│
├── olist_order_items_dataset.csv  # Dataset commandes
├── olist_products_dataset.csv     # Dataset produits
├── products_with_seller_price.csv # Dataset enrichi
│
├── rapport mongodb sharding.pdf   # Rapport explicatif du projet
├── .gitignore
└── README.md

📊 Datasets

Les données utilisées proviennent du dataset Olist (e-commerce) :

Produits

Commandes

Prix vendeurs

Données enrichies pour analyse marketplace

Ces datasets permettent de simuler un catalogue réel à grande échelle.

⚙️ Lancer le projet
1️⃣ Cloner le dépôt
git clone https://github.com/Yousra-khallou/marketplace-distributed-catalog-mongodb_sharded.git
cd marketplace-distributed-catalog-mongodb_sharded

2️⃣ Démarrer le cluster MongoDB sharded
docker compose up -d

3️⃣ Initialiser le sharding (mongosh)
sh.enableSharding("marketplaceDB")
sh.shardCollection("marketplaceDB.products", { product_id: "hashed" })

🔄 Pipeline Producer / Consumer

Producer :

Lit les fichiers CSV

Prépare et envoie les données

Consumer :

Consomme les données

Insère les documents dans MongoDB sharded

Garantit la distribution sur les shards

📈 Dashboard & Analyse

Le script marketplace_dashboard.py permet :

L’analyse des produits

La visualisation des prix

L’exploration des données marketplace

🧪 Vérification du sharding

Dans mongosh :

sh.status()
db.products.getShardDistribution()

📄 Rapport

Le fichier rapport mongodb sharding.pdf détaille :

Le concept de sharding

L’architecture choisie

Les choix techniques

Les résultats et limites

🎯 Compétences mises en valeur

✔ Data Engineering
✔ Big Data Architecture
✔ MongoDB Sharding
✔ Docker
✔ Python
✔ Streaming (Producer / Consumer)

🤝 Contribution

Les contributions sont les bienvenues :

Optimisation du pipeline

Ajout de nouveaux dashboards

Amélioration des performances

📜 Licence

Projet académique / pédagogique — libre d’utilisation à des fins éducatives.

⭐ Si ce projet vous a été utile, n'hésitez pas à lui donner une étoile !
Développé avec ❤️ dans le cadre d'un cours de Big Data
