"""
Clean Christchurch Airbnb data for the DATA422 project.

DATA422 - New Zealand Tenancy Data Wrangling

Purpose
-------
Clean and validate the combined Christchurch Airbnb dataset covering
October 2025 to June 2026.

Input
-----
output/christchurch_oct2025_jun2026.csv

Output
------
output/processed/christchurch_airbnb_clean.csv.gz

Cleaning principles
-------------------
- Preserve the original input dataset.
- Preserve latitude and longitude for later SA2 assignment.
- Retain observations with missing prices because other fields remain useful.
- Do not impute missing prices in the primary cleaned dataset.
- Do not automatically remove price outliers.
- Recover selected missing values only when defensible information exists
  for the same host or listing.
- Remove fields that are not required for the planned analysis.
- Validate important assumptions before and after cleaning.
- Keep important parameters visible rather than using unexplained values.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path(
    "output/processed/christchurch_oct2025_jun2026.csv"
)

OUTPUT_FILE = Path(
    "output/processed/christchurch_airbnb_clean.csv.gz"
)

EXPECTED_ROWS = 28_795
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

REQUIRED_COLUMNS = {
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

GEOGRAPHIC_COLUMNS = {
    "neighbourhood",
    "latitude",
    "longitude",
}

COLUMNS_TO_DROP = [
    "neighbourhood_group",
    "last_review",
    "reviews_per_month",
    "license",
]

FINAL_COLUMNS = [
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
    "listing_price_median",
    "price_ratio_to_listing_median",
    "potential_price_outlier",
]

# Diagnostic thresholds only.
# Observations are flagged, not removed.
HIGH_PRICE_RATIO_THRESHOLD = 5.0
LOW_PRICE_RATIO_THRESHOLD = 0.20


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
    """Check that the expected input file exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path.resolve()}"
        )


def validate_required_columns(airbnb_df):
    """Check that all columns required by the pipeline are present."""

    missing_columns = (
        REQUIRED_COLUMNS - set(airbnb_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Required columns missing: "
            f"{sorted(missing_columns)}"
        )


def validate_dataset_dimensions(airbnb_df):
    """
    Check that the input matches the expected combined dataset.

    These dimensions are project-specific sanity checks for the
    October 2025 to June 2026 source dataset.
    """

    actual_rows, actual_columns = airbnb_df.shape

    if actual_rows != EXPECTED_ROWS:
        raise ValueError(
            f"Expected {EXPECTED_ROWS:,} rows, "
            f"but found {actual_rows:,}. "
            "Check the combined Airbnb input dataset."
        )

    if actual_columns != EXPECTED_COLUMNS:
        raise ValueError(
            f"Expected {EXPECTED_COLUMNS} columns, "
            f"but found {actual_columns}."
        )


def validate_month_coverage(airbnb_df):
    """Check that the dataset contains exactly the expected study months."""

    actual_months = set(
        airbnb_df["month_year"]
        .dropna()
        .astype(str)
        .unique()
    )

    missing_months = EXPECTED_MONTHS - actual_months
    unexpected_months = actual_months - EXPECTED_MONTHS

    if missing_months or unexpected_months:
        raise ValueError(
            "Unexpected month coverage.\n"
            f"Missing months: "
            f"{sorted(missing_months)}\n"
            f"Unexpected months: "
            f"{sorted(unexpected_months)}"
        )


def validate_geographic_columns(airbnb_df):
    """Check that variables needed for later SA2 mapping are available."""

    missing_columns = (
        GEOGRAPHIC_COLUMNS - set(airbnb_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Required geographic columns missing: "
            f"{sorted(missing_columns)}"
        )


def validate_coordinate_ranges(airbnb_df):
    """Check for impossible latitude or longitude values."""

    invalid_latitude = (
        airbnb_df["latitude"].notna()
        & ~airbnb_df["latitude"].between(-90, 90)
    )

    invalid_longitude = (
        airbnb_df["longitude"].notna()
        & ~airbnb_df["longitude"].between(-180, 180)
    )

    invalid_coordinates = (
        invalid_latitude | invalid_longitude
    ).sum()

    if invalid_coordinates:
        raise ValueError(
            f"Found {invalid_coordinates:,} rows with "
            "invalid latitude or longitude values."
        )


# ============================================================
# LOAD DATA
# ============================================================

def load_airbnb_data(file_path):
    """Load and validate the combined Christchurch Airbnb dataset."""

    validate_input_file(file_path)

    print(f"\nReading:\n{file_path}")

    airbnb_df = pd.read_csv(file_path)

    print("\nOriginal dataset:")
    print(f"Rows:    {len(airbnb_df):,}")
    print(f"Columns: {len(airbnb_df.columns)}")

    print_section("INPUT VALIDATION")

    validate_required_columns(airbnb_df)
    validate_dataset_dimensions(airbnb_df)
    validate_month_coverage(airbnb_df)
    validate_geographic_columns(airbnb_df)
    validate_coordinate_ranges(airbnb_df)

    print("Dataset dimensions: PASS")
    print("Required columns:   PASS")
    print("Month coverage:     PASS")
    print("Coordinate ranges:  PASS")

    return airbnb_df


# ============================================================
# INITIAL DATA QUALITY
# ============================================================

def report_initial_data_quality(airbnb_df):
    """Display missing values and duplicate information."""

    print_section("INITIAL DATA QUALITY")

    print("\nMissing values:")
    print(
        airbnb_df.isna()
        .sum()
        .to_string()
    )

    exact_duplicates = (
        airbnb_df.duplicated().sum()
    )

    listing_month_duplicates = (
        airbnb_df.duplicated(
            subset=["id", "month_year"]
        ).sum()
    )

    print(
        f"\nExact duplicate rows: "
        f"{exact_duplicates:,}"
    )

    print(
        f"Duplicate ID + month records: "
        f"{listing_month_duplicates:,}"
    )


# ============================================================
# DUPLICATES
# ============================================================

def remove_duplicates(airbnb_df):
    """
    Remove exact duplicates and duplicate listing-month records.

    A listing should have at most one observation for each monthly
    snapshot in the combined dataset.
    """

    cleaned_df = airbnb_df.copy()

    rows_before = len(cleaned_df)

    cleaned_df = cleaned_df.drop_duplicates()

    cleaned_df = cleaned_df.drop_duplicates(
        subset=["id", "month_year"],
        keep="first",
    )

    removed_count = (
        rows_before - len(cleaned_df)
    )

    print(
        f"\nDuplicate records removed: "
        f"{removed_count:,}"
    )

    return cleaned_df


# ============================================================
# COLUMN SELECTION
# ============================================================

def remove_unnecessary_columns(airbnb_df):
    """
    Remove columns not required by the planned analysis.

    neighbourhood_group:
        The combined input is already restricted to Christchurch City.

    last_review and reviews_per_month:
        Review timing/activity is outside the primary rental-price and
        property-availability comparison.

    license:
        Does not provide useful information for the planned analysis.
    """

    existing_columns = [
        column
        for column in COLUMNS_TO_DROP
        if column in airbnb_df.columns
    ]

    cleaned_df = airbnb_df.drop(
        columns=existing_columns
    ).copy()

    print("\nColumns removed:")

    for column in existing_columns:
        print(f"  - {column}")

    return cleaned_df


# ============================================================
# GEOGRAPHIC DATA
# ============================================================

def report_geographic_quality(airbnb_df):
    """Report missing coordinates required for later SA2 assignment."""

    missing_coordinates = (
        airbnb_df[
            ["latitude", "longitude"]
        ]
        .isna()
        .any(axis=1)
        .sum()
    )

    print(
        "\nRows with missing latitude/longitude: "
        f"{missing_coordinates:,}"
    )

    # Missing coordinates are reported rather than silently removed.
    return missing_coordinates


# ============================================================
# PRICE MISSINGNESS
# ============================================================

def report_price_missingness(airbnb_df):
    """Report overall and monthly Airbnb price missingness."""

    print_section("PRICE MISSINGNESS")

    missing_count = (
        airbnb_df["price"]
        .isna()
        .sum()
    )

    missing_percentage = (
        airbnb_df["price"]
        .isna()
        .mean()
        * 100
    )

    print(
        f"Missing prices: "
        f"{missing_count:,}"
    )

    print(
        f"Missing price percentage: "
        f"{missing_percentage:.2f}%"
    )

    monthly_missingness = (
        airbnb_df
        .groupby("month_year")["price"]
        .agg(
            total="size",
            observed="count",
            missing=lambda values:
                values.isna().sum(),
        )
    )

    monthly_missingness["missing_pct"] = (
        monthly_missingness["missing"]
        / monthly_missingness["total"]
        * 100
    ).round(2)

    # Sort chronologically rather than alphabetically.
    monthly_missingness = (
        monthly_missingness
        .assign(
            sort_date=pd.to_datetime(
                monthly_missingness.index,
                format="%m_%Y",
            )
        )
        .sort_values("sort_date")
        .drop(columns="sort_date")
    )

    print("\nMissing prices by month:")
    print(monthly_missingness.to_string())


def add_price_missing_flag(airbnb_df):
    """
    Flag missing prices without imputing or deleting them.

    Missing price observations are retained because other variables,
    including location and availability, remain useful.
    """

    cleaned_df = airbnb_df.copy()

    cleaned_df["price_was_missing"] = (
        cleaned_df["price"].isna()
    )

    return cleaned_df


# ============================================================
# HOST NAME MISSINGNESS
# ============================================================

def recover_missing_host_names(airbnb_df):
    """
    Recover a missing host name from another observation of the same host.

    Existing host information is used rather than inventing a value.
    If no known host name exists for the host, the value remains missing.
    """

    print_section("HOST NAME MISSINGNESS")

    cleaned_df = airbnb_df.copy()

    missing_before = (
        cleaned_df["host_name"]
        .isna()
        .sum()
    )

    print(
        f"Missing host_name before cleaning: "
        f"{missing_before:,}"
    )

    # Use one existing non-missing name for each host.
    host_name_lookup = (
        cleaned_df.loc[
            cleaned_df["host_name"].notna(),
            ["host_id", "host_name"],
        ]
        .drop_duplicates(
            subset=["host_id"],
            keep="first",
        )
        .set_index("host_id")["host_name"]
    )

    cleaned_df["host_name"] = (
        cleaned_df["host_name"].fillna(
            cleaned_df["host_id"].map(
                host_name_lookup
            )
        )
    )

    missing_after = (
        cleaned_df["host_name"]
        .isna()
        .sum()
    )

    recovered_count = (
        missing_before - missing_after
    )

    print(
        "Host names recovered from same host_id: "
        f"{recovered_count:,}"
    )

    print(
        "Missing host_name after cleaning: "
        f"{missing_after:,}"
    )

    return cleaned_df


# ============================================================
# MINIMUM NIGHTS MISSINGNESS
# ============================================================

def recover_missing_minimum_nights(airbnb_df):
    """
    Recover minimum_nights using historical observations of the same listing.

    The median known minimum_nights for the exact listing is used.
    If no historical value exists, the observation remains missing.
    """

    print_section("MINIMUM NIGHTS MISSINGNESS")

    cleaned_df = airbnb_df.copy()

    missing_before = (
        cleaned_df["minimum_nights"]
        .isna()
        .sum()
    )

    print(
        "Missing minimum_nights before cleaning: "
        f"{missing_before:,}"
    )

    listing_medians = (
        cleaned_df.loc[
            cleaned_df["minimum_nights"].notna()
        ]
        .groupby("id")["minimum_nights"]
        .median()
    )

    missing_mask = (
        cleaned_df["minimum_nights"].isna()
    )

    cleaned_df.loc[
        missing_mask,
        "minimum_nights",
    ] = (
        cleaned_df.loc[
            missing_mask,
            "id",
        ].map(listing_medians)
    )

    missing_after = (
        cleaned_df["minimum_nights"]
        .isna()
        .sum()
    )

    recovered_count = (
        missing_before - missing_after
    )

    print(
        "minimum_nights recovered from same listing: "
        f"{recovered_count:,}"
    )

    print(
        "Missing minimum_nights after cleaning: "
        f"{missing_after:,}"
    )

    return cleaned_df


# ============================================================
# PRICE OUTLIER DIAGNOSTIC
# ============================================================

def add_price_outlier_diagnostics(airbnb_df):
    """
    Flag unusual within-listing price movements without deleting them.

    A price is flagged when it is:
    - at least HIGH_PRICE_RATIO_THRESHOLD times the listing median, or
    - at most LOW_PRICE_RATIO_THRESHOLD times the listing median.

    Missing prices are never classified as price outliers.
    """

    print_section("PRICE OUTLIER DIAGNOSTIC")

    cleaned_df = airbnb_df.copy()

    listing_price_medians = (
        cleaned_df.loc[
            cleaned_df["price"].notna()
        ]
        .groupby("id")["price"]
        .median()
    )

    cleaned_df["listing_price_median"] = (
        cleaned_df["id"].map(
            listing_price_medians
        )
    )

    cleaned_df[
        "price_ratio_to_listing_median"
    ] = (
        cleaned_df["price"]
        / cleaned_df["listing_price_median"]
    )

    cleaned_df[
        "potential_price_outlier"
    ] = (
        (
            cleaned_df[
                "price_ratio_to_listing_median"
            ]
            >= HIGH_PRICE_RATIO_THRESHOLD
        )
        |
        (
            cleaned_df[
                "price_ratio_to_listing_median"
            ]
            <= LOW_PRICE_RATIO_THRESHOLD
        )
    )

    cleaned_df.loc[
        cleaned_df["price"].isna(),
        "potential_price_outlier",
    ] = False

    outlier_count = (
        cleaned_df[
            "potential_price_outlier"
        ]
        .sum()
    )

    print(
        "Potential price outliers flagged: "
        f"{outlier_count:,}"
    )

    return cleaned_df


# ============================================================
# FINAL COLUMN SELECTION
# ============================================================

def select_final_columns(airbnb_df):
    """Return the cleaned dataset in the documented column order."""

    missing_columns = (
        set(FINAL_COLUMNS)
        - set(airbnb_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Final output columns missing: "
            f"{sorted(missing_columns)}"
        )

    return airbnb_df[
        FINAL_COLUMNS
    ].copy()


# ============================================================
# FINAL VALIDATION
# ============================================================

def validate_cleaned_data(
    cleaned_df,
    source_row_count,
):
    """Run sanity checks on the cleaned dataset."""

    print_section("FINAL VALIDATION")

    print(
        f"Final rows:    "
        f"{len(cleaned_df):,}"
    )

    print(
        f"Final columns: "
        f"{len(cleaned_df.columns)}"
    )

    missing_latitude = (
        cleaned_df["latitude"]
        .isna()
        .sum()
    )

    missing_longitude = (
        cleaned_df["longitude"]
        .isna()
        .sum()
    )

    missing_prices = (
        cleaned_df["price"]
        .isna()
        .sum()
    )

    exact_duplicates = (
        cleaned_df.duplicated().sum()
    )

    listing_month_duplicates = (
        cleaned_df.duplicated(
            subset=["id", "month_year"]
        ).sum()
    )

    print(
        f"Missing latitude: "
        f"{missing_latitude:,}"
    )

    print(
        f"Missing longitude: "
        f"{missing_longitude:,}"
    )

    print(
        f"Missing prices retained: "
        f"{missing_prices:,}"
    )

    print(
        f"Exact duplicates remaining: "
        f"{exact_duplicates:,}"
    )

    print(
        "ID + month duplicates remaining: "
        f"{listing_month_duplicates:,}"
    )

    # Cleaning may remove duplicates, but should never create rows.
    if len(cleaned_df) > source_row_count:
        raise AssertionError(
            "Cleaning unexpectedly increased the row count."
        )

    if exact_duplicates != 0:
        raise AssertionError(
            "Exact duplicate rows remain after cleaning."
        )

    if listing_month_duplicates != 0:
        raise AssertionError(
            "Duplicate listing-month records remain "
            "after cleaning."
        )

    actual_months = set(
        cleaned_df["month_year"]
        .dropna()
        .astype(str)
        .unique()
    )

    if actual_months != EXPECTED_MONTHS:
        raise AssertionError(
            "Study month coverage changed during cleaning."
        )

    if not (
        cleaned_df["price_was_missing"]
        == cleaned_df["price"].isna()
    ).all():
        raise AssertionError(
            "price_was_missing does not match "
            "the actual missing-price values."
        )

    print("\nFinal validation: PASS")


# ============================================================
# OUTPUT
# ============================================================

def save_cleaned_data(
    cleaned_df,
    output_file,
):
    """Save the cleaned dataset without modifying the source file."""

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cleaned_df.to_csv(
        output_file,
        index=False,
        compression="gzip",
    )

    print_section("OUTPUT")

    print(
        "Clean dataset saved to:\n"
        f"{output_file}"
    )


def verify_saved_output(
    cleaned_df,
    output_file,
):
    """Reload the saved output and verify basic reproducibility."""

    saved_df = pd.read_csv(
        output_file,
        compression="gzip",
    )

    if saved_df.shape != cleaned_df.shape:
        raise ValueError(
            "Saved dataset shape does not match "
            "the cleaned in-memory dataset."
        )

    if list(saved_df.columns) != list(cleaned_df.columns):
        raise ValueError(
            "Saved dataset columns do not match "
            "the cleaned in-memory dataset."
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
    """Run the Christchurch Airbnb cleaning pipeline."""

    print("=" * 70)
    print("DATA422 - CHRISTCHURCH AIRBNB CLEANING")
    print("=" * 70)

    airbnb_df = load_airbnb_data(
        INPUT_FILE
    )

    source_row_count = len(airbnb_df)

    report_initial_data_quality(
        airbnb_df
    )

    cleaned_df = remove_duplicates(
        airbnb_df
    )

    cleaned_df = remove_unnecessary_columns(
        cleaned_df
    )

    report_geographic_quality(
        cleaned_df
    )

    report_price_missingness(
        cleaned_df
    )

    cleaned_df = add_price_missing_flag(
        cleaned_df
    )

    cleaned_df = recover_missing_host_names(
        cleaned_df
    )

    cleaned_df = recover_missing_minimum_nights(
        cleaned_df
    )

    cleaned_df = add_price_outlier_diagnostics(
        cleaned_df
    )

    cleaned_df = select_final_columns(
        cleaned_df
    )

    validate_cleaned_data(
        cleaned_df,
        source_row_count,
    )

    save_cleaned_data(
        cleaned_df,
        OUTPUT_FILE,
    )

    verify_saved_output(
        cleaned_df,
        OUTPUT_FILE,
    )

    print(
        "\nCleaning completed successfully."
    )


if __name__ == "__main__":
    main()