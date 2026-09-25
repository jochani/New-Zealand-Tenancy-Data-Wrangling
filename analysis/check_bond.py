import pandas as pd

INPUT_FILE = "output/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
df = pd.read_csv(INPUT_FILE)

print("Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isna().sum())

print("\nDwelling Types:")
print(df["Dwelling Type"].value_counts(dropna=False))

print("\nNumber of Beds:")
print(df["Number Of Beds"].value_counts(dropna=False))

print("\nTimeFrames:")
print(
    sorted(df["TimeFrame"].unique())
)

TARGET_QUARTERS = [
    "2025-10-01",
    "2026-01-01",
    "2026-04-01",
]

target = df[
    df["TimeFrame"].isin(TARGET_QUARTERS)
].copy()

print("\nTarget period:")
print(target.shape)

print("\nRows by quarter:")
print(
    target.groupby("TimeFrame").size()
)

print(
    "\nUnique Location IDs:",
    target["Location Id"].nunique()
)

print(
    "\nExact duplicates:",
    target.duplicated().sum()
)
# ============================================================
# LOCATION ID INVESTIGATION
# ============================================================

print("\n" + "=" * 70)
print("LOCATION ID INVESTIGATION")
print("=" * 70)

print("\nLocation Id missing:")
print(target["Location Id"].isna().sum())

print("\nUnique Location IDs:")
print(target["Location Id"].nunique())

print("\nSmallest Location IDs:")
print(
    target["Location Id"]
    .dropna()
    .drop_duplicates()
    .sort_values()
    .head(30)
    .to_string(index=False)
)

print("\nLargest Location IDs:")
print(
    target["Location Id"]
    .dropna()
    .drop_duplicates()
    .sort_values()
    .tail(30)
    .to_string(index=False)
)

print("\nRows where Location Id is missing:")

print(
    target[
        target["Location Id"].isna()
    ].head(30).to_string(index=False)
)

## investigate -99 separately:

# ============================================================
# investigate -99 separately:
# ============================================================

print("\n" + "=" * 70)
print("LOCATION ID = -99")
print("=" * 70)

minus_99 = target[
    target["Location Id"] == -99
]

print("Rows:", len(minus_99))

print(
    minus_99.head(30)
    .to_string(index=False)
)


## investigate the missing bedroom values

# ============================================================
# investigate the missing bedroom values
# ============================================================


print("\n" + "=" * 70)
print("MISSING NUMBER OF BEDS")
print("=" * 70)

missing_beds = target[
    target["Number Of Beds"].isna()
]

print(
    "Missing Number Of Beds:",
    len(missing_beds)
)

print("\nBy Dwelling Type:")

print(
    missing_beds["Dwelling Type"]
    .value_counts(dropna=False)
)

print("\nSample:")

print(
    missing_beds.head(30)
    .to_string(index=False)
)

## investigate missing rent values

# ============================================================
# investigate missing rent values
# ============================================================

print("\n" + "=" * 70)
print("MISSING MEDIAN RENT")
print("=" * 70)

missing_rent = target[
    target["Median Rent"].isna()
]

print(
    "Missing Median Rent:",
    len(missing_rent)
)

print("\nBy Dwelling Type:")

print(
    missing_rent["Dwelling Type"]
    .value_counts(dropna=False)
)

print("\nBy Number Of Beds:")

print(
    missing_rent["Number Of Beds"]
    .value_counts(dropna=False)
)

print("\nSample:")

print(
    missing_rent.head(30)
    .to_string(index=False)
)

# ============================================================
# VERIFY MISSING LOCATION / RENT RELATIONSHIP
# ============================================================

print("\n" + "=" * 70)
print("MISSING LOCATION VS MISSING RENT")
print("=" * 70)

missing_location = target["Location Id"].isna()
missing_rent = target["Median Rent"].isna()

print(
    "Missing Location Id:",
    missing_location.sum()
)

print(
    "Missing Median Rent:",
    missing_rent.sum()
)

print(
    "Both Location Id and Median Rent missing:",
    (missing_location & missing_rent).sum()
)

print(
    "Location missing but rent present:",
    (missing_location & ~missing_rent).sum()
)

print(
    "Location present but rent missing:",
    (~missing_location & missing_rent).sum()
)