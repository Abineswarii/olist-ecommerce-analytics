import pandas as pd

file_path = "data/raw/olist_orders_dataset.csv"

orders = pd.read_csv(file_path)

print("Rows:", len(orders))
print("Columns:")
print(orders.columns.tolist())

print("\nFirst 5 rows:")
print(orders.head())