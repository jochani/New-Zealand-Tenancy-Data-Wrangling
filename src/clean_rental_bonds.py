"""
Clean New Zealand rental bond data for the DATA422 project.

DATA422 - New Zealand Tenancy Data Wrangling

Purpose
-------
Prepare quarterly rental bond statistics for integration with the
Christchurch Airbnb dataset.

Input
-----
output/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv

Output
------
output/processed/rental_bonds_clean.csv

Cleaning principles
-------------------
- Preserve the original source dataset.
- Use only quarters required by the Airbnb study period.
- Retain area-level aggregate rental statistics.
- Standardise geographic location identifiers.
- Convert rental measures to appropriate numeric data types.
- Validate area-quarter uniqueness before joining with Airbnb data.
- Make important analytical parameters explicit.
- Do not silently remove unexpected duplicate area-quarter records.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path(
    "data/bonds/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
)

OUTPUT_FILE = Path(
    "output/processed/rental_bonds_clean.csv"
)

REQUIRED_QUARTERS = pd.to_datetime([
    "2025-10-01",
    "2026-01-01",
    "2026-04-01",
])

AGGREGATE_DWELLING_TYPE = "ALL"
AGGREGATE_BED_COUNT = "ALL"

DAYS_PER_WEEK = 7

REQUIRED_COLUMNS = {
    "TimeFrame",
    "Location Id",
    "Dwelling Type",
    "Number Of Beds",
    "Total Bonds",
    "Active Bonds",
    "Closed Bonds",
    "Median Rent",
    "Geometric Mean Rent",
    "Upper Quartile Rent",
    "Lower Quartile Rent",
    "Log Std Dev Weekly Rent",
}

NUMERIC_COLUMNS = [
    "Total Bonds",
    "Active Bonds",
    "Closed Bonds",
    "Median Rent",
    "Geometric Mean Rent",
    "Upper Quartile Rent",
    "Lower Quartile Rent",
    "Log Std Dev Weekly Rent",
]


# ============================================================
# HELPER
# ============================================================

def print_section(title):
    """Print a consistent section heading."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_input_file(file_path):
    """Check that the rental bond source file exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path.resolve()}"
        )


def validate_required_columns(rental_df):
    """Check that all required rental bond columns are available."""

    missing_columns = (
        REQUIRED_COLUMNS - set(rental_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Rental bond dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )


# ============================================================
# LOAD DATA
# ============================================================

def load_rental_bond_data(file_path):
    """Load and validate the original rental bond dataset."""

    validate_input_file(file_path)

    print(f"\nReading:\n{file_path}")

    rental_df = pd.read_csv(
        file_path,
        dtype={"Location Id": "string"},
        low_memory=False,
    )

    validate_required_columns(rental_df)

    print("\nOriginal dataset:")
    print(f"Rows:    {len(rental_df):,}")
    print(f"Columns: {len(rental_df.columns)}")

    print("\nOriginal missing values:")
    print(
        rental_df.isna()
        .sum()
        .to_string()
    )

    return rental_df


# ============================================================
# LOCATION IDENTIFIERS
# ============================================================

def standardise_location_ids(rental_df):
    """
    Standardise rental bond location identifiers.

    Location identifiers are stored as strings because they represent
    geographic codes rather than quantities used in calculations.
    """

    cleaned_df = rental_df.copy()

    cleaned_df["Location Id"] = (
        cleaned_df["Location Id"]
        .astype("string")
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
    )

    cleaned_df["Location Id"] = (
        cleaned_df["Location Id"].replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "<NA>": pd.NA,
            }
        )
    )

    return cleaned_df


# ============================================================
# TIMEFRAME
# ============================================================

def prepare_timeframe(rental_df):
    """Convert TimeFrame to datetime and report invalid values."""

    cleaned_df = rental_df.copy()

    original_non_missing = (
        cleaned_df["TimeFrame"].notna()
    )

    cleaned_df["TimeFrame"] = pd.to_datetime(
        cleaned_df["TimeFrame"],
        errors="coerce",
    )

    invalid_dates = (
        original_non_missing
        & cleaned_df["TimeFrame"].isna()
    ).sum()

    print(
        f"\nInvalid TimeFrame values after conversion: "
        f"{invalid_dates:,}"
    )

    if invalid_dates:
        raise ValueError(
            f"Found {invalid_dates:,} invalid TimeFrame values."
        )

    return cleaned_df


def filter_required_quarters(rental_df):
    """Keep only quarters required for the project study period."""

    filtered_df = rental_df.loc[
        rental_df["TimeFrame"].isin(
            REQUIRED_QUARTERS
        )
    ].copy()

    if filtered_df.empty:
        raise ValueError(
            "No rental bond records remain after "
            "filtering the required quarters."
        )

    actual_quarters = set(
        filtered_df["TimeFrame"].unique()
    )

    expected_quarters = set(
        REQUIRED_QUARTERS
    )

    missing_quarters = (
        expected_quarters - actual_quarters
    )

    if missing_quarters:
        missing_text = [
            pd.Timestamp(value).strftime("%Y-%m-%d")
            for value in sorted(missing_quarters)
        ]

        raise ValueError(
            "Required rental quarters are missing: "
            f"{missing_text}"
        )

    print(
        f"\nRows after quarter filtering: "
        f"{len(filtered_df):,}"
    )

    return filtered_df


# ============================================================
# AGGREGATE RENTAL RECORDS
# ============================================================

def filter_area_aggregates(rental_df):
    """
    Retain overall area-level rental statistics.

    Dwelling Type = ALL and Number Of Beds = ALL are used because the
    project compares overall Airbnb activity with the overall long-term
    rental market at geographic-area level.
    """

    filtered_df = rental_df.copy()

    filtered_df["Dwelling Type"] = (
        filtered_df["Dwelling Type"]
        .astype("string")
        .str.strip()
    )

    filtered_df["Number Of Beds"] = (
        filtered_df["Number Of Beds"]
        .astype("string")
        .str.strip()
    )

    filtered_df = filtered_df.loc[
        filtered_df["Dwelling Type"].eq(
            AGGREGATE_DWELLING_TYPE
        )
        & filtered_df["Number Of Beds"].eq(
            AGGREGATE_BED_COUNT
        )
    ].copy()

    if filtered_df.empty:
        raise ValueError(
            "No records remain after filtering "
            "for area-level aggregate statistics."
        )

    print(
        f"Rows after aggregate filtering: "
        f"{len(filtered_df):,}"
    )

    return filtered_df


# ============================================================
# MISSING LOCATION IDENTIFIERS
# ============================================================

def remove_missing_location_ids(rental_df):
    """
    Remove records that cannot be geographically joined.

    A missing Location Id prevents the observation from being matched
    to an Airbnb SA2 area, so these rows cannot be used in the
    integration stage.
    """

    missing_before = (
        rental_df["Location Id"]
        .isna()
        .sum()
    )

    cleaned_df = rental_df.dropna(
        subset=["Location Id"]
    ).copy()

    print(
        f"Rows removed with missing Location Id: "
        f"{missing_before:,}"
    )

    return cleaned_df


# ============================================================
# NUMERIC VARIABLES
# ============================================================

def convert_numeric_columns(rental_df):
    """Convert rental-market measures to numeric values."""

    cleaned_df = rental_df.copy()

    for column in NUMERIC_COLUMNS:

        original_non_missing = (
            cleaned_df[column].notna()
        )

        cleaned_df[column] = pd.to_numeric(
            cleaned_df[column],
            errors="coerce",
        )

        newly_missing = (
            original_non_missing
            & cleaned_df[column].isna()
        ).sum()

        if newly_missing:
            print(
                f"Warning: {newly_missing:,} values in "
                f"'{column}' could not be converted to numeric."
            )

    return cleaned_df


# ============================================================
# JOINING QUARTER
# ============================================================

def add_join_quarter(rental_df):
    """Create the quarter key used when joining with Airbnb data."""

    cleaned_df = rental_df.copy()

    cleaned_df["quarter"] = (
        cleaned_df["TimeFrame"]
        .dt.to_period("Q")
        .dt.start_time
    )

    return cleaned_df


# ============================================================
# DUPLICATE VALIDATION
# ============================================================

def validate_area_quarter_uniqueness(rental_df):
    """
    Ensure each Location Id and quarter combination is unique.

    The later Airbnb-to-bond join expects one rental bond record for
    each geographic area and quarter.
    """

    duplicate_mask = rental_df.duplicated(
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
        f"\nDuplicate area-quarter rows: "
        f"{duplicate_count:,}"
    )

    if duplicate_count:

        duplicate_examples = (
            rental_df.loc[
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
        )

        print("\nExample duplicates:")
        print(
            duplicate_examples.to_string(
                index=False
            )
        )

        raise ValueError(
            "Duplicate area-quarter records found. "
            "The later join requires one rental record "
            "per Location Id and quarter."
        )

    print("Area-quarter uniqueness: PASS")


# ============================================================
# RENTAL PRICE DERIVATION
# ============================================================

def add_nightly_rent_equivalent(rental_df):
    """
    Convert median weekly rent to a nightly equivalent.

    This supports comparison with Airbnb nightly prices. It is a simple
    unit conversion, not an assertion that long-term and short-term
    accommodation are economically equivalent.
    """

    cleaned_df = rental_df.copy()

    cleaned_df["Median Nightly Rent"] = (
        cleaned_df["Median Rent"]
        / DAYS_PER_WEEK
    )

    return cleaned_df


# ============================================================
# FINAL VALIDATION
# ============================================================

def validate_cleaned_data(rental_df):
    """Run final sanity checks on the cleaned rental bond dataset."""

    print_section("FINAL VALIDATION")

    if rental_df.empty:
        raise AssertionError(
            "Cleaned rental bond dataset is empty."
        )

    missing_location_ids = (
        rental_df["Location Id"]
        .isna()
        .sum()
    )

    if missing_location_ids:
        raise AssertionError(
            "Cleaned dataset still contains missing Location Id values."
        )

    actual_quarters = set(
        rental_df["quarter"].unique()
    )

    expected_quarters = set(
        REQUIRED_QUARTERS
    )

    if actual_quarters != expected_quarters:
        raise AssertionError(
            "Cleaned dataset does not contain exactly "
            "the required study quarters."
        )

    duplicate_count = rental_df.duplicated(
        subset=[
            "Location Id",
            "quarter",
        ]
    ).sum()

    if duplicate_count:
        raise AssertionError(
            "Duplicate area-quarter combinations remain "
            "in the cleaned dataset."
        )

    # Rental counts should not logically be negative.
    bond_count_columns = [
        "Total Bonds",
        "Active Bonds",
        "Closed Bonds",
    ]

    for column in bond_count_columns:
        negative_count = (
            rental_df[column] < 0
        ).sum()

        if negative_count:
            raise AssertionError(
                f"Found {negative_count:,} negative "
                f"values in '{column}'."
            )

    # Rental values should not logically be negative.
    rent_columns = [
        "Median Rent",
        "Geometric Mean Rent",
        "Upper Quartile Rent",
        "Lower Quartile Rent",
        "Median Nightly Rent",
    ]

    for column in rent_columns:
        negative_count = (
            rental_df[column] < 0
        ).sum()

        if negative_count:
            raise AssertionError(
                f"Found {negative_count:,} negative "
                f"values in '{column}'."
            )

    print(
        f"Final rows:    "
        f"{len(rental_df):,}"
    )

    print(
        f"Final columns: "
        f"{len(rental_df.columns)}"
    )

    print("\nRows per quarter:")

    print(
        rental_df["quarter"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nMissing values:")

    print(
        rental_df.isna()
        .sum()
        .to_string()
    )

    print(
        f"\nUnique locations: "
        f"{rental_df['Location Id'].nunique():,}"
    )

    print("\nFinal validation: PASS")


# ============================================================
# OUTPUT
# ============================================================

def save_cleaned_data(
    rental_df,
    output_file,
):
    """Save cleaned rental bond data without modifying the source."""

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rental_df.to_csv(
        output_file,
        index=False,
    )

    print_section("OUTPUT")

    print(
        "Cleaned rental bond dataset saved to:\n"
        f"{output_file}"
    )


def verify_saved_output(
    rental_df,
    output_file,
):
    """Reload the saved file and verify its basic structure."""

    saved_df = pd.read_csv(
        output_file,
        dtype={"Location Id": "string"},
        parse_dates=[
            "TimeFrame",
            "quarter",
        ],
    )

    if saved_df.shape != rental_df.shape:
        raise ValueError(
            "Saved rental bond dataset shape does "
            "not match the in-memory cleaned dataset."
        )

    if list(saved_df.columns) != list(
        rental_df.columns
    ):
        raise ValueError(
            "Saved rental bond columns do not match "
            "the in-memory cleaned dataset."
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
    """Run the rental bond cleaning pipeline."""

    print("=" * 70)
    print("DATA422 - RENTAL BOND CLEANING")
    print("=" * 70)

    rental_df = load_rental_bond_data(
        INPUT_FILE
    )

    rental_df = standardise_location_ids(
        rental_df
    )

    rental_df = prepare_timeframe(
        rental_df
    )

    rental_df = filter_required_quarters(
        rental_df
    )

    rental_df = filter_area_aggregates(
        rental_df
    )

    rental_df = remove_missing_location_ids(
        rental_df
    )

    rental_df = convert_numeric_columns(
        rental_df
    )

    rental_df = add_join_quarter(
        rental_df
    )

    validate_area_quarter_uniqueness(
        rental_df
    )

    rental_df = add_nightly_rent_equivalent(
        rental_df
    )

    validate_cleaned_data(
        rental_df
    )

    save_cleaned_data(
        rental_df,
        OUTPUT_FILE,
    )

    verify_saved_output(
        rental_df,
        OUTPUT_FILE,
    )

    print(
        "\nRental bond cleaning completed successfully."
    )


if __name__ == "__main__":
    main()