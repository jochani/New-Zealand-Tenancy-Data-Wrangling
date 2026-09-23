import pandas as pd

df = pd.read_excel("output/processed/christchurch_airbnb_clean_with_sa2.xlsx")

central = df[
    df["location_id"].astype(str).str.replace(
        r"\.0$", "", regex=True
    ) == "326600"
].copy()

central["price"] = pd.to_numeric(
    central["price"], errors="coerce"
)

print("Christchurch Central")
print("Total observations:", len(central))
print("Observations with prices:", central["price"].notna().sum())
print("Median nightly price: NZ$", central["price"].median())

print("\nMonthly median prices:")
print(central.groupby("month_year")["price"].median())