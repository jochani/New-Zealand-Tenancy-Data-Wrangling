"""
Create and analyse a SQLite database containing Christchurch Airbnb
and rental bond data.

DATA422 - New Zealand Tenancy Data Wrangling

Purpose
-------
Load processed Airbnb and rental bond datasets into SQLite, create
indexes for the geographic/time join keys, perform a SQL left join,
validate the result, and calculate area-level Airbnb versus rental
price-gap summaries.

Inputs
------
output/processed/christchurch_airbnb_clean_with_sa2.xlsx
output/processed/rental_bonds_clean.csv

Outputs
-------
output/sqlite/christchurch_rentals.db
output/sqlite/sql_joined_airbnb_bonds.csv
output/sqlite/sql_area_price_gaps.csv

Design principles
-----------------
- Use processed pipeline outputs rather than re-cleaning raw data.
- Preserve all upstream processed datasets.
- Use relative project paths.
- Validate input schemas before database creation.
- Separate loading, preparation, validation, database creation,
  querying, analysis, and output into focused functions.
- Validate area-quarter uniqueness before performing the SQL join.
- Use database indexes on frequently joined columns.
- Preserve all Airbnb observations using a LEFT JOIN.
- Validate that the SQL join does not unexpectedly change row count.
- Keep analytical parameters explicit.
"""

import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

AIRBNB_FILE = Path(
    "output/processed/christchurch_airbnb_clean_with_sa2.xlsx"
)

BONDS_FILE = Path(
    "output/processed/rental_bonds_clean.csv"
)

OUTPUT_DIR = Path(
    "output/sqlite"
)

DB_FILE = OUTPUT_DIR / "christchurch_rentals.db"

JOINED_OUTPUT_FILE = (
    OUTPUT_DIR / "sql_joined_airbnb_bonds.csv"
)

GAP_OUTPUT_FILE = (
    OUTPUT_DIR / "sql_area_price_gaps.csv"
)

AIRBNB_TABLE = "airbnb"
BONDS_TABLE = "rental_bonds"

AIRBNB_REQUIRED_COLUMNS = {
    "id",
    "location_id",
    "location_name",
    "month_year",
    "price",
}

BOND_REQUIRED_COLUMNS = {
    "Location Id",
    "TimeFrame",
    "quarter",
    "Dwelling Type",
    "Number Of Beds",
    "Median Rent",
    "Median Nightly Rent",
    "Active Bonds",
    "Total Bonds",
    "Closed Bonds",
}

EXPECTED_QUARTERS = {
    pd.Timestamp("2025-10-01"),
    pd.Timestamp("2026-01-01"),
    pd.Timestamp("2026-04-01"),
}

AGGREGATE_VALUE = "ALL"

DAYS_PER_WEEK = 7

# Require at least this many unique Airbnb listings before an
# SA2 area is included in the area-level price-gap summary.
MIN_LISTINGS_FOR_GAP_SUMMARY = 10


# ============================================================
# SQL QUERIES
# ============================================================

JOIN_QUERY = """
SELECT
    a.*,

    b."Median Rent"
        AS bond_median_weekly_rent,

    b."Median Nightly Rent"
        AS bond_nightly_rent,

    b."Active Bonds"
        AS bond_active_bonds,

    b."Total Bonds"
        AS bond_total_bonds,

    b."Closed Bonds"
        AS bond_closed_bonds,

    a.price - b."Median Nightly Rent"
        AS nightly_price_gap,

    CASE
        WHEN b."Location Id" IS NOT NULL
        THEN 'both'
        ELSE 'left_only'
    END AS merge_status

FROM airbnb AS a

LEFT JOIN rental_bonds AS b

    ON a.location_id = b."Location Id"
   AND a.quarter = b.quarter
"""


GAP_QUERY = """
SELECT
    a.location_id,
    a.location_name,
    a.id,

    a.price - b."Median Nightly Rent"
        AS nightly_price_gap

FROM airbnb AS a

INNER JOIN rental_bonds AS b

    ON a.location_id = b."Location Id"
   AND a.quarter = b.quarter

WHERE a.price > 0
  AND b."Median Nightly Rent" > 0
"""


# ============================================================
# HELPER
# ============================================================

def print_section(title):
    """Print a consistent section heading."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def validate_input_file(file_path):
    """Check that an expected pipeline input exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path.resolve()}"
        )


def validate_required_columns(
    dataframe,
    required_columns,
    dataset_name,
):
    """Check that all columns required by this stage are available."""

    missing_columns = (
        required_columns - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def standardise_location_id(series):
    """
    Standardise geographic identifiers defensively.

    The upstream cleaning stages should already have standardised
    these identifiers. This function protects the database join
    against representation differences such as '316700.0'.
    """

    return (
        series
        .astype("string")
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
        .replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "<NA>": pd.NA,
            }
        )
    )


# ============================================================
# LOAD AIRBNB
# ============================================================

def load_airbnb_data(file_path):
    """Load the processed SA2-enriched Airbnb dataset."""

    validate_input_file(file_path)

    airbnb_df = pd.read_excel(
        file_path,
        dtype={
            "id": "string",
            "location_id": "string",
        },
    )

    validate_required_columns(
        airbnb_df,
        AIRBNB_REQUIRED_COLUMNS,
        "Airbnb dataset",
    )

    airbnb_df["location_id"] = (
        standardise_location_id(
            airbnb_df["location_id"]
        )
    )

    airbnb_df["price"] = pd.to_numeric(
        airbnb_df["price"],
        errors="coerce",
    )

    print(
        f"Airbnb rows loaded: "
        f"{len(airbnb_df):,}"
    )

    return airbnb_df


# ============================================================
# PREPARE AIRBNB JOIN KEY
# ============================================================

def add_airbnb_quarter(airbnb_df):
    """
    Convert Airbnb month_year into the quarterly temporal join key.

    Examples:
        10_2025 -> 2025-10-01
        11_2025 -> 2025-10-01
        01_2026 -> 2026-01-01

    SQLite stores the resulting quarter as YYYY-MM-DD text.
    """

    prepared_df = airbnb_df.copy()

    prepared_df["month_date"] = pd.to_datetime(
        prepared_df["month_year"].astype(str),
        format="%m_%Y",
        errors="raise",
    )

    quarter_dates = (
        prepared_df["month_date"]
        .dt.to_period("Q")
        .dt.start_time
    )

    actual_quarters = set(
        quarter_dates.dropna().unique()
    )

    missing_quarters = (
        EXPECTED_QUARTERS - actual_quarters
    )

    unexpected_quarters = (
        actual_quarters - EXPECTED_QUARTERS
    )

    if missing_quarters or unexpected_quarters:
        raise ValueError(
            "Unexpected Airbnb quarter coverage.\n"
            f"Missing: {sorted(missing_quarters)}\n"
            f"Unexpected: {sorted(unexpected_quarters)}"
        )

    prepared_df["quarter"] = (
        quarter_dates.dt.strftime(
            "%Y-%m-%d"
        )
    )

    return prepared_df


# ============================================================
# LOAD RENTAL BONDS
# ============================================================

def load_bond_data(file_path):
    """Load the cleaned rental bond dataset."""

    validate_input_file(file_path)

    bond_df = pd.read_csv(
        file_path,
        dtype={
            "Location Id": "string",
        },
        low_memory=False,
    )

    validate_required_columns(
        bond_df,
        BOND_REQUIRED_COLUMNS,
        "Rental bond dataset",
    )

    bond_df["Location Id"] = (
        standardise_location_id(
            bond_df["Location Id"]
        )
    )

    print(
        f"Rental bond rows loaded: "
        f"{len(bond_df):,}"
    )

    return bond_df


# ============================================================
# VALIDATE CLEANED RENTAL BONDS
# ============================================================

def prepare_bond_data(bond_df):
    """
    Validate and prepare the upstream cleaned rental bond dataset.

    Filtering and cleaning should already have been completed by
    clean_rental_bonds.py. This function checks those assumptions
    instead of repeating the cleaning process.
    """

    prepared_df = bond_df.copy()

    if prepared_df["Location Id"].isna().any():
        raise ValueError(
            "Cleaned rental bond data contains "
            "missing Location Id values."
        )

    dwelling_type = (
        prepared_df["Dwelling Type"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    bed_count = (
        prepared_df["Number Of Beds"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    invalid_aggregate_rows = (
        ~dwelling_type.eq(AGGREGATE_VALUE)
        | ~bed_count.eq(AGGREGATE_VALUE)
    )

    if invalid_aggregate_rows.any():
        raise ValueError(
            "Cleaned rental bond data contains "
            "non-aggregate dwelling or bedroom records."
        )

    quarter_dates = pd.to_datetime(
        prepared_df["quarter"],
        errors="raise",
    )

    actual_quarters = set(
        quarter_dates.dropna().unique()
    )

    missing_quarters = (
        EXPECTED_QUARTERS - actual_quarters
    )

    unexpected_quarters = (
        actual_quarters - EXPECTED_QUARTERS
    )

    if missing_quarters or unexpected_quarters:
        raise ValueError(
            "Unexpected rental bond quarter coverage.\n"
            f"Missing: {sorted(missing_quarters)}\n"
            f"Unexpected: {sorted(unexpected_quarters)}"
        )

    prepared_df["quarter"] = (
        quarter_dates.dt.strftime(
            "%Y-%m-%d"
        )
    )

    numeric_columns = [
        "Median Rent",
        "Median Nightly Rent",
        "Active Bonds",
        "Total Bonds",
        "Closed Bonds",
    ]

    for column in numeric_columns:
        prepared_df[column] = pd.to_numeric(
            prepared_df[column],
            errors="coerce",
        )

    validate_bond_join_keys(
        prepared_df
    )

    return prepared_df


# ============================================================
# JOIN-KEY VALIDATION
# ============================================================

def validate_bond_join_keys(bond_df):
    """
    Ensure there is at most one rental bond record for each SA2-quarter.

    This is required because many Airbnb observations are expected to
    join to one rental bond observation.
    """

    duplicate_mask = bond_df.duplicated(
        subset=[
            "Location Id",
            "quarter",
        ],
        keep=False,
    )

    duplicate_count = (
        duplicate_mask.sum()
    )

    print(
        f"\nDuplicate bond area-quarter rows: "
        f"{duplicate_count:,}"
    )

    if duplicate_count:

        print("\nExample duplicate keys:")

        print(
            bond_df.loc[
                duplicate_mask,
                [
                    "Location Id",
                    "quarter",
                ],
            ]
            .sort_values(
                [
                    "Location Id",
                    "quarter",
                ]
            )
            .head(20)
            .to_string(index=False)
        )

        raise ValueError(
            "Duplicate rental bond area-quarter "
            "records found. The SQL join requires "
            "one bond record per Location Id and quarter."
        )

    print("Bond join-key uniqueness: PASS")


# ============================================================
# DATABASE
# ============================================================

def create_database(
    connection,
    airbnb_df,
    bond_df,
):
    """Create SQLite tables from the processed datasets."""

    print_section("CREATE SQLITE DATABASE")

    airbnb_df.to_sql(
        AIRBNB_TABLE,
        connection,
        if_exists="replace",
        index=False,
    )

    bond_df.to_sql(
        BONDS_TABLE,
        connection,
        if_exists="replace",
        index=False,
    )

    print(
        f"Created table '{AIRBNB_TABLE}': "
        f"{len(airbnb_df):,} rows"
    )

    print(
        f"Created table '{BONDS_TABLE}': "
        f"{len(bond_df):,} rows"
    )


def create_indexes(connection):
    """
    Create indexes for the columns used in the area-quarter join.

    Indexes improve lookup efficiency without changing the data.
    """

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_airbnb_location_quarter
        ON airbnb(location_id, quarter)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
            idx_bonds_location_quarter
        ON rental_bonds("Location Id", quarter)
        """
    )

    connection.commit()

    print("Database indexes created.")


# ============================================================
# SQL JOIN
# ============================================================

def run_sql_join(connection):
    """Run the SQL LEFT JOIN between Airbnb and rental bonds."""

    print_section("SQL LEFT JOIN")

    joined_df = pd.read_sql_query(
        JOIN_QUERY,
        connection,
    )

    return joined_df


def validate_sql_join(
    connection,
    joined_df,
):
    """
    Verify that the SQL LEFT JOIN preserves all Airbnb observations.
    """

    print_section("SQL JOIN VALIDATION")

    original_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM airbnb
        """
    ).fetchone()[0]

    joined_count = len(joined_df)

    print(
        f"Original Airbnb rows: "
        f"{original_count:,}"
    )

    print(
        f"Joined rows:          "
        f"{joined_count:,}"
    )

    if original_count != joined_count:
        raise AssertionError(
            "SQL join changed the Airbnb row count. "
            "Check rental bond area-quarter uniqueness."
        )

    print("\nJoin results:")

    join_counts = (
        joined_df["merge_status"]
        .value_counts(dropna=False)
    )

    print(
        join_counts.to_string()
    )

    matched_count = (
        joined_df["merge_status"]
        .eq("both")
        .sum()
    )

    unmatched_count = (
        joined_df["merge_status"]
        .eq("left_only")
        .sum()
    )

    if (
        matched_count + unmatched_count
        != joined_count
    ):
        raise AssertionError(
            "Unexpected SQL join status detected."
        )

    print(
        f"\nMatched rows:   "
        f"{matched_count:,}"
    )

    print(
        f"Unmatched rows: "
        f"{unmatched_count:,}"
    )

    if joined_count:
        match_rate = (
            matched_count
            / joined_count
            * 100
        )

        print(
            f"Match rate:     "
            f"{match_rate:.2f}%"
        )

    print("\nSQL join validation: PASS")


# ============================================================
# PRICE-GAP ANALYSIS
# ============================================================

def calculate_area_price_gaps(connection):
    """
    Calculate median Airbnb-versus-rental nightly price gaps by SA2.

    SQLite performs the row-level join and gap calculation. Pandas is
    used for the median because standard SQLite does not provide a
    built-in MEDIAN aggregate.

    Areas with fewer than MIN_LISTINGS_FOR_GAP_SUMMARY unique Airbnb
    listings are excluded from the final summary.
    """

    print_section("AREA PRICE-GAP ANALYSIS")

    gap_df = pd.read_sql_query(
        GAP_QUERY,
        connection,
    )

    if gap_df.empty:
        print(
            "No matched positive-price observations "
            "available for gap analysis."
        )

        return pd.DataFrame(
            columns=[
                "location_id",
                "location_name",
                "unique_listings",
                "median_nightly_gap",
            ]
        )

    gap_summary_df = (
        gap_df
        .groupby(
            [
                "location_id",
                "location_name",
            ],
            dropna=False,
        )
        .agg(
            unique_listings=(
                "id",
                "nunique",
            ),
            median_nightly_gap=(
                "nightly_price_gap",
                "median",
            ),
        )
        .reset_index()
    )

    gap_summary_df = (
        gap_summary_df.loc[
            gap_summary_df["unique_listings"]
            >= MIN_LISTINGS_FOR_GAP_SUMMARY
        ]
        .sort_values(
            "median_nightly_gap",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    print(
        f"Minimum unique listings per area: "
        f"{MIN_LISTINGS_FOR_GAP_SUMMARY}"
    )

    print("\nTop 10 median nightly price gaps:")

    print(
        gap_summary_df
        .head(10)
        .to_string(index=False)
    )

    return gap_summary_df


# ============================================================
# DATABASE SANITY CHECK
# ============================================================

def validate_database_tables(connection):
    """Check that expected SQLite tables contain records."""

    airbnb_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM airbnb
        """
    ).fetchone()[0]

    bond_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM rental_bonds
        """
    ).fetchone()[0]

    if airbnb_count == 0:
        raise AssertionError(
            "SQLite Airbnb table is empty."
        )

    if bond_count == 0:
        raise AssertionError(
            "SQLite rental_bonds table is empty."
        )

    print(
        f"\nDatabase sanity check: "
        f"{airbnb_count:,} Airbnb rows and "
        f"{bond_count:,} bond rows."
    )


# ============================================================
# OUTPUT
# ============================================================

def save_results(
    joined_df,
    gap_summary_df,
):
    """Save SQL-derived outputs separately from source datasets."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joined_df.to_csv(
        JOINED_OUTPUT_FILE,
        index=False,
    )

    gap_summary_df.to_csv(
        GAP_OUTPUT_FILE,
        index=False,
    )

    print_section("OUTPUT")

    print(
        f"SQLite database:\n"
        f"{DB_FILE}"
    )

    print(
        f"\nSQL joined dataset:\n"
        f"{JOINED_OUTPUT_FILE}"
    )

    print(
        f"\nArea price-gap summary:\n"
        f"{GAP_OUTPUT_FILE}"
    )


def verify_output_files(
    joined_df,
    gap_summary_df,
):
    """Reload exported CSV files and verify their basic structure."""

    saved_joined_df = pd.read_csv(
        JOINED_OUTPUT_FILE,
        low_memory=False,
    )

    saved_gap_df = pd.read_csv(
        GAP_OUTPUT_FILE,
    )

    if saved_joined_df.shape != joined_df.shape:
        raise AssertionError(
            "Saved SQL join output does not match "
            "the in-memory joined dataset shape."
        )

    if saved_gap_df.shape != gap_summary_df.shape:
        raise AssertionError(
            "Saved price-gap output does not match "
            "the in-memory summary shape."
        )

    print("\nSaved-file verification: PASS")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """Build and analyse the Christchurch rental SQLite database."""

    print("=" * 70)
    print("DATA422 - SQLITE AIRBNB / RENTAL BOND ANALYSIS")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    airbnb_df = load_airbnb_data(
        AIRBNB_FILE
    )

    airbnb_df = add_airbnb_quarter(
        airbnb_df
    )

    bond_df = load_bond_data(
        BONDS_FILE
    )

    bond_df = prepare_bond_data(
        bond_df
    )

    with sqlite3.connect(
        DB_FILE
    ) as connection:

        create_database(
            connection,
            airbnb_df,
            bond_df,
        )

        create_indexes(
            connection
        )

        validate_database_tables(
            connection
        )

        joined_df = run_sql_join(
            connection
        )

        validate_sql_join(
            connection,
            joined_df,
        )

        gap_summary_df = (
            calculate_area_price_gaps(
                connection
            )
        )

    save_results(
        joined_df,
        gap_summary_df,
    )

    verify_output_files(
        joined_df,
        gap_summary_df,
    )

    print(
        "\nSQLite processing completed successfully."
    )


if __name__ == "__main__":
    main()