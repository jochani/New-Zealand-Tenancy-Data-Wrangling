"""
DATA422 - Deliverable 4
Christchurch Airbnb Data Cleaning

Input:
    data/raw/christchurch_oct2025_jun2026.csv

Output:
    data/processed/christchurch_airbnb_clean.csv.gz

Cleaning principles:
- Preserve latitude and longitude as required by Deliverable 4.
- Preserve rows with missing prices because other fields remain useful.
- Do not impute missing prices in the primary cleaned dataset.
- Do not automatically remove price outliers.
- Remove columns that provide no useful information for the planned
  rental-price/property-availability comparison.
- Validate the input dataset so all team members produce the same output.
"""

from pathlib import Path
import pandas as pd


# ============================================================
# 1. FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

## df = pd.read_csv("output/christchurch_oct2025_jun2026.csv")

INPUT_FILE = "output/christchurch_oct2025_jun2026.csv"

OUTPUT_DIR = "output/processed"

OUTPUT_FILE = "output/processed/christchurch_airbnb_clean.csv.gz"

## OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. EXPECTED INPUT
# ============================================================

EXPECTED_ROWS = 28795
EXPECTED_COLUMNS = 19

EXPECTED_MONTHS = {
    "10_2025",
    "11_2025",
    "12_2025",
    "01_2026",
    "02_2026",
    "03_2026",
    "04_2026",
    "05_2026",
    "06_2026",
}


# ============================================================
# 3. LOAD DATA
# ============================================================

print("=" * 70)
print("DATA422 - DELIVERABLE 4")
print("CHRISTCHURCH AIRBNB CLEANING")
print("=" * 70)

print(f"\nReading:\n{INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)

original_rows = len(df)
original_columns = len(df.columns)

print("\nOriginal dataset:")
print(f"Rows:    {original_rows:,}")
print(f"Columns: {original_columns}")


# ============================================================
# 4. VALIDATE STARTING DATASET
# ============================================================

print("\n" + "=" * 70)
print("INPUT VALIDATION")
print("=" * 70)

if original_rows != EXPECTED_ROWS:
    raise ValueError(
        f"Expected {EXPECTED_ROWS:,} rows, "
        f"but found {original_rows:,}. "
        "Check the Deliverable 3 dataset."
    )

if original_columns != EXPECTED_COLUMNS:
    raise ValueError(
        f"Expected {EXPECTED_COLUMNS} columns, "
        f"but found {original_columns}."
    )

required_columns = {
    "id",
    "name",
    "host_id",
    "host_name",
    "neighbourhood_group",
    "neighbourhood",
    "latitude",
    "longitude",
    "room_type",
    "price",
    "minimum_nights",
    "number_of_reviews",
    "last_review",
    "reviews_per_month",
    "calculated_host_listings_count",
    "availability_365",
    "number_of_reviews_ltm",
    "license",
    "month_year",
}

missing_required_columns = (
    required_columns - set(df.columns)
)

if missing_required_columns:
    raise ValueError(
        "Required columns missing: "
        f"{sorted(missing_required_columns)}"
    )

actual_months = set(
    df["month_year"]
    .dropna()
    .astype(str)
    .unique()
)

if actual_months != EXPECTED_MONTHS:
    raise ValueError(
        "Unexpected month coverage.\n"
        f"Expected: {sorted(EXPECTED_MONTHS)}\n"
        f"Found:    {sorted(actual_months)}"
    )

print("Dataset dimensions: PASS")
print("Required columns:   PASS")
print("Month coverage:     PASS")


# ============================================================
# 5. INITIAL DATA-QUALITY REPORT
# ============================================================

print("\n" + "=" * 70)
print("INITIAL DATA QUALITY")
print("=" * 70)

print("\nMissing values:")
print(df.isna().sum())

exact_duplicates = df.duplicated().sum()

listing_month_duplicates = df.duplicated(
    subset=["id", "month_year"]
).sum()

print(
    f"\nExact duplicate rows: "
    f"{exact_duplicates:,}"
)

print(
    f"Duplicate ID + month records: "
    f"{listing_month_duplicates:,}"
)


# ============================================================
# 6. REMOVE DUPLICATES IF PRESENT
# ============================================================

before_duplicates = len(df)

df = df.drop_duplicates()

df = df.drop_duplicates(
    subset=["id", "month_year"],
    keep="first"
)

duplicates_removed = (
    before_duplicates - len(df)
)

print(
    f"\nDuplicate records removed: "
    f"{duplicates_removed:,}"
)


# ============================================================
# 7. REMOVE AGREED UNNECESSARY COLUMNS
# ============================================================

"""
Cleaning decisions:

neighbourhood_group:
    Dataset is already restricted to Christchurch and the column
    provides no additional useful variation after filtering.

last_review:
    Review timing is outside the planned rental-price and property-
    availability comparison.

reviews_per_month:
    Review activity is outside the planned analysis.

license:
    Contains 100% missing values.
"""

columns_to_drop = [
    "neighbourhood_group",
    "last_review",
    "reviews_per_month",
    "license",
]

existing_drop_columns = [
    column
    for column in columns_to_drop
    if column in df.columns
]

df = df.drop(
    columns=existing_drop_columns
)

print("\nColumns removed:")

for column in existing_drop_columns:
    print(f"  - {column}")


# ============================================================
# 8. PRESERVE IMPORTANT GEOGRAPHIC VARIABLES
# ============================================================

geographic_columns = [
    "neighbourhood",
    "latitude",
    "longitude",
]

for column in geographic_columns:
    if column not in df.columns:
        raise ValueError(
            f"Required geographic column missing: "
            f"{column}"
        )

coordinate_missing = (
    df[["latitude", "longitude"]]
    .isna()
    .any(axis=1)
    .sum()
)

print(
    "\nRows with missing latitude/longitude: "
    f"{coordinate_missing:,}"
)

# Do not silently remove them.
# Our validated source currently contains none.


# ============================================================
# 9. PRICE MISSINGNESS
# ============================================================

price_missing = df["price"].isna().sum()

price_missing_pct = (
    df["price"].isna().mean() * 100
)

print("\n" + "=" * 70)
print("PRICE MISSINGNESS")
print("=" * 70)

print(
    f"Missing prices: "
    f"{price_missing:,}"
)

print(
    f"Missing price percentage: "
    f"{price_missing_pct:.2f}%"
)

price_missing_by_month = (
    df.groupby("month_year")["price"]
    .agg(
        total="size",
        observed="count",
        missing=lambda x: x.isna().sum()
    )
)

price_missing_by_month[
    "missing_pct"
] = (
    price_missing_by_month["missing"]
    / price_missing_by_month["total"]
    * 100
).round(2)

print("\nMissing prices by month:")
print(price_missing_by_month)


# ============================================================
# 10. MISSING PRICE DECISION
# ============================================================

"""
IMPORTANT:

Missing price rows are RETAINED.

Reason:
- 10,667 observations (37.04%) have missing prices.
- 9,427 of those occur in Dec 2025-Feb 2026, when price is
  completely unavailable.
- Rows still contain useful geographic and availability data.
- KNN validation performed during exploratory analysis produced
  substantially higher MAE than same-listing temporal estimates.
- True Dec-Feb prices do not exist in the source dataset, so
  imputed values cannot be directly validated.

Therefore:
    price remains NaN in the primary cleaned dataset.
"""

df["price_was_missing"] = (
    df["price"].isna()
)

# ============================================================
# 11. HANDLE MISSING HOST NAME
# ============================================================

"""
host_name:
    One host_name value is missing.

Decision:
    Where possible, recover the host name using another observation
    with the same host_id.

Reason:
    host_id uniquely identifies the host, and the same host may appear
    across multiple monthly snapshots. Recovering an existing host
    name is preferable to deleting the row or inventing a value.

    If no known host_name exists for that host_id, leave the value
    missing.
"""

missing_host_before = df["host_name"].isna().sum()

print("\n" + "=" * 70)
print("HOST NAME MISSINGNESS")
print("=" * 70)

print(
    f"Missing host_name before cleaning: "
    f"{missing_host_before:,}"
)

# Build host_id -> known host_name mapping
host_name_lookup = (
    df[df["host_name"].notna()]
    .drop_duplicates(subset=["host_id"])
    .set_index("host_id")["host_name"]
)

# Fill only missing host names using an existing value
df["host_name"] = df["host_name"].fillna(
    df["host_id"].map(host_name_lookup)
)

missing_host_after = df["host_name"].isna().sum()

host_names_recovered = (
    missing_host_before - missing_host_after
)

print(
    f"Host names recovered from same host_id: "
    f"{host_names_recovered:,}"
)

print(
    f"Missing host_name after cleaning: "
    f"{missing_host_after:,}"
)


# ============================================================
# 12. HANDLE MISSING MINIMUM NIGHTS
# ============================================================

"""
minimum_nights:
    37 observations contain missing minimum_nights.

Decision:
    First attempt to recover the value from another monthly
    observation of the EXACT SAME listing.

    The median minimum_nights for that listing is used because a
    listing may change its minimum-stay requirement between snapshots.

    If the listing has no known minimum_nights value elsewhere,
    leave the value missing rather than applying a dataset-wide
    imputation.

Reason:
    Same-listing information is more defensible than replacing values
    using the overall Christchurch median or an unrelated listing.
"""

missing_min_before = (
    df["minimum_nights"].isna().sum()
)

print("\n" + "=" * 70)
print("MINIMUM NIGHTS MISSINGNESS")
print("=" * 70)

print(
    f"Missing minimum_nights before cleaning: "
    f"{missing_min_before:,}"
)

# Calculate median known minimum_nights for each exact listing
listing_minimum_nights = (
    df[df["minimum_nights"].notna()]
    .groupby("id")["minimum_nights"]
    .median()
)

# Only fill currently missing values
missing_min_mask = (
    df["minimum_nights"].isna()
)

df.loc[
    missing_min_mask,
    "minimum_nights"
] = (
    df.loc[
        missing_min_mask,
        "id"
    ].map(listing_minimum_nights)
)

missing_min_after = (
    df["minimum_nights"].isna().sum()
)

minimum_nights_recovered = (
    missing_min_before - missing_min_after
)

print(
    f"minimum_nights recovered from same listing: "
    f"{minimum_nights_recovered:,}"
)

print(
    f"Missing minimum_nights after cleaning: "
    f"{missing_min_after:,}"
)

# ============================================================
# 13. PRICE OUTLIER DIAGNOSTIC
# ============================================================

"""
Observed prices are not automatically deleted.

Instead, extreme within-listing price movements are flagged for
future investigation.

Diagnostic rule:
    price >= 5 times listing median
OR
    price <= 20% of listing median

This is a diagnostic flag, NOT an automatic deletion rule.
"""

observed_prices = df[
    df["price"].notna()
].copy()

listing_medians = (
    observed_prices
    .groupby("id")["price"]
    .median()
)

df["listing_price_median"] = (
    df["id"].map(listing_medians)
)

df["price_ratio_to_listing_median"] = (
    df["price"]
    / df["listing_price_median"]
)

df["potential_price_outlier"] = (
    (
        df["price_ratio_to_listing_median"]
        >= 5
    )
    |
    (
        df["price_ratio_to_listing_median"]
        <= 0.20
    )
)

# Missing prices should not be classified as outliers.

df.loc[
    df["price"].isna(),
    "potential_price_outlier"
] = False

outlier_count = (
    df["potential_price_outlier"]
    .sum()
)

print("\n" + "=" * 70)
print("PRICE OUTLIER DIAGNOSTIC")
print("=" * 70)

print(
    f"Potential price outliers flagged: "
    f"{outlier_count:,}"
)


# ============================================================
# 14. FINAL COLUMN ORDER
# ============================================================

final_columns = [
    "id",
    "name",
    "host_id",
    "host_name",

    "neighbourhood",
    "latitude",
    "longitude",

    "room_type",
    "price",
    "price_was_missing",

    "minimum_nights",
    "number_of_reviews",

    "calculated_host_listings_count",
    "availability_365",
    "number_of_reviews_ltm",

    "month_year",

    # Diagnostic fields
    "listing_price_median",
    "price_ratio_to_listing_median",
    "potential_price_outlier",
]

df = df[final_columns]


# ============================================================
# 15. FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

print(f"Final rows:    {len(df):,}")
print(f"Final columns: {len(df.columns)}")

print(
    "Missing latitude:",
    df["latitude"].isna().sum()
)

print(
    "Missing longitude:",
    df["longitude"].isna().sum()
)

print(
    "Missing prices retained:",
    df["price"].isna().sum()
)

print(
    "Exact duplicates remaining:",
    df.duplicated().sum()
)

print(
    "ID + month duplicates remaining:",
    df.duplicated(
        subset=["id", "month_year"]
    ).sum()
)


# ============================================================
# 16. SAVE COMPRESSED CLEAN DATASET
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    compression="gzip"
)

print("\n" + "=" * 70)
print("OUTPUT")
print("=" * 70)

print(
    f"Clean dataset saved to:\n"
    f"{OUTPUT_FILE}"
)


# ============================================================
# 17. RELOAD OUTPUT TO VERIFY REPRODUCIBILITY
# ============================================================

check = pd.read_csv(
    OUTPUT_FILE,
    compression="gzip"
)

if check.shape != df.shape:
    raise ValueError(
        "Saved dataset shape does not "
        "match cleaned dataset."
    )

print(
    "\nSaved-file verification: PASS"
)

print(
    f"Verified shape: "
    f"{check.shape[0]:,} rows x "
    f"{check.shape[1]} columns"
)

print("\nCleaning completed successfully.")