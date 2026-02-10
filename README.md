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


```md
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
