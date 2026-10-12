import os
import pathlib
import pandas as pd

# Output directories
ANALYSIS_DIR = pathlib.Path('output/analysis')
SUMMARIES_DIR = pathlib.Path('output/summaries')
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

# Input file path
MERGED_FILE = pathlib.Path('output/processed/short_v_long_term_rentals.csv')
print("Loading cleaned short vs long-term rentals dataset...")
df = pd.read_csv(MERGED_FILE)

summary_report = []
summary_report.append("=== SHORT VS LONG-TERM RENTALS ANALYSIS SUMMARY ===")

# Calculate median price of Christchurch Central (location id = 326600)
central_df = df[df["location_id"] == 326600]
median_price_central = central_df["price"].median()
central_text = f"1. Christchurch Central Median Airbnb Price (ID: 326600): ${median_price_central:.2f}"
print(f"\n--- {central_text} ---")
summary_report.append(f"\n{central_text}")

# Calculate price gap (Short-term daily vs Long-term daily equivalent)
df['long_term_daily_rent'] = df['Median Rent'] / 7
df['price_gap_per_night'] = df['price'] - df['long_term_daily_rent']

# Top Locations with Largest Gap between Short and Long Term Rental Prices
print("\n--- 2. Top Locations by Largest Median Price Gap ---")
top_locations_gap = (
    df.groupby("location_name")["price_gap_per_night"]
    .agg(median_gap="median", listing_count="count")
    .sort_values(by="median_gap", ascending=False)
    .head(10)
    .reset_index()
)
print(top_locations_gap)
top_locations_gap.to_csv(ANALYSIS_DIR / 'top_10_price_gap_locations.csv', index=False)

summary_report.append("\n2. Top Locations by Largest Median Price Gap:")
summary_report.append(top_locations_gap.to_string(index=False))

# Price Gap Aggregated by Region/Location (or Ward if column exists)
group_col = "WARD2023_name" if "WARD2023_name" in df.columns else "location_name"
print(f"\n--- 3. Price Gap Aggregated by {group_col} ---")

agg_summary = (
    df.groupby(group_col)["price_gap_per_night"]
    .agg(
        median_gap="median",
        mean_gap="mean",
        max_gap="max",
        listing_count="count"
    )
    .sort_values(by="median_gap", ascending=False)
)
print(agg_summary.head(15))

ward_summary_path = ANALYSIS_DIR / 'ward_price_gap_summary.csv'
agg_summary.to_csv(ward_summary_path)
print(f"Ward price gap summary saved to: {ward_summary_path}")

summary_report.append(f"\n3. Price Gap Aggregated by {group_col}:")
summary_report.append(agg_summary.to_string())

# save
full_summary_path = SUMMARIES_DIR / 'short_v_long_term_rentals_analysis.txt'
with open(full_summary_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(summary_report))

print(f"\nFull analysis summary successfully saved to: {full_summary_path}")
print("\n--- Analysis Script Complete ---")