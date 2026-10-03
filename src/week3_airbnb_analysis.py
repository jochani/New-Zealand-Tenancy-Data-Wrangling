"""
DATA422 - Christchurch Airbnb Data Preparation

Purpose:
    Load monthly Airbnb datasets, filter observations to Christchurch City,
    add the observation month, combine all monthly datasets, and produce
    basic summary statistics.

Inputs:
    Monthly Airbnb CSV files in data/airbnb/

Output:
    A combined Christchurch Airbnb DataFrame covering the study period.

The original input datasets are never modified.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# Project parameters
# ============================================================

AIRBNB_DATA_DIR = Path("data/airbnb")
TARGET_AREA = "Christchurch City"

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
    "neighbourhood_group",
    "number_of_reviews_ltm",
}


# ============================================================
# Data validation
# ============================================================

def validate_columns(airbnb_df, file_name):
    """Check that an Airbnb dataset contains the required columns."""

    missing_columns = REQUIRED_COLUMNS - set(airbnb_df.columns)

    if missing_columns:
        raise ValueError(
            f"{file_name} is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def extract_month_year(file_path):
    """
    Extract month and year from an Airbnb filename.

    Expected filename format:
        listings_DD_MM_YYYY.csv

    Example:
        listings_19_06_2026.csv -> 06_2026
    """

    filename_parts = file_path.stem.split("_")

    if len(filename_parts) < 4:
        raise ValueError(
            f"Unexpected filename format: {file_path.name}"
        )

    month = filename_parts[-2]
    year = filename_parts[-1]

    return f"{month}_{year}"


# ============================================================
# Data preparation
# ============================================================

def prepare_christchurch_dataset(file_path):
    """
    Load one monthly Airbnb dataset and prepare Christchurch observations.

    Returns:
        DataFrame containing only Christchurch City listings with
        a month_year column.
    """

    airbnb_df = pd.read_csv(file_path)

    validate_columns(airbnb_df, file_path.name)

    christchurch_df = airbnb_df[
        airbnb_df["neighbourhood_group"] == TARGET_AREA
    ].copy()

    christchurch_df["month_year"] = extract_month_year(file_path)

    return christchurch_df


def combine_monthly_datasets(data_directory):
    """
    Combine all monthly Christchurch Airbnb datasets.

    Returns:
        Combined DataFrame ordered chronologically.
    """

    csv_files = sorted(data_directory.glob("listings_*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No Airbnb CSV files found in {data_directory.resolve()}"
        )

    monthly_datasets = []

    for file_path in csv_files:
        print(f"Processing: {file_path.name}")

        christchurch_df = prepare_christchurch_dataset(file_path)

        print(
            f"  Christchurch listings: "
            f"{len(christchurch_df):,}"
        )

        monthly_datasets.append(christchurch_df)

    combined_airbnb_df = pd.concat(
        monthly_datasets,
        ignore_index=True,
    )

    combined_airbnb_df["_sort_date"] = pd.to_datetime(
        combined_airbnb_df["month_year"],
        format="%m_%Y",
    )

    combined_airbnb_df = (
        combined_airbnb_df
        .sort_values("_sort_date")
        .drop(columns="_sort_date")
        .reset_index(drop=True)
    )

    return combined_airbnb_df


# ============================================================
# Sanity checks
# ============================================================

def sanity_check_combined_data(combined_airbnb_df):
    """Check important assumptions about the combined dataset."""

    if combined_airbnb_df.empty:
        raise ValueError("Combined Airbnb dataset is empty.")

    # Every observation should be Christchurch City.
    unexpected_areas = set(
        combined_airbnb_df["neighbourhood_group"].dropna().unique()
    ) - {TARGET_AREA}

    if unexpected_areas:
        raise ValueError(
            f"Unexpected areas found: {unexpected_areas}"
        )

    # Check whether all expected study months are present.
    actual_months = set(
        combined_airbnb_df["month_year"].unique()
    )

    missing_months = EXPECTED_MONTHS - actual_months
    unexpected_months = actual_months - EXPECTED_MONTHS

    if missing_months:
        raise ValueError(
            f"Missing expected months: {sorted(missing_months)}"
        )

    if unexpected_months:
        print(
            "Warning - additional months found:",
            sorted(unexpected_months),
        )

    print("\nSanity checks passed.")
    print(f"Total rows: {len(combined_airbnb_df):,}")
    print(f"Months: {len(actual_months)}")


# ============================================================
# Summary statistics
# ============================================================

def display_monthly_counts(combined_airbnb_df):
    """Display the number of Airbnb observations for each month."""

    month_counts = (
        combined_airbnb_df
        .groupby("month_year")
        .size()
        .reset_index(name="number_of_listings")
    )

    month_counts["_date"] = pd.to_datetime(
        month_counts["month_year"],
        format="%m_%Y",
    )

    month_counts = (
        month_counts
        .sort_values("_date")
        .drop(columns="_date")
    )

    print("\nListings by month:")
    print(month_counts.to_string(index=False))


def display_summary_statistics(combined_airbnb_df):
    """Display numerical, categorical, and missing-value summaries."""

    print("\n" + "=" * 60)
    print("Dataset Overview")
    print("=" * 60)

    print(f"Rows    : {combined_airbnb_df.shape[0]:,}")
    print(f"Columns : {combined_airbnb_df.shape[1]}")

    print("\n" + "=" * 60)
    print("Numerical Summary Statistics")
    print("=" * 60)

    print(
        combined_airbnb_df
        .describe(include="number")
        .T
    )

    categorical_columns = (
        combined_airbnb_df
        .select_dtypes(include=["object", "string"])
        .columns
    )

    print("\n" + "=" * 60)
    print("Categorical Summary Statistics")
    print("=" * 60)

    print(
        combined_airbnb_df[
            categorical_columns
        ].describe().T
    )

    print("\n" + "=" * 60)
    print("Missing Values")
    print("=" * 60)

    missing_values = (
        combined_airbnb_df
        .isna()
        .sum()
        .sort_values(ascending=False)
    )

    print(missing_values)


# ============================================================
# Main pipeline
# ============================================================

def main():
    """Run the Christchurch Airbnb preparation pipeline."""

    print("Starting DATA422 Airbnb analysis...")
    print(f"Input directory: {AIRBNB_DATA_DIR.resolve()}")

    combined_airbnb_df = combine_monthly_datasets(
        AIRBNB_DATA_DIR
    )

    sanity_check_combined_data(combined_airbnb_df)

    display_monthly_counts(combined_airbnb_df)

    display_summary_statistics(combined_airbnb_df)


if __name__ == "__main__":
    main()