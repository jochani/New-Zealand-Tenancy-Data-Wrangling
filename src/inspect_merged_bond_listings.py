import os
import pathlib
import pandas as pd

# 1. Ensure output summaries directory exists
SUMMARIES_DIR = pathlib.Path('output/summaries')
SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

# 2. Load the merged dataset
MERGED_FILE = pathlib.Path('output/processed/spatial_bond_listings_merged.csv')
df = pd.read_csv(MERGED_FILE)

# 3. Generate summary statistics and inspections
summary_lines = []
summary_lines.append("=== DATASET INSPECTION SUMMARY ===")
summary_lines.append(f"Total Rows: {len(df):,}")
summary_lines.append(f"Total Columns: {len(df.columns)}")
summary_lines.append("\n--- Column Names & Types ---")
for col, dtype in df.dtypes.items():
    summary_lines.append(f"{col}: {dtype}")

summary_lines.append("\n--- Missing Values Count ---")
missing = df.isnull().sum()
for col, val in missing[missing > 0].items():
    summary_lines.append(f"{col}: {val:,}")

summary_lines.append("\n--- Numerical Summary Statistics ---")
summary_lines.append(str(df.describe()))

# 4. Save inspection report to output/summaries/
summary_path = SUMMARIES_DIR / 'merged_bonds_listings_summary.txt'
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(summary_lines))

print(f"Inspection summary successfully saved to: {summary_path}")