import os
import pathlib
import pandas as pd

# 1. Ensure output directory exists
OUTPUT_DIR = pathlib.Path('output/processed')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# File paths
MERGED_FILE = OUTPUT_DIR / 'spatial_bond_listings_merged.csv'
CLEANED_OUTPUT_FILE = OUTPUT_DIR / 'short_v_long_term_rentals.csv'

# Load the merged dataset
print("Loading merged dataset...")
df = pd.read_csv(MERGED_FILE)

# Drop redundant columns
columns_to_drop = ['join_timeframe_key', 'join_location_key', 'Location Id']
df_cleaned = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')

# Save the cleaned dataset as short_v_long_term_rentals.csv
df_cleaned.to_csv(CLEANED_OUTPUT_FILE, index=False)

print("--- Cleaning Complete ---")
print(f"Original shape: {df.shape}")
print(f"Cleaned shape: {df_cleaned.shape}")
print(f"Saved successfully to: {CLEANED_OUTPUT_FILE}")