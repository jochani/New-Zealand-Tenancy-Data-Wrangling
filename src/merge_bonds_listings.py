import os
import pathlib
import pandas as pd

# 1. Ensure output directory exists
OUTPUT_DIR = pathlib.Path('output/processed')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 2. Define file paths with MERGED_FILE
AIRBNB_FILE = pathlib.Path('output/data_sa2/airbnb_listings_spatial.csv')
BOND_FILE = pathlib.Path('output/processed/rental_bonds_cleaned.csv')
MERGED_FILE = OUTPUT_DIR / 'spatial_bond_listings_merged.csv'

# 3. Load the datasets
print("Loading spatial Airbnb listings and cleaned rental bond datasets...")
df_airbnb = pd.read_csv(AIRBNB_FILE)
df_bond = pd.read_csv(BOND_FILE)

# 4. Create standardized join keys for timeframe and location ID
df_airbnb["join_timeframe_key"] = (
    pd.to_datetime(df_airbnb["month_year"], format="%B %Y")
    .dt.to_period("Q")
    .dt.start_time.dt.strftime("%Y-%m-%d")
)
df_airbnb["join_location_key"] = (
    df_airbnb["location_id"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
)

df_bond["join_location_key"] = (
    df_bond["Location Id"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
)

# 5. Execute the inner merge
print("Executing merge between spatial listings and rental bonds...")
df_merged = pd.merge(
    df_airbnb,
    df_bond,
    left_on=["join_location_key", "join_timeframe_key"],
    right_on=["join_location_key", "TimeFrame"],
    how="inner",
)

# 6. Save the final merged dataset
df_merged.to_csv(MERGED_FILE, index=False)

print("--- Merge Complete ---")
print(f"Merged dataset rows: {len(df_merged):,}")
print(f"Saved successfully to: {MERGED_FILE}")