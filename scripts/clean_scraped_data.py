import pandas as pd

df = pd.read_csv("data/raw/flights_scraped.csv")

allowed_airlines = ["American", "Delta", "JetBlue", "Spirit", "United"]

df = df[df["airline"].isin(allowed_airlines)]
df = df[(df["price"] >= 50) & (df["price"] <= 1500)]
df["stops"] = pd.to_numeric(df["stops"], errors="coerce")

df = df.dropna(subset=["airline", "price", "stops"])
df = df.drop_duplicates()

df.to_csv("data/processed/flights_final.csv", index=False)

print(df.head(20))
print("Rows after cleaning:", len(df))
print("Saved to data/processed/flights_final.csv")