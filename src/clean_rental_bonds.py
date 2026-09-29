import pandas as pd

# File configuration
INPUT_FILE = "output/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"  # Change to your filename
OUTPUT_FILE = "output/processed/rental_bonds_clean.csv"

# 1. Load the original dataset
df = pd.read_csv(
    INPUT_FILE,
    dtype={"Location Id": "string"},
    low_memory=False
)

print("Original dataset shape:", df.shape)
print("\nOriginal missing values:")
print(df.isna().sum())

# 2. Standardise the location codes
df["Location Id"] = (
    df["Location Id"]
    .astype("string")
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

df["Location Id"] = df["Location Id"].replace(
    {"": pd.NA, "nan": pd.NA, "None": pd.NA}
)

# 3. Convert TimeFrame to datetime
df["TimeFrame"] = pd.to_datetime(
    df["TimeFrame"],
    errors="coerce"
)

# 4. Keep the relevant quarters
required_quarters = pd.to_datetime([
    "2025-10-01",
    "2026-01-01",
    "2026-04-01"
])

df = df[
    df["TimeFrame"].isin(required_quarters)
].copy()

print("\nRows after filtering by time:", len(df))

# 5. Keep area-level aggregate records
df["Dwelling Type"] = (
    df["Dwelling Type"].astype("string").str.strip()
)

df["Number Of Beds"] = (
    df["Number Of Beds"].astype("string").str.strip()
)

df = df[
    df["Dwelling Type"].eq("ALL")
    & df["Number Of Beds"].eq("ALL")
].copy()

print("Rows after aggregate filtering:", len(df))

# 6. Remove records without a location code
df = df.dropna(subset=["Location Id"])

# 7. Convert rental statistics to numeric
numeric_columns = [
    "Total Bonds",
    "Active Bonds",
    "Closed Bonds",
    "Median Rent",
    "Geometric Mean Rent",
    "Upper Quartile Rent",
    "Lower Quartile Rent",
    "Log Std Dev Weekly Rent"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

# 8. Create a quarter column for joining
df["quarter"] = (
    df["TimeFrame"]
    .dt.to_period("Q")
    .dt.start_time
)

# 9. Check duplicate area-quarter combinations
duplicates = df.duplicated(
    subset=["Location Id", "quarter"],
    keep=False
)

print("\nDuplicate area-quarter rows:")
print(duplicates.sum())

if duplicates.any():
    print(
        df.loc[
            duplicates,
            ["Location Id", "quarter"]
        ].sort_values(
            ["Location Id", "quarter"]
        ).head(20)
    )

    raise ValueError(
        "Duplicate area-quarter records found. "
        "Investigate before joining."
    )

# 10. Calculate nightly rental equivalent
df["Median Nightly Rent"] = df["Median Rent"] / 7

# 11. Final validation
print("\nFinal dataset shape:", df.shape)

print("\nRows per quarter:")
print(df["quarter"].value_counts().sort_index())

print("\nMissing values:")
print(df.isna().sum())

print("\nUnique locations:")
print(df["Location Id"].nunique())

# 12. Save the cleaned dataset
df.to_csv(OUTPUT_FILE, index=False)

print("\nCleaned dataset saved:", OUTPUT_FILE)