import os
import pandas as pd

# 1. Ensure the output directory exists
os.makedirs('output/processed', exist_ok=True)

# 2. Load the reference spatial dataset to get Christchurch location IDs
airbnb_df = pd.read_csv('output/data_sa2/airbnb_listings_spatial.csv')

# Extract unique location IDs from the Airbnb spatial reference
chch_location_ids = airbnb_df['location_id'].dropna().astype(int).unique()
print(f"Loaded {len(chch_location_ids)} unique Christchurch location IDs from reference dataset.")

# 3. Load the nationwide rental bond dataset
bond_df = pd.read_csv('data/bond/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv')

# 4. Clean and Standardize the Rental Bond Data
# Ensure 'Location Id' is numeric (coercing errors to NaN)
bond_df['Location Id'] = pd.to_numeric(bond_df['Location Id'], errors='coerce')

# Drop exact duplicate rows if any exist
initial_rows = len(bond_df)
bond_df = bond_df.drop_duplicates()
print(f"Dropped {initial_rows - len(bond_df)} duplicate rows from nationwide data.")

# 5. Filter Rental Bond Data strictly to Christchurch location IDs
chch_bonds_df = bond_df[bond_df['Location Id'].isin(chch_location_ids)].copy()

# Sort strictly by Location Id
chch_bonds_df = chch_bonds_df.sort_values(by=['Location Id']).reset_index(drop=True)

print(f"Filtered Christchurch bond dataset shape: {chch_bonds_df.shape}")

# 6. Save the cleaned and filtered dataset to the specified directory
output_path = 'output/processed/rental_bonds_cleaned.csv'
chch_bonds_df.to_csv(output_path, index=False)
print(f"Successfully saved cleaned dataset to '{output_path}'.")