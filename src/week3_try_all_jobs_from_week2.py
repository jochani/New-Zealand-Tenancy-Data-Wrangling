"""
DATA422 - Week 3 Airbnb Exploratory Analysis

Purpose:
    Analyse the June 2026 New Zealand Airbnb dataset and compare
    Christchurch City with the national dataset.

Analysis:
    1. Compare Airbnb price distributions.
    2. Calculate days since the last review.
    3. Analyse listings in the top 10% by number of reviews.

Input:
    data/airbnb/listings_19_06_2026.csv

The original input dataset is not modified.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# Parameters
# ============================================================

INPUT_FILE = Path("data/airbnb/listings_19_06_2026.csv")

TARGET_AREA = "Christchurch City"

MAX_PLOT_PRICE = 2000
HISTOGRAM_BINS = 50
TOP_REVIEW_QUANTILE = 0.90

REQUIRED_COLUMNS = {
    "id",
    "name",
    "neighbourhood_group",
    "neighbourhood",
    "room_type",
    "price",
    "last_review",
    "number_of_reviews",
}


# ============================================================
# Loading and validation
# ============================================================

def load_airbnb_data(file_path):
    """Load an Airbnb CSV file and validate its required columns."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Airbnb dataset not found: {file_path.resolve()}"
        )

    airbnb_df = pd.read_csv(file_path)

    missing_columns = REQUIRED_COLUMNS - set(airbnb_df.columns)

    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    return airbnb_df


def filter_target_area(airbnb_df):
    """Return Airbnb observations belonging to the target area."""

    return airbnb_df[
        airbnb_df["neighbourhood_group"] == TARGET_AREA
    ].copy()


# ============================================================
# Price analysis
# ============================================================

def filter_prices_for_plot(airbnb_df):
    """Return observations with valid prices within the plotting range."""

    return airbnb_df[
        airbnb_df["price"].notna()
        & airbnb_df["price"].between(
            0,
            MAX_PLOT_PRICE,
        )
    ].copy()


def plot_price_distribution(price_df, area_name):
    """Plot the Airbnb nightly-price distribution for one area."""

    plt.figure(figsize=(10, 6))

    plt.hist(
        price_df["price"],
        bins=HISTOGRAM_BINS,
    )

    plt.title(
        f"Distribution of Airbnb Prices - {area_name}"
    )
    plt.xlabel("Price per night (NZD)")
    plt.ylabel("Number of listings")
    plt.xlim(0, MAX_PLOT_PRICE)

    plt.tight_layout()
    plt.show()


def plot_price_comparison(
    new_zealand_price_df,
    christchurch_price_df,
):
    """Compare NZ and Christchurch Airbnb price distributions."""

    plt.figure(figsize=(10, 6))

    plt.hist(
        new_zealand_price_df["price"],
        bins=HISTOGRAM_BINS,
        alpha=0.5,
        label="New Zealand",
    )

    plt.hist(
        christchurch_price_df["price"],
        bins=HISTOGRAM_BINS,
        alpha=0.5,
        label=TARGET_AREA,
    )

    plt.title(
        "Airbnb Price Distribution: "
        "New Zealand vs Christchurch"
    )
    plt.xlabel("Price per night (NZD)")
    plt.ylabel("Number of listings")
    plt.xlim(0, MAX_PLOT_PRICE)

    plt.legend()
    plt.tight_layout()
    plt.show()


# ============================================================
# Review-date analysis
# ============================================================

def extract_snapshot_date(file_path):
    """
    Extract the dataset snapshot date from the Airbnb filename.

    Expected format:
        listings_DD_MM_YYYY.csv
    """

    filename_parts = file_path.stem.split("_")

    if len(filename_parts) < 4:
        raise ValueError(
            f"Unexpected filename format: {file_path.name}"
        )

    day = filename_parts[-3]
    month = filename_parts[-2]
    year = filename_parts[-1]

    return pd.to_datetime(
        f"{year}-{month}-{day}",
        errors="raise",
    )


def add_days_since_last_review(airbnb_df, snapshot_date):
    """Calculate the number of days since each listing's last review."""

    result_df = airbnb_df.copy()

    result_df["last_review"] = pd.to_datetime(
        result_df["last_review"],
        errors="coerce",
    )

    result_df["days_since_last_review"] = (
        snapshot_date - result_df["last_review"]
    ).dt.days

    return result_df


def validate_review_days(airbnb_df):
    """Check calculated days-since-review values for impossible results."""

    negative_review_days = (
        airbnb_df["days_since_last_review"] < 0
    ).sum()

    if negative_review_days > 0:
        raise ValueError(
            f"Found {negative_review_days} reviews dated "
            "after the dataset snapshot date."
        )


def plot_days_since_last_review(airbnb_df):
    """Plot the distribution of days since the last Airbnb review."""

    review_days = (
        airbnb_df["days_since_last_review"]
        .dropna()
    )

    plt.figure(figsize=(10, 6))

    plt.hist(
        review_days,
        bins=HISTOGRAM_BINS,
    )

    plt.title(
        "Distribution of Days Since Last Airbnb Review "
        "- New Zealand"
    )
    plt.xlabel("Days since last review")
    plt.ylabel("Number of listings")

    plt.tight_layout()
    plt.show()


# ============================================================
# Review-count analysis
# ============================================================

def find_top_reviewed_listings(airbnb_df):
    """Return listings in the top 10% by total number of reviews."""

    review_threshold = airbnb_df[
        "number_of_reviews"
    ].quantile(TOP_REVIEW_QUANTILE)

    top_reviewed_df = airbnb_df[
        airbnb_df["number_of_reviews"] >= review_threshold
    ].copy()

    return top_reviewed_df, review_threshold


def display_top_review_summary(top_reviewed_df):
    """Display national and Christchurch top-review statistics."""

    top_christchurch_df = top_reviewed_df[
        top_reviewed_df["neighbourhood_group"] == TARGET_AREA
    ].copy()

    total_top_listings = len(top_reviewed_df)
    christchurch_top_listings = len(top_christchurch_df)

    if total_top_listings == 0:
        raise ValueError(
            "No listings were found above the review threshold."
        )

    christchurch_percentage = (
        christchurch_top_listings
        / total_top_listings
        * 100
    )

    print(
        f"Top-review listings in New Zealand: "
        f"{total_top_listings:,}"
    )

    print(
        f"Top-review listings in Christchurch: "
        f"{christchurch_top_listings:,}"
    )

    print(
        f"Percentage located in Christchurch: "
        f"{christchurch_percentage:.2f}%"
    )

    return top_christchurch_df


def display_highest_reviewed(
    top_reviewed_df,
    top_christchurch_df,
):
    """Display the highest-reviewed NZ and Christchurch listings."""

    display_columns = [
        "id",
        "name",
        "neighbourhood_group",
        "neighbourhood",
        "room_type",
        "price",
        "number_of_reviews",
    ]

    highest_reviewed = (
        top_reviewed_df[display_columns]
        .sort_values(
            "number_of_reviews",
            ascending=False,
        )
        .head(20)
    )

    print("\nHighest-reviewed New Zealand properties:")
    print(highest_reviewed.to_string(index=False))

    christchurch_columns = [
        "name",
        "neighbourhood",
        "price",
        "number_of_reviews",
    ]

    highest_christchurch = (
        top_christchurch_df[christchurch_columns]
        .sort_values(
            "number_of_reviews",
            ascending=False,
        )
        .head(10)
    )

    print("\nHighest-reviewed Christchurch properties:")
    print(highest_christchurch.to_string(index=False))


# ============================================================
# Main pipeline
# ============================================================

def main():
    """Run the Week 3 Airbnb exploratory analysis."""

    airbnb_df = load_airbnb_data(INPUT_FILE)

    print("June 2026 New Zealand dataset loaded.")
    print(f"Rows: {airbnb_df.shape[0]:,}")
    print(f"Columns: {airbnb_df.shape[1]}")

    # Christchurch subset
    christchurch_df = filter_target_area(airbnb_df)

    print(f"\nNew Zealand listings: {len(airbnb_df):,}")
    print(
        f"Christchurch listings: "
        f"{len(christchurch_df):,}"
    )

    # --------------------------------------------------------
    # Price analysis
    # --------------------------------------------------------

    new_zealand_price_df = filter_prices_for_plot(
        airbnb_df
    )

    christchurch_price_df = filter_prices_for_plot(
        christchurch_df
    )

    plot_price_distribution(
        new_zealand_price_df,
        "New Zealand",
    )

    plot_price_distribution(
        christchurch_price_df,
        TARGET_AREA,
    )

    plot_price_comparison(
        new_zealand_price_df,
        christchurch_price_df,
    )

    # --------------------------------------------------------
    # Last-review analysis
    # --------------------------------------------------------

    snapshot_date = extract_snapshot_date(INPUT_FILE)

    print(
        f"\nDataset snapshot date: "
        f"{snapshot_date.date()}"
    )

    airbnb_df = add_days_since_last_review(
        airbnb_df,
        snapshot_date,
    )

    validate_review_days(airbnb_df)

    print(
        airbnb_df[
            [
                "last_review",
                "days_since_last_review",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    plot_days_since_last_review(airbnb_df)

    # --------------------------------------------------------
    # Top-review analysis
    # --------------------------------------------------------

    top_reviewed_df, review_threshold = (
        find_top_reviewed_listings(airbnb_df)
    )

    print(
        f"\n90th percentile number of reviews: "
        f"{review_threshold:.2f}"
    )

    top_christchurch_df = display_top_review_summary(
        top_reviewed_df
    )

    display_highest_reviewed(
        top_reviewed_df,
        top_christchurch_df,
    )


if __name__ == "__main__":
    main()