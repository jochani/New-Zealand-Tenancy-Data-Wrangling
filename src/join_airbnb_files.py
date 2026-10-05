"""
DATA422 - Airbnb Monthly Dataset Joining

Purpose:
    Automatically discover all listings_*.csv files,
    extract Christchurch City records, assign the
    month_year column, and generate one combined dataset.

Input:
    data/airbnb/listings_*.csv

Output:
    output/processed/christchurch_airbnb_joined_file.csv
"""

import re
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "airbnb"

OUTPUT_FILE = (
    BASE_DIR
    / "output"
    / "processed"
    / "christchurch_airbnb_joined_file.csv"
)

FILE_PATTERN = "listings_*.csv"

REQUIRED_RAW_COLUMNS = {
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
}

# Add month_year to the raw columns
OUTPUT_COLUMNS = sorted(
    REQUIRED_RAW_COLUMNS | {"month_year"}
)


# ============================================================
# JOIN AIRBNB FILES
# ============================================================

def join_airbnb_files():
    """
    Discover and combine monthly Airbnb datasets.

    Steps:
        1. Discover all listings_*.csv files.
        2. Extract snapshot month from filename.
        3. Filter Christchurch City records.
        4. Add month_year.
        5. Select the required 19 columns.
        6. Save the combined CSV file.
    """

    print("\n" + "=" * 70)
    print("DATA422 - JOIN AIRBNB MONTHLY DATASETS")
    print("=" * 70)

    files = sorted(
        RAW_DATA_DIR.glob(FILE_PATTERN)
    )

    if not files:
        raise FileNotFoundError(
            f"No Airbnb CSV files found in {RAW_DATA_DIR}"
        )

    print(f"\nMonthly files discovered: {len(files)}")

    dataframes = []
    processed_months = set()

    for file in files:

        print(f"\nProcessing: {file.name}")

        # Example: listings_12_07_2026.csv
        match = re.fullmatch(
            r"listings_(\d{2})_(\d{2})_(\d{4})\.csv",
            file.name
        )

        if not match:
            raise ValueError(
                f"Invalid filename: {file.name}"
            )

        day, month, year = match.groups()

        snapshot_date = pd.to_datetime(
            f"{day}_{month}_{year}",
            format="%d_%m_%Y",
            errors="raise"
        )

        month_year = snapshot_date.strftime("%m_%Y")

        if month_year in processed_months:
            raise ValueError(
                f"Duplicate monthly snapshot: {month_year}"
            )

        processed_months.add(month_year)

        # Read the raw dataset
        df = pd.read_csv(
            file,
            low_memory=False,
            dtype={"id": "string", "host_id": "string"}
        )

        print(f"Raw records: {len(df):,}")

        # Validate required columns
        missing_columns = (
            REQUIRED_RAW_COLUMNS - set(df.columns)
        )

        if missing_columns:
            raise ValueError(
                f"Missing columns in {file.name}: "
                f"{sorted(missing_columns)}"
            )

        # Filter Christchurch City
        df = df[
            df["neighbourhood_group"]
            .astype("string")
            .str.strip()
            .eq("Christchurch City")
        ].copy()

        if df.empty:
            raise ValueError(
                f"No Christchurch City records in {file.name}. "
                "Verify the geographic filtering column."
            )

        print(f"Christchurch records: {len(df):,}")

        # Assign month
        df["month_year"] = month_year

        # Select required columns
        df = df[OUTPUT_COLUMNS].copy()

        dataframes.append(df)

    # Combine monthly datasets
    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    # Chronological sorting
    combined_df["_sort_date"] = pd.to_datetime(
        combined_df["month_year"],
        format="%m_%Y"
    )

    combined_df = (
        combined_df
        .sort_values(["_sort_date", "id"])
        .drop(columns="_sort_date")
        .reset_index(drop=True)
    )

    # Save combined dataset
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    combined_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("JOIN SUMMARY")
    print("=" * 70)

    print(f"Files processed: {len(files)}")
    print(f"Combined rows: {len(combined_df):,}")
    print(f"Combined columns: {len(combined_df.columns)}")

    print("\nRows per month:")

    print(
        combined_df.groupby(
            "month_year",
            sort=False
        ).size().to_string()
    )

    print(f"\nOutput saved: {OUTPUT_FILE}")

    return OUTPUT_FILE


if __name__ == "__main__":
    join_airbnb_files()