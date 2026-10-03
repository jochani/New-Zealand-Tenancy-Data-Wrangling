"""
Join cleaned Christchurch Airbnb data with cleaned rental bond data.

DATA422 - New Zealand Tenancy Data Wrangling

Purpose
-------
Integrate SA2-enriched Christchurch Airbnb observations with cleaned
quarterly rental bond statistics.

The join uses:
    location_id + quarter

Each Airbnb observation may match at most one rental bond record for
its SA2 area and quarter.

Inputs
------
output/processed/christchurch_airbnb_clean_with_sa2.xlsx
output/processed/rental_bonds_clean.csv

Outputs
-------
output/processed/christchurch_airbnb_bonds_joined.csv
output/processed/airbnb_unmatched_bonds.csv

Design principles
-----------------
- Preserve the processed input datasets.
- Use relative project paths.
- Keep configuration values visible.
- Separate loading, validation, transformation, joining, and saving.
- Validate join assumptions before performing the merge.
- Use a many-to-one merge relationship explicitly.
- Preserve all Airbnb observations using a left join.
- Save unmatched observations for investigation.
- Check that the join does not unexpectedly change the Airbnb row count.
- Avoid repeating cleaning already performed by upstream pipeline stages.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

AIRBNB_FILE = Path(
    "output/processed/christchurch_airbnb_clean_with_sa2.xlsx"
)

BOND_FILE = Path(
    "output/processed/rental_bonds_clean.csv"
)

OUTPUT_FILE = Path(
    "output/processed/christchurch_airbnb_bonds_joined.csv"
)

UNMATCHED_FILE = Path(
    "output/logs/airbnb_unmatched_bonds.csv"
)

EXPECTED_QUARTERS = {
    pd.Timestamp("2025-10-01"),
    pd.Timestamp("2026-01-01"),
    pd.Timestamp("2026-04-01"),
}

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

JOIN_KEYS = [
    "location_id",
    "quarter",
]

BOND_LOOKUP_COLUMNS = [
    "Location Id",
    "quarter",
    "Median Rent",
    "Median Nightly Rent",
    "Active Bonds",
    "Total Bonds",
    "Closed Bonds",
]

BOND_COLUMN_NAMES = {
    "Location Id": "location_id",
    "Median Rent": "bond_median_weekly_rent",
    "Median Nightly Rent": "bond_nightly_rent",
    "Active Bonds": "bond_active_bonds",
    "Total Bonds": "bond_total_bonds",
    "Closed Bonds": "bond_closed_bonds",
}

# Known listing previously verified during SA2 assignment.
KNOWN_TEST_LISTING_ID = 40183765
EXPECTED_TEST_SA2_ID = "316700"


# ============================================================
# HELPER
# ============================================================

def print_section(title):
    """Print a consistent section heading."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def standardise_location_id(series):
    """
    Standardise geographic identifiers as strings.

    This protects the join against values such as '316700.0'
    versus '316700'.
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
# FILE VALIDATION
# ============================================================

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
    """Check that a dataset contains all columns required for joining."""

    missing_columns = (
        required_columns - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{sorted(missing_columns)}"
        )


# ============================================================
# LOAD INPUTS
# ============================================================

def load_airbnb_data(file_path):
    """Load and validate the SA2-enriched Airbnb dataset."""

    validate_input_file(file_path)

    airbnb_df = pd.read_excel(
        file_path,
        dtype={
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

    print(
        f"Airbnb rows loaded: "
        f"{len(airbnb_df):,}"
    )

    return airbnb_df


def load_bond_data(file_path):
    """Load and validate the cleaned rental bond dataset."""

    validate_input_file(file_path)

    if file_path.suffix.lower() == ".csv":
        bond_df = pd.read_csv(
            file_path,
            dtype={
                "Location Id": "string",
            },
            low_memory=False,
        )

    elif file_path.suffix.lower() in {
        ".xlsx",
        ".xls",
    }:
        bond_df = pd.read_excel(
            file_path,
            dtype={
                "Location Id": "string",
            },
        )

    else:
        raise ValueError(
            "Unsupported rental bond file format: "
            f"{file_path.suffix}"
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
# AIRBNB TEMPORAL KEY
# ============================================================

def add_airbnb_quarter(airbnb_df):
    """
    Convert Airbnb month_year values to quarterly join keys.

    Example:
        10_2025 -> 2025-10-01
        11_2025 -> 2025-10-01
        01_2026 -> 2026-01-01
    """

    prepared_df = airbnb_df.copy()

    prepared_df["month_date"] = pd.to_datetime(
        prepared_df["month_year"].astype(str),
        format="%m_%Y",
        errors="raise",
    )

    prepared_df["quarter"] = (
        prepared_df["month_date"]
        .dt.to_period("Q")
        .dt.start_time
    )

    actual_quarters = set(
        prepared_df["quarter"].dropna().unique()
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

    return prepared_df


# ============================================================
# VALIDATE CLEANED BOND INPUT
# ============================================================

def validate_cleaned_bond_data(bond_df):
    """
    Validate assumptions established by clean_rental_bonds.py.

    This join stage should not repeat upstream cleaning. Instead, it
    verifies that the cleaned rental bond input satisfies the contract
    expected by this stage.
    """

    validated_df = bond_df.copy()

    validated_df["TimeFrame"] = pd.to_datetime(
        validated_df["TimeFrame"],
        errors="raise",
    )

    validated_df["quarter"] = pd.to_datetime(
        validated_df["quarter"],
        errors="raise",
    )

    # The cleaning stage should already have retained only
    # aggregate ALL/ALL records.
    invalid_aggregate_rows = ~(
        validated_df["Dwelling Type"]
        .astype("string")
        .str.strip()
        .eq("ALL")
        &
        validated_df["Number Of Beds"]
        .astype("string")
        .str.strip()
        .eq("ALL")
    )

    if invalid_aggregate_rows.any():
        raise ValueError(
            "Cleaned bond input contains non-aggregate "
            "Dwelling Type or Number Of Beds records."
        )

    actual_quarters = set(
        validated_df["quarter"]
        .dropna()
        .unique()
    )

    missing_quarters = (
        EXPECTED_QUARTERS - actual_quarters
    )

    unexpected_quarters = (
        actual_quarters - EXPECTED_QUARTERS
    )

    if missing_quarters or unexpected_quarters:
        raise ValueError(
            "Cleaned rental bond input has unexpected "
            "quarter coverage.\n"
            f"Missing: {sorted(missing_quarters)}\n"
            f"Unexpected: {sorted(unexpected_quarters)}"
        )

    if validated_df["Location Id"].isna().any():
        raise ValueError(
            "Cleaned rental bond input contains "
            "missing Location Id values."
        )

    return validated_df


# ============================================================
# BOND LOOKUP
# ============================================================

def prepare_bond_lookup(bond_df):
    """
    Prepare the one-record-per-area-quarter lookup used in the join.
    """

    duplicate_mask = bond_df.duplicated(
        subset=[
            "Location Id",
            "quarter",
        ],
        keep=False,
    )

    duplicate_count = duplicate_mask.sum()

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
            "Multiple rental bond rows exist for the "
            "same Location Id and quarter. "
            "The Airbnb join requires a unique bond "
            "record for each area-quarter combination."
        )

    bond_lookup = (
        bond_df[BOND_LOOKUP_COLUMNS]
        .rename(
            columns=BOND_COLUMN_NAMES
        )
        .copy()
    )

    return bond_lookup


# ============================================================
# JOIN
# ============================================================

def join_airbnb_to_bonds(
    airbnb_df,
    bond_lookup,
):
    """
    Left join Airbnb observations to rental bond statistics.

    many_to_one means:
        many Airbnb observations
                ->
        one rental bond record per area-quarter.
    """

    original_row_count = len(airbnb_df)

    joined_df = airbnb_df.merge(
        bond_lookup,
        on=JOIN_KEYS,
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    if len(joined_df) != original_row_count:
        raise AssertionError(
            "The Airbnb-to-bond join changed the "
            "number of Airbnb observations. "
            f"Before: {original_row_count:,}; "
            f"after: {len(joined_df):,}."
        )

    return joined_df


# ============================================================
# DERIVED ANALYSIS VARIABLES
# ============================================================

def add_price_comparison(joined_df):
    """
    Calculate the difference between Airbnb nightly price and the
    median long-term rental nightly equivalent.

    bond_nightly_rent is produced upstream by clean_rental_bonds.py
    from median weekly rent / 7.

    The comparison is a unit-based analytical measure. It does not
    imply that Airbnb and long-term rental products are economically
    equivalent.
    """

    prepared_df = joined_df.copy()

    prepared_df["price"] = pd.to_numeric(
        prepared_df["price"],
        errors="coerce",
    )

    prepared_df[
        "bond_median_weekly_rent"
    ] = pd.to_numeric(
        prepared_df["bond_median_weekly_rent"],
        errors="coerce",
    )

    prepared_df[
        "bond_nightly_rent"
    ] = pd.to_numeric(
        prepared_df["bond_nightly_rent"],
        errors="coerce",
    )

    prepared_df["nightly_price_gap"] = (
        prepared_df["price"]
        - prepared_df["bond_nightly_rent"]
    )

    return prepared_df


# ============================================================
# JOIN VALIDATION
# ============================================================

def validate_join_results(
    airbnb_df,
    joined_df,
):
    """Report and validate the results of the integration stage."""

    print_section("JOIN VALIDATION")

    print(
        f"Original Airbnb rows: "
        f"{len(airbnb_df):,}"
    )

    print(
        f"Joined rows:          "
        f"{len(joined_df):,}"
    )

    print("\nJoin results:")

    join_counts = (
        joined_df["_merge"]
        .value_counts()
    )

    print(join_counts.to_string())

    if len(joined_df) != len(airbnb_df):
        raise AssertionError(
            "The join unexpectedly changed "
            "the Airbnb row count."
        )

    # A left join should never produce right_only rows.
    right_only_count = (
        joined_df["_merge"] == "right_only"
    ).sum()

    if right_only_count:
        raise AssertionError(
            "Unexpected right_only rows were produced "
            "by a left join."
        )

    matched_count = (
        joined_df["_merge"] == "both"
    ).sum()

    unmatched_count = (
        joined_df["_merge"] == "left_only"
    ).sum()

    if matched_count + unmatched_count != len(
        joined_df
    ):
        raise AssertionError(
            "Join-status counts do not equal "
            "the total joined row count."
        )

    print(
        f"\nMatched Airbnb rows:   "
        f"{matched_count:,}"
    )

    print(
        f"Unmatched Airbnb rows: "
        f"{unmatched_count:,}"
    )

    if len(joined_df):
        match_rate = (
            matched_count
            / len(joined_df)
            * 100
        )

        print(
            f"Bond match rate:       "
            f"{match_rate:.2f}%"
        )

    print("\nJoin validation: PASS")


# ============================================================
# KNOWN-LISTING SANITY CHECK
# ============================================================

def sanity_check_known_listing(joined_df):
    """
    Check that a previously verified Airbnb listing retains its SA2.

    This sanity check primarily validates that geographic information
    has survived the integration stage unchanged.
    """

    test_rows = joined_df.loc[
        joined_df["id"] == KNOWN_TEST_LISTING_ID,
        [
            "id",
            "location_id",
            "location_name",
            "quarter",
            "bond_median_weekly_rent",
            "_merge",
        ],
    ].drop_duplicates()

    if test_rows.empty:
        print(
            "\nKnown-listing sanity check skipped: "
            f"listing {KNOWN_TEST_LISTING_ID} "
            "is not present."
        )
        return

    print("\nKnown-listing sanity check:")
    print(
        test_rows.to_string(
            index=False
        )
    )

    observed_sa2_ids = set(
        test_rows["location_id"]
        .dropna()
        .astype(str)
    )

    if EXPECTED_TEST_SA2_ID not in observed_sa2_ids:
        raise AssertionError(
            f"Known listing {KNOWN_TEST_LISTING_ID} "
            f"does not retain expected SA2 "
            f"{EXPECTED_TEST_SA2_ID}."
        )

    print(
        "Known-listing SA2 check: PASS"
    )


# ============================================================
# UNMATCHED RECORDS
# ============================================================

def save_unmatched_records(
    joined_df,
    output_file,
):
    """
    Save Airbnb observations without a corresponding rental bond match.

    Unmatched records are retained for investigation rather than
    silently discarded.
    """

    unmatched_df = joined_df.loc[
        joined_df["_merge"] == "left_only"
    ].copy()

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    unmatched_df.to_csv(
        output_file,
        index=False,
    )

    print(
        f"\nUnmatched records saved: "
        f"{len(unmatched_df):,}"
    )

    print(
        f"Unmatched file: "
        f"{output_file}"
    )

    return unmatched_df


# ============================================================
# FINAL OUTPUT
# ============================================================

def save_joined_data(
    joined_df,
    output_file,
):
    """Save the final integrated dataset."""

    final_df = joined_df.drop(
        columns=["_merge"]
    ).copy()

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_df.to_csv(
        output_file,
        index=False,
    )

    print(
        f"\nJoined dataset saved to:\n"
        f"{output_file}"
    )

    return final_df


def verify_saved_output(
    final_df,
    output_file,
):
    """Reload the joined output and verify its basic structure."""

    saved_df = pd.read_csv(
        output_file,
        dtype={
            "location_id": "string",
        },
        low_memory=False,
    )

    if saved_df.shape != final_df.shape:
        raise ValueError(
            "Saved joined dataset shape does not match "
            "the in-memory dataset."
        )

    if list(saved_df.columns) != list(
        final_df.columns
    ):
        raise ValueError(
            "Saved joined dataset columns do not "
            "match the in-memory dataset."
        )

    print("\nSaved-file verification: PASS")

    print(
        f"Verified shape: "
        f"{saved_df.shape[0]:,} rows x "
        f"{saved_df.shape[1]} columns"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """Run the Airbnb and rental bond integration pipeline."""

    print("=" * 70)
    print("DATA422 - AIRBNB / RENTAL BOND INTEGRATION")
    print("=" * 70)

    airbnb_df = load_airbnb_data(
        AIRBNB_FILE
    )

    bond_df = load_bond_data(
        BOND_FILE
    )

    airbnb_df = add_airbnb_quarter(
        airbnb_df
    )

    bond_df = validate_cleaned_bond_data(
        bond_df
    )

    bond_lookup = prepare_bond_lookup(
        bond_df
    )

    joined_df = join_airbnb_to_bonds(
        airbnb_df,
        bond_lookup,
    )

    joined_df = add_price_comparison(
        joined_df
    )

    validate_join_results(
        airbnb_df,
        joined_df,
    )

    sanity_check_known_listing(
        joined_df
    )

    save_unmatched_records(
        joined_df,
        UNMATCHED_FILE,
    )

    final_df = save_joined_data(
        joined_df,
        OUTPUT_FILE,
    )

    verify_saved_output(
        final_df,
        OUTPUT_FILE,
    )

    print(
        "\nAirbnb / rental bond integration "
        "completed successfully."
    )


if __name__ == "__main__":
    main()