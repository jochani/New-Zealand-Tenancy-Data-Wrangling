import os
import pandas as pd

# Load concatenated Christchurch listings
df_airbnb = pd.read_csv("data/christchurch_combined_2025_2026.csv")

# Columns explicitly selected for removal
columns_to_drop = [
    "neighbourhood_group",
    "last_review",
    "reviews_per_month",
    "license",
]

# Drop specified columns while keeping all other columns
df_airbnb_clean = df_airbnb.drop(columns=columns_to_drop, errors="ignore")

os.makedirs("data", exist_ok=True)

# Save cleaned dataset locally
output_path = os.path.join("data", "christchurch_listings_cleaned.csv")
df_airbnb_clean.to_csv(output_path, index=False)

print(f"✔ Christchurch dataset cleaned successfully!")
print(f"  - Initial shape: {df_airbnb.shape}")
print(f"  - Removed: neighbourhood_group, last review, reviews per month, license")
print(f"  - Cleaned shape: {df_airbnb_clean.shape}")
print(f"  - Saved to: {output_path}")

