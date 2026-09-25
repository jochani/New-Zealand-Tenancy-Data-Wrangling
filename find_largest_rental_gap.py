
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

INPUT = "output/processed/christchurch_airbnb_bonds_joined.csv"
OUTPUT = Path("output/analysis")
OUTPUT.mkdir(parents=True, exist_ok=True)

# Read the joined data
df = pd.read_csv(
    INPUT,
    dtype={"location_id": "string"}
)

# Convert prices to numeric
df["price"] = pd.to_numeric(
    df["price"], errors="coerce"
)
df["bond_median_weekly_rent"] = pd.to_numeric(
    df["bond_median_weekly_rent"], errors="coerce"
)

# Exclude observations without comparable prices
df = df.dropna(
    subset=[
        "location_id",
        "price",
        "bond_median_weekly_rent"
    ]
).copy()

df = df[
    (df["price"] > 0)
    & (df["bond_median_weekly_rent"] > 0)
]

# Calculate the difference
df["long_term_nightly"] = (
    df["bond_median_weekly_rent"] / 7
)

df["nightly_gap"] = (
    df["price"] - df["long_term_nightly"]
)

print("Valid comparisons:", len(df))

if df.empty:
    raise ValueError(
        "No valid comparisons. Check the bond join."
    )

# Find the largest individual gap
largest_individual = df.loc[
    df["nightly_gap"].idxmax()
]

print("\nLARGEST INDIVIDUAL GAP")
print(
    largest_individual[
        [
            "id",
            "location_id",
            "location_name",
            "month_year",
            "price",
            "bond_median_weekly_rent",
            "nightly_gap"
        ]
    ]
)

# Summarise the differences by SA2 area
summary = (
    df.groupby(
        ["location_id", "location_name"],
        dropna=False
    )
    .agg(
        observations=("nightly_gap", "size"),
        unique_listings=("id", "nunique"),
        median_gap=("nightly_gap", "median"),
        mean_gap=("nightly_gap", "mean"),
        max_gap=("nightly_gap", "max")
    )
    .reset_index()
)

# Minimum sample size for the main comparison
eligible = summary[
    summary["unique_listings"] >= 10
].sort_values(
    "median_gap", ascending=False
)

summary.to_csv(
    OUTPUT / "all_area_gaps.csv",
    index=False
)

eligible.to_csv(
    OUTPUT / "area_gap_summary.csv",
    index=False
)

print("\nTOP 10 AREAS BY MEDIAN GAP")
print(
    eligible.head(10).to_string(index=False)
)

# Plot the top 10 median gaps
top10 = eligible.head(10).sort_values("median_gap")

plt.figure(figsize=(11, 6))
plt.barh(
    top10["location_name"],
    top10["median_gap"]
)
plt.xlabel("Median nightly price gap (NZ$)")
plt.title(
    "Airbnb vs long-term rental: "
    "largest median gaps"
)
plt.tight_layout()
plt.savefig(
    OUTPUT / "top10_rental_gaps.png",
    dpi=200
)
plt.close()

# Plot distributions for the same areas
top_ids = eligible.head(10)["location_id"]

plot_df = df[
    df["location_id"].isin(top_ids)
]

labels = eligible.head(10)["location_name"].tolist()

values = [
    plot_df.loc[
        plot_df["location_name"] == name,
        "nightly_gap"
    ].values
    for name in labels
]

plt.figure(figsize=(12, 7))
plt.boxplot(
    values,
    tick_labels=labels,
    orientation="horizontal",
    showfliers=False
)
plt.xlabel("Nightly price gap (NZ$)")
plt.title("Distribution of nightly rental price gaps")
plt.tight_layout()
plt.savefig(
    OUTPUT / "rental_gap_distribution.png",
    dpi=200
)
plt.close()

# Find areas excluded from the main comparison
excluded = summary[
    summary["unique_listings"] < 10
].sort_values(
    "median_gap",
    ascending=False
)

print("\nAREAS WITH FEWER THAN 10 UNIQUE LISTINGS")
print(
    excluded[
        [
            "location_name",
            "unique_listings",
            "observations",
            "median_gap"
        ]
    ].head(10).to_string(index=False)
)

# Christchurch Central observations
central = df[
    df["location_id"].astype(str) == "326600"
].copy()

# Calculate statistics with the extreme price included
print("\nCHRISTCHURCH CENTRAL: BEFORE REMOVING OUTLIER")
print("Observations:", len(central))
print("Mean gap:", round(central["nightly_gap"].mean(), 2))
print("Median gap:", round(central["nightly_gap"].median(), 2))

# Remove only the identified extreme observation
central_without_outlier = central[
    ~(
        (central["id"].astype(str) == "1000994810230097024")
        & (central["month_year"] == "11_2025")
        & (central["price"] == 43654)
    )
].copy()

print("\nCHRISTCHURCH CENTRAL: AFTER REMOVING OUTLIER")
print("Observations:", len(central_without_outlier))
print(
    "Mean gap:",
    round(central_without_outlier["nightly_gap"].mean(), 2)
)
print(
    "Median gap:",
    round(central_without_outlier["nightly_gap"].median(), 2)
)

print("\nAnalysis completed.")