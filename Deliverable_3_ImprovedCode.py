print(__file__)
"""
DATA422 Airbnb Christchurch Analysis

Purpose:
- Import Airbnb listings datasets
- Filter Christchurch City listings
- Add month/year information
- Merge all monthly datasets
- Generate summary statistics
- Produce visualisations
- Analyse review activity

Author: Carolina Faka'osi
"""
print("RUNNING UPDATED SCRIPT")

# ==================================================
# IMPORTS
# ==================================================

import pandas as pd
import matplotlib.pyplot as plt

# ==================================================
# PARAMETERS
# ==================================================

CHRISTCHURCH_NAME = "Christchurch City"

TOP_REVIEW_PERCENTILE = 0.90

PRICE_BINS = 400
MAX_PRICE = 4500

FILES = [
    ("listings_19062026.csv", "listings_19_06_2026.csv", "06-2026"),
    ("listings_23052026.csv", "listings_23_05_2026.csv", "05-2026"),
    ("listings_16042026.csv", "listings_16_04_2026.csv", "04-2026"),
    ("listings_17032026.csv", "listings_17_03_2026.csv", "03-2026"),
    ("listings_13022026.csv", "listings_13_02_2026.csv", "02-2026"),
    ("listings_16012026.csv", "listings_16_01_2026.csv", "01-2026"),
    ("listings_11122025.csv", "listings_11_12_2025.csv", "12-2025"),
    ("listings_07112025.csv", "listings_07_11_2025.csv", "11-2025"),
    ("listings_05102025.csv", "listings_05_10_2025.csv", "10-2025")
]

# ==================================================
# FUNCTION TO PROCESS FILES
# ==================================================

def process_listing_file(input_file, output_file, month_year):
    """
    Read Airbnb listing data,
    filter Christchurch City records,
    add month_year field,
    save filtered file.
    """

    print(f"\nProcessing {input_file}")

    df = pd.read_csv(input_file)

    print(df.head())

    print("\nColumns:")
    print(df.columns)

    print("\nNeighbourhood Groups:")
    print(df["neighbourhood_group"].unique())

    df = df[
        df["neighbourhood_group"] == CHRISTCHURCH_NAME
    ].copy()

    assert len(df) > 0, (
        f"No Christchurch records found in {input_file}"
    )

    df["month_year"] = month_year

    df.to_csv(
        output_file,
        index=False
    )

    print(
        f"New column 'month_year' added successfully!"
    )

    return df

# ==================================================
# IMPORT AND FILTER FILES
# ==================================================

print("\n=== DATA IMPORTS AND FILTERING FOR CHRISTCHURCH ===")

for input_file, output_file, month_year in FILES:

    process_listing_file(
        input_file,
        output_file,
        month_year
    )

# ==================================================
# CONCATENATION PROCESS
# ==================================================

print("\n=== CONCATENATION PROCESS FOR CHRISTCHURCH ===")

listings_files = [
    "listings_19_06_2026.csv",
    "listings_23_05_2026.csv",
    "listings_16_04_2026.csv",
    "listings_17_03_2026.csv",
    "listings_13_02_2026.csv",
    "listings_16_01_2026.csv",
    "listings_11_12_2025.csv",
    "listings_07_11_2025.csv",
    "listings_05_10_2025.csv"
]

all_dfs = []

for filename in listings_files:

    print("filename:", filename)

    date_part = (
        filename
        .replace("listings_", "")
        .replace(".csv", "")
    )

    publish_date = pd.to_datetime(
        date_part,
        format="%d_%m_%Y"
    )

    month_year = publish_date.strftime("%m_%Y")

    temp_df = pd.read_csv(filename)

    temp_df["month_year"] = month_year
    temp_df["publish_date"] = publish_date

    all_dfs.append(temp_df)

df = pd.concat(
    all_dfs,
    ignore_index=True
)

# ==================================================
# SANITY CHECKS
# ==================================================

assert len(df) > 0, (
    "Merged dataframe is empty."
)

assert (
    df["neighbourhood_group"]
    == CHRISTCHURCH_NAME
).all(), (
    "Non-Christchurch records found."
)

assert "price" in df.columns

assert "number_of_reviews" in df.columns

print("\nConcatenation complete.")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

# ==================================================
# SAVE MERGED DATASET
# ==================================================

OUTPUT_FILE = (
    "Christchurch_merged_listings_2025_2026.csv"
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    f"\nMerged dataset saved as {OUTPUT_FILE}"
)

print(df.head())
print(df.shape)

print(
    "Christchurch listings (2025-2026) merged and saved successfully!"
)

# ==================================================
# SUMMARY STATISTICS
# ==================================================

print("\n=== NUMERICAL SUMMARY STATISTICS ===")

print(
    df.describe()
      .T
      .to_string()
)

print("\n=== CATEGORICAL SUMMARY STATISTICS ===")

print(
    df.describe(include="object")
      .T
      .to_string()
)

print("\n=== MISSING VALUES SUMMARY ===")

missing_summary = (
    df.isnull()
      .sum()
      .to_frame(
          name="missing_values"
      )
)

print(
    missing_summary.to_string()
)

# ==================================================
# SAVE SUMMARY STATISTICS
# ==================================================

with open(
    "summary_statistics.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "=== NUMERICAL SUMMARY STATISTICS ===\n"
    )

    f.write(
        df.describe()
          .T
          .to_string()
    )

    f.write(
        "\n\n=== CATEGORICAL SUMMARY STATISTICS ===\n"
    )

    f.write(
        df.describe(include="object")
          .T
          .to_string()
    )

    f.write(
        "\n\n=== MISSING VALUES SUMMARY ===\n"
    )

    f.write(
        missing_summary.to_string()
    )

print(
    "\nSummary statistics saved successfully."
)

# ==================================================
# DATA CLEANING
# ==================================================

df_cleaned = df.dropna(
    subset=["price"]
)

print(
    "\nPrice datatype:"
)

print(
    df_cleaned["price"].dtype
)

# ==================================================
# HISTOGRAM
# ==================================================

plt.figure(figsize=(10, 6))

plt.hist(
    df_cleaned["price"],
    bins=PRICE_BINS,
    edgecolor="black",
    color="skyblue"
)

plt.xlim(
    0,
    MAX_PRICE
)

plt.title(
    "Price Distribution of Airbnb Listings in Christchurch City"
)

plt.xlabel(
    "Price (NZD)"
)

plt.ylabel(
    "Number of Listings"
)

plt.show()

plt.close()

# ==================================================
# REVIEW ANALYSIS
# ==================================================

df["last_review"] = pd.to_datetime(
    df["last_review"],
    format="%Y-%m-%d"
)

print(
    "\n=== DIFFERENCE BETWEEN SCRAPE DATE AND LAST REVIEW DATE ==="
)

df["days_since_review"] = (
    df["publish_date"]
    - df["last_review"]
).dt.days

print(
    df[
        [
            "last_review",
            "publish_date",
            "days_since_review"
        ]
    ]
)

# ==================================================
# NUMBER OF LISTINGS BY PUBLISH DATE
# ==================================================

print(
    "\n=== NUMBER OF LISTINGS BY PUBLISH DATE ==="
)

print(
    df["publish_date"]
      .value_counts()
)

# ==================================================
# TOP 10% MOST REVIEWED PROPERTIES
# ==================================================

print(
    "\n=== TOP 10% MOST REVIEWED PROPERTIES IN CHRISTCHURCH ==="
)

threshold = (
    df_cleaned["number_of_reviews"]
    .quantile(
        TOP_REVIEW_PERCENTILE
    )
)

top_10 = df_cleaned[
    df_cleaned["number_of_reviews"]
    >= threshold
]

print(
    f"Number of properties in the top 10%: {threshold} properties"
)

print(top_10)

print(
    "\nChristchurch analysis completed successfully!"
)