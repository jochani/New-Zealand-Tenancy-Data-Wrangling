
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. File configuration
# --------------------------------------------------

AIRBNB_FILE = "output/processed/christchurch_airbnb_clean_with_sa2.xlsx"
BOND_FILE = "output/processed/rental_bonds_clean.csv"  # Change this

OUTPUT_FILE = "output/processed/christchurch_airbnb_bonds_joined.csv"
UNMATCHED_FILE = "output/processed/airbnb_unmatched_bonds.csv"

# --------------------------------------------------
# 2. Load datasets
# --------------------------------------------------

airbnb = pd.read_excel(
    AIRBNB_FILE,
    dtype={"location_id": "string"}
)

bond_path = Path(BOND_FILE)

if bond_path.suffix.lower() == ".csv":
    bonds = pd.read_csv(
        bond_path,
        dtype={"Location Id": "string"}
    )
else:
    bonds = pd.read_excel(
        bond_path,
        dtype={"Location Id": "string"}
    )

print("Airbnb rows:", len(airbnb))
print("Bond rows:", len(bonds))

# --------------------------------------------------
# 3. Standardise area codes
# --------------------------------------------------

airbnb["location_id"] = (
    airbnb["location_id"]
    .astype("string")
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

bonds["Location Id"] = (
    bonds["Location Id"]
    .astype("string")
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

# --------------------------------------------------
# 4. Convert Airbnb months to quarters
# --------------------------------------------------

# Example: 10_2025 -> 2025-10-01

airbnb["month_date"] = pd.to_datetime(
    airbnb["month_year"].astype(str),
    format="%m_%Y",
    errors="raise"
)

airbnb["quarter"] = (
    airbnb["month_date"]
    .dt.to_period("Q")
    .dt.start_time
)

# --------------------------------------------------
# 5. Prepare rental-bond data
# --------------------------------------------------

bonds["quarter"] = pd.to_datetime(
    bonds["TimeFrame"],
    errors="raise"
).dt.to_period("Q").dt.start_time

# Use the aggregate rows rather than mixing
# individual dwelling types and bedroom categories.

bonds = bonds[
    bonds["Dwelling Type"].astype(str).str.strip().eq("ALL")
    &
    bonds["Number Of Beds"].astype(str).str.strip().eq("ALL")
].copy()

# Retain the required project period.

bonds = bonds[
    bonds["quarter"].isin(
        pd.to_datetime([
            "2025-10-01",
            "2026-01-01",
            "2026-04-01"
        ])
    )
]

# --------------------------------------------------
# 6. Validate bond join keys
# --------------------------------------------------

keys = ["Location Id", "quarter"]

duplicates = bonds.duplicated(
    subset=keys,
    keep=False
)

if duplicates.any():
    print(
        bonds.loc[duplicates, keys]
        .sort_values(keys)
        .head(20)
    )

    raise ValueError(
        "Multiple bond rows exist for an "
        "area and quarter. Inspect before joining."
    )

print("Prepared bond rows:", len(bonds))

# --------------------------------------------------
# 7. Select and rename bond columns
# --------------------------------------------------

bond_columns = [
    "Location Id",
    "quarter",
    "Median Rent",
    "Active Bonds",
    "Total Bonds",
    "Closed Bonds"
]

bond_lookup = bonds[bond_columns].rename(
    columns={
        "Location Id": "location_id",
        "Median Rent": "bond_median_weekly_rent",
        "Active Bonds": "bond_active_bonds",
        "Total Bonds": "bond_total_bonds",
        "Closed Bonds": "bond_closed_bonds"
    }
)

# --------------------------------------------------
# 8. Left join on area code AND quarter
# --------------------------------------------------

joined = airbnb.merge(
    bond_lookup,
    on=["location_id", "quarter"],
    how="left",
    validate="many_to_one",
    indicator=True
)

# --------------------------------------------------
# 9. Calculate comparable nightly prices
# --------------------------------------------------

joined["price"] = pd.to_numeric(
    joined["price"],
    errors="coerce"
)

joined["bond_median_weekly_rent"] = pd.to_numeric(
    joined["bond_median_weekly_rent"],
    errors="coerce"
)

joined["bond_nightly_rent"] = (
    joined["bond_median_weekly_rent"] / 7
)

joined["nightly_price_gap"] = (
    joined["price"] - joined["bond_nightly_rent"]
)

# --------------------------------------------------
# 10. Validate results
# --------------------------------------------------

print("\nJOIN VALIDATION")
print("------------------------------")

print("Original Airbnb rows:", len(airbnb))
print("Joined rows:", len(joined))

print("\nJoin results:")
print(joined["_merge"].value_counts())

assert len(joined) == len(airbnb), (
    "The join unexpectedly changed the row count."
)

# Check the known SA2 test listing.
print("\nTest listing:")
print(
    joined.loc[
        joined["id"] == 40183765,
        [
            "id",
            "location_id",
            "location_name",
            "quarter",
            "bond_median_weekly_rent"
        ]
    ].drop_duplicates().to_string(index=False)
)

# --------------------------------------------------
# 11. Save unmatched records
# --------------------------------------------------

unmatched = joined[
    joined["_merge"] == "left_only"
].copy()

unmatched.to_csv(
    UNMATCHED_FILE,
    index=False
)

# --------------------------------------------------
# 12. Save final dataset
# --------------------------------------------------

joined = joined.drop(columns=["_merge"])

joined.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved:", OUTPUT_FILE)
print("Unmatched records:", UNMATCHED_FILE)