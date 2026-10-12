import os
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Ensure output/plots/short_v_long_term_rentals directory exists
PLOTS_DIR = pathlib.Path('output/plots/short_v_long_term_rentals')
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# 2. Load the cleaned dataset
print("Loading dataset for plotting...")
df = pd.read_csv('output/processed/short_v_long_term_rentals.csv')

# Ensure price gap is computed
if 'price_gap_per_night' not in df.columns:
    df['long_term_daily_rent'] = df['Median Rent'] / 7
    df['price_gap_per_night'] = df['price'] - df['long_term_daily_rent']

# Filter locations with at least 30 listings for statistical robustness in box plots
group_counts = df['location_name'].value_counts()
valid_locations = group_counts[group_counts >= 30].index
df_valid = df[df['location_name'].isin(valid_locations)]

# Get top 12 locations by median price gap among robustly sampled locations
top_groups = df_valid.groupby('location_name')['price_gap_per_night'].median().sort_values(ascending=False).head(12).index.tolist()
df_filtered_box = df_valid[df_valid['location_name'].isin(top_groups)]

# --- Step 1: Price Gap Boxplot (With Outliers) ---
print("Generating Price Gap Boxplot (With Outliers)...")
plt.figure(figsize=(14, 6))
sns.boxplot(
    data=df_filtered_box,
    x='location_name',
    y='price_gap_per_night',
    order=top_groups,
    palette='coolwarm',
    linewidth=1.2
)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.axhline(0, color='red', linestyle='--', linewidth=1.2, label='Equal Price')
plt.title('Short-Term vs Long-Term Rental Price Gap Distribution (With Outliers)', fontsize=14, fontweight='bold')
plt.xlabel('Area / Location', fontsize=12)
plt.ylabel('Price Gap per Night ($)', fontsize=12)
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'price_gap_boxplot.png', dpi=300)
plt.close()

# --- Step 2: Price Gap Boxplot (Without Outliers / Zoomed) ---
print("Generating Price Gap Boxplot (Without Outliers)...")
q_low = df_filtered_box['price_gap_per_night'].quantile(0.01)
q_high = df_filtered_box['price_gap_per_night'].quantile(0.95)
df_zoomed = df_filtered_box[(df_filtered_box['price_gap_per_night'] >= q_low) & (df_filtered_box['price_gap_per_night'] <= q_high)]

plt.figure(figsize=(14, 6))
sns.boxplot(
    data=df_zoomed,
    x='location_name',
    y='price_gap_per_night',
    order=top_groups,
    palette='coolwarm',
    showfliers=False,
    linewidth=1.2
)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.axhline(0, color='red', linestyle='--', linewidth=1.2, label='Equal Price')
plt.title('Short-Term vs Long-Term Rental Price Gap Distribution (Without Outliers)', fontsize=14, fontweight='bold')
plt.xlabel('Area / Location', fontsize=12)
plt.ylabel('Price Gap per Night ($)', fontsize=12)
plt.legend(loc='upper right')
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'price_gap_boxplot_no_outliers.png', dpi=300)
plt.close()

# --- Step 3: Top 10 Locations Barplot by Median Price Gap ---
print("Generating Top 10 Locations Barplot...")
top_10_gap = (
    df.groupby("location_name")["price_gap_per_night"]
    .median()
    .reset_index(name="median_gap")
    .sort_values(by="median_gap", ascending=False)
    .head(10)
)

plt.figure(figsize=(10, 6))
sns.barplot(
    data=top_10_gap,
    x="median_gap",
    y="location_name",
    palette="viridis"
)
plt.title("Top 10 Locations by Median Short vs Long-Term Price Gap", fontsize=14, fontweight='bold')
plt.xlabel("Median Price Gap per Night ($)", fontsize=12)
plt.ylabel("Location / Suburb", fontsize=12)
plt.axvline(0, color="red", linestyle="--", linewidth=1, label="Equal Price")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'top_10_price_gap_bar.png', dpi=300)
plt.close()

# --- Step 4: Comparison of Short Term vs Long Term Rental Supply (Top 15 Strictly) ---
print("Generating Supply Comparison Barplot (Top 15 Strictly)...")
df_totals = df[
    (df["Dwelling Type"] == "ALL") & (df["Number Of Beds"] == "ALL")
]
location_counts = (
    df_totals.groupby("location_name")
    .agg(
        airbnb_property_count=("id", "nunique"),
        rental_property_count=("Active Bonds", "max")
    )
    .reset_index()
    .sort_values(by="airbnb_property_count", ascending=False)
    .head(15)  # Strictly Top 15
)

df_melted = location_counts.melt(
    id_vars="location_name",
    value_vars=["airbnb_property_count", "rental_property_count"],
    var_name="Property Type",
    value_name="Count",
)
df_melted["Property Type"] = df_melted["Property Type"].map(
    {
        "airbnb_property_count": "Short-Term (Airbnb)",
        "rental_property_count": "Long-Term (Active Bonds)"
    }
)

plt.figure(figsize=(12, 7))
sns.barplot(
    data=df_melted,
    x="Count",
    y="location_name",
    hue="Property Type",
    palette="Set2"
)
plt.title("Comparison of Short-Term vs. Long-Term Rental Supply by Location (Top 15)", fontsize=14, fontweight='bold')
plt.xlabel("Number of Properties / Active Bonds", fontsize=12)
plt.ylabel("Location", fontsize=12)
plt.legend(title="Property Type")
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'airbnb_vs_rental_supply.png', dpi=300)
plt.close()

print("--- All plots generated and saved successfully under output/plots/short_v_long_term_rentals/ ---")