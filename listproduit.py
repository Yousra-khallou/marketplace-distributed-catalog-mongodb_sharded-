import pandas as pd

# Charger les CSV
products = pd.read_csv("olist_products_dataset.csv")
items = pd.read_csv("olist_order_items_dataset.csv")

# Garder uniquement les colonnes importantes
items_clean = items[["product_id", "seller_id", "price"]].drop_duplicates()

# Fusionner produits + seller_id + price
merged = pd.merge(products, items_clean, on="product_id", how="left")

# Supprimer les lignes sans vendeur ou prix
merged = merged.dropna(subset=["seller_id", "price"])

# Convertir seller_id en string pour MongoDB (par sécurité)
merged["seller_id"] = merged["seller_id"].astype(str)

# Sauvegarder le fichier final
merged.to_csv("products_with_seller_price.csv", index=False)

print("Fichier généré : products_with_seller_price.csv")
print("Nombre de produits :", len(merged))
print("Colonnes :", merged.columns.tolist())
