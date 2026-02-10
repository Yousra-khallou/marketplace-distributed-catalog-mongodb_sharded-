# 🛒 Marketplace Distributed Catalog — MongoDB Sharded

Ce projet met en place un **catalogue distribué pour une marketplace** basé sur
**MongoDB Sharding**, en suivant une approche **Data Engineering & Big Data**.

Il combine un **pipeline Producer / Consumer** pour l’ingestion des données et
un **cluster MongoDB sharded** pour assurer la scalabilité horizontale.

---

## 🚀 Objectifs du projet

- Implémenter un **cluster MongoDB sharded**
- Distribuer les données produits sur plusieurs shards
- Mettre en place un **pipeline Producer / Consumer**
- Analyser et visualiser les données d’une marketplace
- Appliquer des concepts clés du **Data Engineering**

---

## 🧠 Technologies utilisées

- MongoDB (Sharding)
- Docker & Docker Compose
- Python
- Architecture Producer / Consumer
- Datasets e-commerce (Olist)

---

## 🏗️ Architecture du projet

Le système est composé de deux parties principales :
1. Un **pipeline de données** (Producer / Consumer)
2. Un **cluster MongoDB sharded** pour le stockage distribué

### Architecture globale

```text
                 CSV Datasets
        (products, orders, prices)
                        |
                    Producer
                        |
                Consumer Worker
                        |
                 MongoDB Router
                      (mongos)
                        |
        ┌───────────────┼───────────────┐
        |               |               |
     Shard 1          Shard 2          Shard 3
   (Replica Set)   (Replica Set)   (Replica Set)

Explication

Producer : lit les fichiers CSV et envoie les données.

Consumer : traite les données et les insère dans MongoDB.

mongos : route les requêtes vers le bon shard.

Shards : stockent les données de façon distribuée.


## ⚙️ Lancer le projet

### 1️⃣ Cloner le dépôt
```bash
git clone https://github.com/Yousra-khallou/marketplace-distributed-catalog-mongodb_sharded.git
cd marketplace-distributed-catalog-mongodb_sharded
2️⃣ Démarrer le cluster MongoDB sharded
docker compose up -d
Assurez-vous que tous les conteneurs sont bien lancés avant de continuer.

3️⃣ Initialiser le sharding (mongosh)
sh.enableSharding("marketplaceDB")
sh.shardCollection("marketplaceDB.products", { product_id: "hashed" })
🔄 Pipeline Producer / Consumer
Le Producer lit les fichiers CSV de la marketplace.

Le Consumer traite les données reçues.

Les données sont automatiquement distribuées sur les shards MongoDB.

Ce pipeline simule une ingestion de données à grande échelle,
typique des architectures Data Engineering.

📈 Dashboard Marketplace
Le script marketplace_dashboard.py permet :

L’analyse des produits

La visualisation des prix

L’exploration des données marketplace

📄 Rapport
Le fichier rapport mongodb sharding.pdf contient :

Une explication détaillée du sharding MongoDB

L’architecture du projet

Les choix techniques

Les résultats obtenus

🎯 Compétences mises en valeur
Data Engineering

Big Data

MongoDB Sharding

Docker & Docker Compose

Python

Architecture distribuée


