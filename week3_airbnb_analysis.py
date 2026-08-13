from pathlib import Path

import pandas as pd

file_path = Path("data/listings_19_06_2026.csv")

# Show all columns
# pd.set_option("display.max_columns", None)

# Show full column width (optional)
# pd.set_option("display.width", None)

#print("Starting DATA422 Week 3 analysis...")
#print(f"Looking for file: {file_path.resolve()}")

if not file_path.exists():
    raise FileNotFoundError(
        f"Dataset not found: {file_path.resolve()}\n"
        "Check the filename and confirm it is inside the data folder."
    )

df = pd.read_csv(file_path)

# print("\nDataset loaded successfully.")
# print(f"Rows: {df.shape[0]:,}")
# print(f"Columns: {df.shape[1]}")


# print("\nFirst five rows:")
# print(df[["id", "name", "host_id", "number_of_reviews_ltm", "neighbourhood_group"]].head())
## print(df.head().to_string())

# print("\nColumn names:")
# print(df.columns.tolist())

# Check the unique values
# print(df["neighbourhood_group"].unique())
chch_df = df[df["neighbourhood_group"] == "Christchurch City"]
##print("Original dataset shape:", df.shape)
##print("Christchurch dataset shape:", chch_df.shape)
##print(chch_df.head())

## From this point onward, use chch_df for all remaining tasks:
## Add the month_year column
## Concatenate all monthly Christchurch datasets
## Produce summary statistics
## Save the combined CSV
## Create plots

# Add month/year
chch_df["month_year"] = "06-2026"

# print("\nFirst five rows with new column month + year:")

# print(chch_df[["id", "name", "host_id", "number_of_reviews_ltm", "neighbourhood_group", "month_year"]].head())
# print(chch_df.head())

# print("\nColumn names:")
# print(chch_df.columns.tolist())

# Summary statistics
##print(chch_df.describe())

# Missing values
##print(chch_df.isnull().sum())

# print(df["neighbourhood_group"].unique())

# Add a column for the month + year

# check the path of data folder
data_folder = Path("data")

# Find all CSV files
csv_files = sorted(data_folder.glob("*.csv"))

all_chch_data = []

# print(f"Found {len(csv_files)} files\n")

for file in csv_files:

    # print(f"Processing: {file.name}")

    # 1. Load dataset
    df = pd.read_csv(file)

    # 2. Filter Christchurch only
    chch_df = df[
        df["neighbourhood_group"] == "Christchurch City"
    ].copy()

    # 3. Get month and year from filename
    # listings_19_06_2026.csv
    filename = file.stem
    parts = filename.split("_")

    month = parts[-2]
    year = parts[-1]

    # 4. Create month_year, e.g. 06_2026
    month_year = f"{month}_{year}"

    # 5. Add new column
    chch_df["month_year"] = month_year

    # print(f"Month/year: {month_year}")
    # print(f"Christchurch rows: {len(chch_df):,}")

    # Keep prepared data
    all_chch_data.append(chch_df)

    # print("-" * 50)


# 6. Concatenate all monthly datasets
combined_df = pd.concat(
    all_chch_data,
    ignore_index=True
)

# print("\nCombined Christchurch dataset created successfully!")

# print(f"Rows: {combined_df.shape[0]:,}")
# print(f"Columns: {combined_df.shape[1]}")


combined_df["_sort_date"] = pd.to_datetime(
    combined_df["month_year"],
    format="%m_%Y"
)

combined_df = combined_df.sort_values("_sort_date")

combined_df = combined_df.drop(columns="_sort_date")

combined_df = combined_df.reset_index(drop=True)

# print("\nFirst five rows:")

# print(chch_df[["id", "name", "host_id", "number_of_reviews_ltm", "neighbourhood_group", "month_year"]].head())
# print(combined_df[["id", "name", "host_id", "number_of_reviews_ltm", "neighbourhood_group", "month_year"]].head())

# After verification that all nine months exist, For a chronological verification, use :

month_counts = (
    combined_df
    .groupby("month_year")
    .size()
    .reset_index(name="number_of_listings")
)

month_counts["_date"] = pd.to_datetime(
    month_counts["month_year"],
    format="%m_%Y"
)

month_counts = month_counts.sort_values("_date")

# print(
    # month_counts[
        # ["month_year", "number_of_listings"]
    # ].to_string(index=False)
# )

# Finally, as per the next step all data should be to store the concatenated dataset in a new file:

# output_folder = Path("output")
# output_folder.mkdir(exist_ok=True)

# output_file = output_folder / "christchurch_oct2025_jun2026.csv"

# combined_df.to_csv(
    # output_file,
    # index=False
#)

# I loop through all nine monthly datasets and apply exactly the same preparation process to each one.
# I filter each dataset to Christchurch City, derive the month and year from its filename, add this as a new month_year column, and collect each prepared DataFrame.
# I then concatenate them using pandas to create one Christchurch dataset spanning October 2025 to June 2026.

# Deliverable 5
# print(f"\nSaved combined dataset to: {output_file}")

# Deliverable 4
# Produce suitable summary statistics for all columns (categories + counts or min + max + mean + std) and number of missing values (per column) etc.
# 
# For this deliverable, you need to produce:
# Summary statistics for numeric columns (min, max, mean, std, etc.)
# Summary statistics for categorical columns (counts/frequencies)
# Number of missing values for each column
# Assuming your final combined dataset is combined_df, here's a complete solution.

# Dataset overview
print("=" * 60)
print("Dataset Overview")
print("=" * 60)

print(f"Rows    : {combined_df.shape[0]:,}")
print(f"Columns : {combined_df.shape[1]}")

# Numerical summary statistics

print("\n" + "=" * 60)
print("Numerical Summary Statistics")
print("=" * 60)

print(combined_df.describe().T)

# Categorical summary statistics

print("\n" + "=" * 60)
print("Categorical Summary Statistics")
print("=" * 60)

categorical_columns = combined_df.select_dtypes(
    include=["object", "string"]
).columns

print(combined_df[categorical_columns].describe().T)

# Value counts for each categorical column