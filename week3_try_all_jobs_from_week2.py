from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


file_path = Path("data/listings_19_06_2026.csv")

df = pd.read_csv(file_path)

print("June 2026 New Zealand dataset loaded.")
print(f"Rows: {df.shape[0]:,}")
print(f"Columns: {df.shape[1]}")

chch_df = df[
    df["neighbourhood_group"] == "Christchurch City"
].copy()

print(f"All New Zealand listings: {len(df):,}")
print(f"Christchurch listings: {len(chch_df):,}")

# Histogram — all New Zealand prices

nz_price = df["price"].dropna()

plt.figure(figsize=(10, 6))

plt.hist(
    nz_price,
    bins=50
)

plt.title("Distribution of Airbnb Prices - New Zealand")

# However, because Airbnb contains very large price outliers, this may look compressed.
# A more readable version matching what you did previously is:
plt.xlabel("Price per night (NZD)")
plt.ylabel("Number of listings")

plt.xlim(left=0)

plt.tight_layout()
plt.show()

nz_price_plot = df[
    (df["price"].notna()) &
    (df["price"] <= 2000)
]

plt.figure(figsize=(10, 6))

plt.hist(
    nz_price_plot["price"],
    bins=50
)

plt.title("Distribution of Airbnb Prices - New Zealand")
plt.xlabel("Price per night (NZD)")
plt.ylabel("Number of listings")

plt.xlim(0, 2000)

plt.tight_layout()
# plt.show()

# However, because Airbnb contains very large price outliers, this may look compressed.
# A more readable version matching what you did previously is:

chch_price_plot = chch_df[
    (chch_df["price"].notna()) &
    (chch_df["price"] <= 2000)
]

plt.figure(figsize=(10, 6))

plt.hist(
    chch_price_plot["price"],
    bins=50
)

plt.title("Distribution of Airbnb Prices - Christchurch City")
plt.xlabel("Price per night (NZD)")
plt.ylabel("Number of listings")

plt.xlim(0, 2000)

plt.tight_layout()
plt.show()

# Bonus — NZ and Christchurch in the same plot

plt.figure(figsize=(10, 6))

plt.hist(
    nz_price_plot["price"],
    bins=50,
    alpha=0.5,
    label="New Zealand"
)

plt.hist(
    chch_price_plot["price"],
    bins=50,
    alpha=0.5,
    label="Christchurch City"
)

plt.title("Airbnb Price Distribution: New Zealand vs Christchurch")
plt.xlabel("Price per night (NZD)")
plt.ylabel("Number of listings")

plt.xlim(0, 2000)

plt.legend()

plt.tight_layout()
plt.show()

# Calculate days since the last review

filename = file_path.stem

# listings_19_06_2026
parts = filename.split("_")

day = parts[-3]
month = parts[-2]
year = parts[-1]

snapshot_date = pd.to_datetime(
    f"{year}-{month}-{day}"
)

print("Dataset snapshot date:", snapshot_date)

# Convert last_review to a date:

df["last_review"] = pd.to_datetime(
    df["last_review"],
    errors="coerce"
)

# Then calculate:

df["days_since_last_review"] = (
    snapshot_date - df["last_review"]
).dt.days

# Check:

print(
    df[
        [
            "last_review",
            "days_since_last_review"
        ]
    ].head(20)
)

# Plot days since last review
# Calculate how long ago the last review was in days. Plot the distribution of this new feature.

review_days = df[
    "days_since_last_review"
].dropna()

plt.figure(figsize=(10, 6))

plt.hist(
    review_days,
    bins=50
)

plt.title("Distribution of Days Since Last Airbnb Review - New Zealand")
plt.xlabel("Days since last review")
plt.ylabel("Number of listings")

plt.tight_layout()

plt.xlim(left=0)
plt.show()

# Find the top 10% by number of reviews
# The relevant column is: number_of_reviews
# Calculate the 90th percentile:

review_threshold = df[
    "number_of_reviews"
].quantile(0.90)

print(
    "90th percentile number of reviews:",
    review_threshold
)

# Now select listings at or above that threshold:

top_10_reviews = df[
    df["number_of_reviews"] >= review_threshold
].copy()

print(
    f"Listings in top 10%: "
    f"{len(top_10_reviews):,}"
)

# How many top-10% properties are in Christchurch?

top_10_chch = top_10_reviews[
    top_10_reviews["neighbourhood_group"]
    == "Christchurch City"
]

print(
    f"Top 10% listings in New Zealand: "
    f"{len(top_10_reviews):,}"
)

print(
    f"Top 10% listings in Christchurch: "
    f"{len(top_10_chch):,}"
)

# I can also calculate the percentage:

percentage_chch = (
    len(top_10_chch) /
    len(top_10_reviews) *
    100
)

print(
    f"Percentage of top-review listings "
    f"in Christchurch: {percentage_chch:.2f}%"
)

# Show the actual highest-reviewed properties
# This is useful during the presentation:

highest_reviewed = top_10_reviews[
    [
        "id",
        "name",
        "neighbourhood_group",
        "neighbourhood",
        "room_type",
        "price",
        "number_of_reviews"
    ]
].sort_values(
    "number_of_reviews",
    ascending=False
)

print("\nHighest reviewed properties:")
print(
    highest_reviewed.head(20).to_string(index=False)
)

# We can specifically show Christchurch:

print("\nHighest reviewed Christchurch properties:")

print(
    top_10_chch[
        [
            "name",
            "neighbourhood",
            "price",
            "number_of_reviews"
        ]
    ]
    .sort_values(
        "number_of_reviews",
        ascending=False
    )
    .head(10)
    .to_string(index=False)
)