
import sqlite3
from pathlib import Path

import pandas as pd

AIRBNB_FILE = Path("output/processed/christchurch_airbnb_clean_with_sa2.xlsx")
BONDS_FILE = Path("output/processed/rental_bonds_clean.csv")

OUTPUT_DIR = Path("output/sqlite")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = OUTPUT_DIR / "christchurch_rentals.db"

# -------------------------------------------------
# 1. Prepare Airbnb data
# -------------------------------------------------

airbnb = pd.read_excel(
    AIRBNB_FILE,
    dtype={"id": "string", "location_id": "string"}
)

airbnb["location_id"] = (
    airbnb["location_id"]
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

airbnb["price"] = pd.to_numeric(
    airbnb["price"], errors="coerce"
)

# month_year format: 04_2026
airbnb["month_date"] = pd.to_datetime(
    airbnb["month_year"],
    format="%m_%Y",
    errors="coerce"
)

airbnb["quarter"] = (
    airbnb["month_date"]
    .dt.to_period("Q")
    .dt.start_time
    .dt.strftime("%Y-%m-%d")
)

# -------------------------------------------------
# 2. Prepare rental-bond data
# -------------------------------------------------

bonds = pd.read_csv(
    BONDS_FILE,
    dtype={"Location Id": "string"}
)

bonds["Location Id"] = (
    bonds["Location Id"]
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

bonds["TimeFrame"] = pd.to_datetime(
    bonds["TimeFrame"], errors="coerce"
)

bonds["quarter"] = (
    bonds["TimeFrame"]
    .dt.to_period("Q")
    .dt.start_time
    .dt.strftime("%Y-%m-%d")
)

# Keep only overall statistics, not individual
# dwelling-type or bedroom breakdowns.
if "Dwelling Type" in bonds.columns:
    bonds = bonds[
        bonds["Dwelling Type"].astype(str).str.upper() == "ALL"
    ]

if "Number Of Beds" in bonds.columns:
    bonds = bonds[
        bonds["Number Of Beds"].astype(str).str.upper() == "ALL"
    ]

bonds = bonds.rename(
    columns={
        "Location Id": "location_id",
        "Median Rent": "median_weekly_rent",
        "Active Bonds": "active_bonds",
        "Total Bonds": "total_bonds"
    }
)

for col in [
    "median_weekly_rent",
    "active_bonds",
    "total_bonds"
]:
    if col in bonds.columns:
        bonds[col] = pd.to_numeric(
            bonds[col], errors="coerce"
        )

bonds = bonds.dropna(
    subset=["location_id", "quarter"]
)

# Each area must have at most one aggregate
# bond record per quarter.
duplicates = bonds.duplicated(
    subset=["location_id", "quarter"],
    keep=False
)

if duplicates.any():
    print(
        bonds.loc[
            duplicates,
            ["location_id", "quarter"]
        ].head(20)
    )
    raise ValueError(
        "Duplicate bond area-quarter records found. "
        "Check the aggregate filters."
    )

# -------------------------------------------------
# 3. Create SQLite database and import tables
# -------------------------------------------------

with sqlite3.connect(DB_FILE) as conn:

    airbnb.to_sql(
        "airbnb",
        conn,
        if_exists="replace",
        index=False
    )

    bonds.to_sql(
        "rental_bonds",
        conn,
        if_exists="replace",
        index=False
    )

    conn.execute("""
        CREATE INDEX idx_airbnb_location_quarter
        ON airbnb(location_id, quarter)
    """)

    conn.execute("""
        CREATE INDEX idx_bonds_location_quarter
        ON rental_bonds(location_id, quarter)
    """)

    # ---------------------------------------------
    # 4. SQL LEFT JOIN
    # ---------------------------------------------

    join_query = """
        SELECT
            a.*,
            b.median_weekly_rent
                AS bond_median_weekly_rent,
            b.active_bonds
                AS bond_active_bonds,
            b.total_bonds
                AS bond_total_bonds,

            b.median_weekly_rent / 7.0
                AS bond_nightly_rent,

            a.price - b.median_weekly_rent / 7.0
                AS nightly_price_gap,

            CASE
                WHEN b.location_id IS NOT NULL
                THEN 'both'
                ELSE 'left_only'
            END AS merge_status

        FROM airbnb AS a

        LEFT JOIN rental_bonds AS b
            ON a.location_id = b.location_id
           AND a.quarter = b.quarter
    """

    joined = pd.read_sql_query(
        join_query, conn
    )

    # ---------------------------------------------
    # 5. Verify the join
    # ---------------------------------------------

    original_count = conn.execute(
        "SELECT COUNT(*) FROM airbnb"
    ).fetchone()[0]

    joined_count = len(joined)

    print("Original Airbnb rows:", original_count)
    print("Joined rows:", joined_count)

    if original_count != joined_count:
        raise ValueError(
            "Joined row count differs from Airbnb. "
            "Check for duplicate bond records."
        )

    print("\nJOIN RESULTS")
    print(joined["merge_status"].value_counts())

    # ---------------------------------------------
    # 6. SQL: largest median nightly gaps
    # ---------------------------------------------

    # SQLite does not have a built-in median()
    # aggregate. Retrieve the SQL-calculated gaps,
    # then calculate area medians with pandas.
    gaps = pd.read_sql_query("""
        SELECT
            location_id,
            location_name,
            id,
            nightly_price_gap
        FROM (
            SELECT
                a.location_id,
                a.location_name,
                a.id,
                a.price - b.median_weekly_rent / 7.0
                    AS nightly_price_gap
            FROM airbnb AS a
            INNER JOIN rental_bonds AS b
                ON a.location_id = b.location_id
               AND a.quarter = b.quarter
            WHERE a.price > 0
              AND b.median_weekly_rent > 0
        )
    """, conn)

    gap_summary = (
        gaps.groupby(
            ["location_id", "location_name"],
            dropna=False
        )
        .agg(
            unique_listings=("id", "nunique"),
            median_nightly_gap=(
                "nightly_price_gap", "median"
            )
        )
        .reset_index()
    )

    gap_summary = gap_summary[
        gap_summary["unique_listings"] >= 10
    ].sort_values(
        "median_nightly_gap",
        ascending=False
    )

    print("\nTOP 10 MEDIAN PRICE GAPS")
    print(gap_summary.head(10).to_string(index=False))

# -------------------------------------------------
# 7. Export results
# -------------------------------------------------

joined.to_csv(
    OUTPUT_DIR / "sql_joined_airbnb_bonds.csv",
    index=False
)

gap_summary.to_csv(
    OUTPUT_DIR / "sql_area_price_gaps.csv",
    index=False
)

print("\nSQLite database:", DB_FILE)
print("SQL join completed successfully.")