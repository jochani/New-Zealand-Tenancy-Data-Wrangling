"""
Generate updated plots for the DATA422 Christchurch Airbnb
and rental bond analysis.

DATA422 - New Zealand Tenancy Data Wrangling

Purpose
-------
Generate automatically updated visualisations from the processed
Airbnb dataset and SQLite analysis outputs.

The script does not hard-code individual months. Therefore, when
new monthly Airbnb data is added to the upstream pipeline, the
plots automatically include the new observations.

Inputs
------
output/processed/christchurch_airbnb_clean_with_sa2.csv
output/sqlite/sql_area_price_gaps.csv

Outputs
-------
output/plots/monthly_listing_count.png
output/plots/monthly_median_price.png
output/plots/monthly_missing_price_percentage.png
output/plots/sa2_airbnb_rental_price_gap.png
output/plots/monthly_summary.csv
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

AIRBNB_FILE = Path(
    "output/processed/christchurch_airbnb_clean_with_sa2.csv"
)

PRICE_GAP_FILE = Path(
    "output/sqlite/sql_area_price_gaps.csv"
)

OUTPUT_DIR = Path(
    "output/plots"
)

MONTHLY_SUMMARY_FILE = (
    OUTPUT_DIR / "monthly_summary.csv"
)

LISTING_COUNT_PLOT = (
    OUTPUT_DIR / "monthly_listing_count.png"
)

MEDIAN_PRICE_PLOT = (
    OUTPUT_DIR / "monthly_median_price.png"
)

MISSING_PRICE_PLOT = (
    OUTPUT_DIR / "monthly_missing_price_percentage.png"
)

PRICE_GAP_PLOT = (
    OUTPUT_DIR / "sa2_airbnb_rental_price_gap.png"
)

AIRBNB_REQUIRED_COLUMNS = {
    "id",
    "month_year",
    "price",
}

GAP_REQUIRED_COLUMNS = {
    "location_id",
    "location_name",
    "unique_listings",
    "median_nightly_gap",
}

TOP_N_AREAS = 10


# ============================================================
# HELPERS
# ============================================================

def print_section(title):
    """Print a consistent console section heading."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def validate_input_file(file_path):
    """Check that a required pipeline input exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path.resolve()}"
        )


def validate_required_columns(
    dataframe,
    required_columns,
    dataset_name,
):
    """Check that required columns are available."""

    missing_columns = (
        required_columns - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def save_plot(output_file):
    """
    Save the current Matplotlib figure and close it.

    Closing each figure prevents figures accumulating in memory
    when this script is called from the complete pipeline.
    """

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Saved: {output_file}")


# ============================================================
# LOAD AIRBNB
# ============================================================

def load_airbnb_data(file_path):
    """Load the processed SA2-enriched Airbnb dataset."""

    validate_input_file(file_path)

    airbnb_df = pd.read_csv(
        file_path,
        dtype={
            "id": "string",
            "location_id": "string",
        },
        low_memory=False,
    )

    validate_required_columns(
        airbnb_df,
        AIRBNB_REQUIRED_COLUMNS,
        "Airbnb dataset",
    )

    airbnb_df["price"] = pd.to_numeric(
        airbnb_df["price"],
        errors="coerce",
    )

    # Convert month_year into a real date so plotting order
    # is chronological rather than alphabetical.
    airbnb_df["month_date"] = pd.to_datetime(
        airbnb_df["month_year"].astype(str),
        format="%m_%Y",
        errors="raise",
    )

    print(
        f"Airbnb rows loaded: "
        f"{len(airbnb_df):,}"
    )

    print(
        f"Months available: "
        f"{airbnb_df['month_date'].nunique()}"
    )

    return airbnb_df


# ============================================================
# MONTHLY SUMMARY
# ============================================================

def create_monthly_summary(airbnb_df):
    """
    Calculate monthly Airbnb metrics.

    Metrics:
    - number of observations
    - number of unique listings
    - observed prices
    - missing prices
    - missing-price percentage
    - median nightly Airbnb price
    """

    print_section("MONTHLY AIRBNB SUMMARY")

    monthly_summary = (
        airbnb_df
        .groupby(
            "month_date",
            as_index=False,
        )
        .agg(
            observations=(
                "id",
                "size",
            ),
            unique_listings=(
                "id",
                "nunique",
            ),
            observed_prices=(
                "price",
                "count",
            ),
            median_price=(
                "price",
                "median",
            ),
        )
    )

    monthly_summary["missing_prices"] = (
        monthly_summary["observations"]
        - monthly_summary["observed_prices"]
    )

    monthly_summary[
        "missing_price_percentage"
    ] = (
        monthly_summary["missing_prices"]
        / monthly_summary["observations"]
        * 100
    )

    monthly_summary = (
        monthly_summary
        .sort_values("month_date")
        .reset_index(drop=True)
    )

    monthly_summary["month_year"] = (
        monthly_summary["month_date"]
        .dt.strftime("%m_%Y")
    )

    # Arrange output columns in a readable order.
    monthly_summary = monthly_summary[
        [
            "month_date",
            "month_year",
            "observations",
            "unique_listings",
            "observed_prices",
            "missing_prices",
            "missing_price_percentage",
            "median_price",
        ]
    ]

    print(
        monthly_summary[
            [
                "month_year",
                "unique_listings",
                "median_price",
                "missing_prices",
                "missing_price_percentage",
            ]
        ].to_string(
            index=False,
            formatters={
                "median_price":
                    lambda value: (
                        f"{value:.2f}"
                        if pd.notna(value)
                        else "NA"
                    ),
                "missing_price_percentage":
                    lambda value: f"{value:.2f}%",
            },
        )
    )

    return monthly_summary


def save_monthly_summary(monthly_summary):
    """Save monthly analysis results as CSV."""

    monthly_summary.to_csv(
        MONTHLY_SUMMARY_FILE,
        index=False,
    )

    print(
        f"\nMonthly summary saved:\n"
        f"{MONTHLY_SUMMARY_FILE}"
    )


# ============================================================
# PLOT 1 — MONTHLY LISTING COUNT
# ============================================================

def plot_monthly_listing_count(monthly_summary):
    """Plot unique Airbnb listing counts by month."""

    print_section(
        "PLOT 1 - MONTHLY AIRBNB LISTING COUNT"
    )

    plt.figure(
        figsize=(11, 6)
    )

    plt.plot(
        monthly_summary["month_date"],
        monthly_summary["unique_listings"],
        marker="o",
    )

    plt.title(
        "Christchurch Airbnb Listings by Month"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Number of unique listings"
    )

    plt.xticks(
        monthly_summary["month_date"],
        monthly_summary["month_date"]
        .dt.strftime("%b %Y"),
        rotation=45,
        ha="right",
    )

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    save_plot(
        LISTING_COUNT_PLOT
    )


# ============================================================
# PLOT 2 — MONTHLY MEDIAN PRICE
# ============================================================

def plot_monthly_median_price(monthly_summary):
    """Plot median observed Airbnb nightly price by month."""

    print_section(
        "PLOT 2 - MONTHLY MEDIAN AIRBNB PRICE"
    )

    plot_df = monthly_summary.loc[
        monthly_summary["median_price"].notna()
    ].copy()

    if plot_df.empty:
        print(
            "No observed Airbnb prices available. "
            "Skipping median-price plot."
        )
        return

    plt.figure(
        figsize=(11, 6)
    )

    plt.plot(
        plot_df["month_date"],
        plot_df["median_price"],
        marker="o",
    )

    plt.title(
        "Median Airbnb Nightly Price by Month - Christchurch"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Median nightly price (NZD)"
    )

    plt.xticks(
        monthly_summary["month_date"],
        monthly_summary["month_date"]
        .dt.strftime("%b %Y"),
        rotation=45,
        ha="right",
    )

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    save_plot(
        MEDIAN_PRICE_PLOT
    )


# ============================================================
# PLOT 3 — MISSING PRICE PERCENTAGE
# ============================================================

def plot_monthly_missing_prices(monthly_summary):
    """Plot the percentage of missing Airbnb prices by month."""

    print_section(
        "PLOT 3 - MONTHLY MISSING PRICE PERCENTAGE"
    )

    plt.figure(
        figsize=(11, 6)
    )

    plt.bar(
        monthly_summary["month_date"],
        monthly_summary[
            "missing_price_percentage"
        ],
        width=20,
    )

    plt.title(
        "Missing Airbnb Prices by Month - Christchurch"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Missing prices (%)"
    )

    plt.xticks(
        monthly_summary["month_date"],
        monthly_summary["month_date"]
        .dt.strftime("%b %Y"),
        rotation=45,
        ha="right",
    )

    plt.ylim(
        bottom=0
    )

    plt.grid(
        axis="y",
        alpha=0.3,
    )

    save_plot(
        MISSING_PRICE_PLOT
    )


# ============================================================
# LOAD PRICE-GAP ANALYSIS
# ============================================================

def load_price_gap_data(file_path):
    """Load the SQLite-derived SA2 price-gap summary."""

    validate_input_file(file_path)

    gap_df = pd.read_csv(
        file_path,
        dtype={
            "location_id": "string",
        },
    )

    validate_required_columns(
        gap_df,
        GAP_REQUIRED_COLUMNS,
        "Price-gap dataset",
    )

    gap_df["median_nightly_gap"] = (
        pd.to_numeric(
            gap_df["median_nightly_gap"],
            errors="coerce",
        )
    )

    gap_df["unique_listings"] = (
        pd.to_numeric(
            gap_df["unique_listings"],
            errors="coerce",
        )
    )

    return gap_df


# ============================================================
# PLOT 4 — AIRBNB VS RENTAL PRICE GAP
# ============================================================

def plot_sa2_price_gap(gap_df):
    """
    Plot the SA2 areas with the largest median nightly
    Airbnb-versus-rental price gaps.
    """

    print_section(
        "PLOT 4 - AIRBNB VS RENTAL PRICE GAP"
    )

    plot_df = (
        gap_df
        .dropna(
            subset=[
                "location_name",
                "median_nightly_gap",
            ]
        )
        .nlargest(
            TOP_N_AREAS,
            "median_nightly_gap",
        )
        .sort_values(
            "median_nightly_gap",
            ascending=True,
        )
    )

    if plot_df.empty:
        print(
            "No price-gap results available. "
            "Skipping price-gap plot."
        )
        return

    plt.figure(
        figsize=(11, 7)
    )

    plt.barh(
        plot_df["location_name"],
        plot_df["median_nightly_gap"],
    )

    plt.title(
        "Top 10 Median Airbnb vs Rental Nightly Price Gaps"
    )

    plt.xlabel(
        "Median nightly price gap (NZD)"
    )

    plt.ylabel(
        "SA2 area"
    )

    plt.grid(
        axis="x",
        alpha=0.3,
    )

    save_plot(
        PRICE_GAP_PLOT
    )

    print(
        "\nTop SA2 price gaps:"
    )

    print(
        plot_df[
            [
                "location_id",
                "location_name",
                "unique_listings",
                "median_nightly_gap",
            ]
        ]
        .sort_values(
            "median_nightly_gap",
            ascending=False,
        )
        .to_string(
            index=False,
        )
    )


# ============================================================
# OUTPUT VALIDATION
# ============================================================

def validate_outputs():
    """Check that expected plot and summary files were created."""

    expected_files = [
        MONTHLY_SUMMARY_FILE,
        LISTING_COUNT_PLOT,
        MEDIAN_PRICE_PLOT,
        MISSING_PRICE_PLOT,
        PRICE_GAP_PLOT,
    ]

    missing_files = [
        file_path
        for file_path in expected_files
        if not file_path.exists()
    ]

    if missing_files:
        raise AssertionError(
            "Expected plot outputs were not created: "
            f"{missing_files}"
        )

    print_section(
        "OUTPUT VALIDATION"
    )

    for file_path in expected_files:
        print(
            f"PASS: {file_path}"
        )

    print(
        "\nPlot output validation: PASS"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """Generate all updated DATA422 analysis plots."""

    print("=" * 70)
    print(
        "DATA422 - UPDATED AIRBNB / RENTAL BOND PLOTS"
    )
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ----------------------------------------
    # Airbnb monthly analysis
    # ----------------------------------------

    airbnb_df = load_airbnb_data(
        AIRBNB_FILE
    )

    monthly_summary = (
        create_monthly_summary(
            airbnb_df
        )
    )

    save_monthly_summary(
        monthly_summary
    )

    plot_monthly_listing_count(
        monthly_summary
    )

    plot_monthly_median_price(
        monthly_summary
    )

    plot_monthly_missing_prices(
        monthly_summary
    )

    # ----------------------------------------
    # Airbnb vs rental-bond analysis
    # ----------------------------------------

    gap_df = load_price_gap_data(
        PRICE_GAP_FILE
    )

    plot_sa2_price_gap(
        gap_df
    )

    # ----------------------------------------
    # Validate generated outputs
    # ----------------------------------------

    validate_outputs()

    print(
        "\nUpdated plot generation completed successfully."
    )


if __name__ == "__main__":
    main()