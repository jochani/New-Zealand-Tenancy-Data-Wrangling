
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

INPUT_FILE = "output/processed/christchurch_airbnb_bonds_joined.csv"
OUTPUT_DIR = Path("output/analysis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load joined Airbnb and rental-bond data
df = pd.read_csv(
    INPUT_FILE,
    dtype={"location_id": "string", "id": "string"},
    low_memory=False
)

# Select April–June 2026
quarter_months = ["04_2026", "05_2026", "06_2026"]
df = df[df["month_year"].isin(quarter_months)].copy()

# Standardise geographic identifiers
df["location_id"] = (
    df["location_id"].str.replace(r"\.0$", "", regex=True)
)

# Convert active bond counts to numeric
df["bond_active_bonds"] = pd.to_numeric(
    df["bond_active_bonds"], errors="coerce"
)

# Count unique Airbnb listings in each area
# Do not drop rows simply because Airbnb price is missing.
airbnb_counts = (
    df.dropna(subset=["location_id"])
    .groupby("location_id")
    .agg(
        location_name=("location_name", "first"),
        airbnb_listings=("id", "nunique")
    )
    .reset_index()
)

# Bond values repeat on each joined Airbnb row.
# Take one value per area, rather than summing repeated rows.
bond_counts = (
    df.dropna(subset=["location_id", "bond_active_bonds"])
    .groupby("location_id")["bond_active_bonds"]
    .agg(["min", "max"])
    .reset_index()
)

# Check whether each area has consistent bond statistics
inconsistent = bond_counts[
    bond_counts["min"] != bond_counts["max"]
]

if not inconsistent.empty:
    raise ValueError(
        "Some areas have conflicting active-bond counts. "
        "Check the quarter matching and source data:\n"
        + inconsistent.to_string(index=False)
    )

bond_counts = bond_counts.rename(
    columns={"max": "active_rental_bonds"}
)[["location_id", "active_rental_bonds"]]

# Merge counts for the same SA2 area
comparison = airbnb_counts.merge(
    bond_counts,
    on="location_id",
    how="left",
    validate="one_to_one"
)

# Additional comparison measures
comparison["airbnb_per_100_bonds"] = (
    comparison["airbnb_listings"]
    / comparison["active_rental_bonds"]
    * 100
)

comparison["count_difference"] = (
    comparison["active_rental_bonds"]
    - comparison["airbnb_listings"]
)

# Areas without matching bond statistics remain missing,
# rather than being incorrectly treated as zero.
comparison = comparison.sort_values(
    "airbnb_listings",
    ascending=False
)

comparison.to_csv(
    OUTPUT_DIR / "airbnb_vs_rental_counts.csv",
    index=False
)

print("\nAIRBNB VS ACTIVE RENTAL BONDS")
print(
    comparison[
        [
            "location_name",
            "airbnb_listings",
            "active_rental_bonds",
            "airbnb_per_100_bonds"
        ]
    ].head(20).to_string(index=False)
)

print("\nAreas with no matching bond statistics:")
print(
    comparison.loc[
        comparison["active_rental_bonds"].isna(),
        ["location_id", "location_name", "airbnb_listings"]
    ].to_string(index=False)
)

# Plot areas with the most Airbnb listings and valid bond data
top10 = (
    comparison.dropna(subset=["active_rental_bonds"])
    .head(10)
    .sort_values("airbnb_listings")
)

if not top10.empty:
    ax = top10.plot.barh(
        x="location_name",
        y=["airbnb_listings", "active_rental_bonds"],
        figsize=(12, 7)
    )

    ax.set_title(
        "Airbnb listings vs active rental bonds "
        "(April–June 2026)"
    )
    ax.set_xlabel("Count")
    ax.set_ylabel("SA2 area")
    ax.legend(["Unique Airbnb listings", "Active rental bonds"])

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "airbnb_vs_rental_counts.png",
        dpi=200
    )
    plt.close()

print("\nFiles saved in:", OUTPUT_DIR)