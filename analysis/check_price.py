import pandas as pd
import numpy as np

df = pd.read_csv("output/christchurch_oct2025_jun2026.csv")

print("Total rows:", len(df))
print("Missing price:", df["price"].isna().sum())
print(
    "Missing price %:",
    round(df["price"].isna().mean() * 100, 2)
)

## Create the missing-price analysis

missing_month = (
    df.groupby("month_year")["price"]
      .agg(
          total="size",
          observed="count",
          missing=lambda x: x.isna().sum()
      )
)

missing_month["missing_pct"] = (
    missing_month["missing"] /
    missing_month["total"] * 100
).round(2)

print(missing_month)

## Analyse by room type and neighbourhood

missing_room = (
    df.groupby("room_type")["price"]
      .agg(
          total="size",
          observed="count",
          missing=lambda x: x.isna().sum()
      )
)

missing_room["missing_pct"] = (
    missing_room["missing"] /
    missing_room["total"] * 100
).round(2)

print(missing_room)


## neighbourhood result

missing_neighbourhood = (
    df.groupby("neighbourhood")["price"]
      .agg(
          total="size",
          observed="count",
          missing=lambda x: x.isna().sum()
      )
)

missing_neighbourhood["missing_pct"] = (
    missing_neighbourhood["missing"]
    / missing_neighbourhood["total"]
    * 100
).round(2)

print(
    missing_neighbourhood.sort_values(
        "missing_pct",
        ascending=False
    ).to_string()
)

## Run the neighbourhood analysis again excluding those three months:
months_with_prices = df[
    ~df["month_year"].isin([
        "12_2025",
        "01_2026",
        "02_2026"
    ])
].copy()

neighbourhood_check = (
    months_with_prices
    .groupby("neighbourhood")["price"]
    .agg(
        total="size",
        observed="count",
        missing=lambda x: x.isna().sum()
    )
)

neighbourhood_check["missing_pct"] = (
    neighbourhood_check["missing"]
    / neighbourhood_check["total"]
    * 100
).round(2)

print(
    neighbourhood_check
    .sort_values("missing_pct", ascending=False)
    .to_string()
)

## the same analysis for room type excluding Dec–Feb

months_with_prices = df[
    ~df["month_year"].isin([
        "12_2025",
        "01_2026",
        "02_2026"
    ])
].copy()

room_check = (
    months_with_prices
    .groupby("room_type")["price"]
    .agg(
        total="size",
        observed="count",
        missing=lambda x: x.isna().sum()
    )
)

room_check["missing_pct"] = (
    room_check["missing"]
    / room_check["total"]
    * 100
).round(2)

print(room_check)

## Run the same-listing history test:

missing_months = [
    "12_2025",
    "01_2026",
    "02_2026"
]

# Records from the three completely missing-price months
missing_period = df[
    df["month_year"].isin(missing_months)
].copy()

# Records from months where price information exists
other_period = df[
    ~df["month_year"].isin(missing_months)
].copy()

# Price history for each listing in the other months
listing_history = (
    other_period
    .groupby("id")["price"]
    .agg(
        known_price_count="count",
        median_known_price="median",
        mean_known_price="mean",
        min_known_price="min",
        max_known_price="max"
    )
)

# Match Dec-Feb listings to their historical prices
missing_check = missing_period.merge(
    listing_history,
    left_on="id",
    right_index=True,
    how="left"
)

total = len(missing_check)

has_history = (
    missing_check["known_price_count"]
    .fillna(0)
    .gt(0)
    .sum()
)

no_history = total - has_history

print("=== SAME-LISTING PRICE HISTORY ===")

print("Dec-Feb missing observations:", total)

print(
    "Have observed price in another month:",
    has_history
)

print(
    "No observed price elsewhere:",
    no_history
)

print(
    "Percentage with price history:",
    round(has_history / total * 100, 2),
    "%"
)

print("\n=== UNIQUE LISTINGS ===")

print(
    "Unique listings in Dec-Feb:",
    missing_period["id"].nunique()
)

listings_with_history = (
    missing_check.loc[
        missing_check["known_price_count"]
        .fillna(0)
        .gt(0),
        "id"
    ]
    .nunique()
)

print(
    "Unique listings with known price elsewhere:",
    listings_with_history
)

## Step 1 — Create a validation function

VALID_MONTHS = [
    "10_2025",
    "11_2025",
    "03_2026",
    "04_2026",
    "05_2026",
    "06_2026"
]

from sklearn.metrics import mean_absolute_error
import numpy as np
import pandas as pd

def test_same_listing_method(df, test_month):

    # Actual known prices for the month being tested
    test = df[
        (df["month_year"] == test_month) &
        (df["price"].notna())
    ][["id", "price"]].copy()

    test = test.rename(
        columns={"price": "actual_price"}
    )

    # Historical prices from OTHER months
    history = df[
        (df["month_year"] != test_month) &
        (df["price"].notna())
    ].copy()

    # Median known price for each exact listing
    listing_estimates = (
        history.groupby("id")["price"]
        .median()
        .rename("estimated_price")
    )

    comparison = test.merge(
        listing_estimates,
        left_on="id",
        right_index=True,
        how="left"
    )

    # Only evaluate where same-listing history exists
    comparison = comparison.dropna(
        subset=["estimated_price"]
    )

    comparison["absolute_error"] = abs(
        comparison["actual_price"] -
        comparison["estimated_price"]
    )

    mae = mean_absolute_error(
        comparison["actual_price"],
        comparison["estimated_price"]
    )

    rmse = np.sqrt(
        np.mean(
            (
                comparison["actual_price"] -
                comparison["estimated_price"]
            ) ** 2
        )
    )

    return {
        "month": test_month,
        "tested": len(test),
        "matched": len(comparison),
        "coverage_pct": round(
            len(comparison) / len(test) * 100, 2
        ),
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2)
    }

results = []

for month in VALID_MONTHS:
    results.append(
        test_same_listing_method(df, month)
    )

results_df = pd.DataFrame(results)

print(results_df.to_string(index=False))

## Investigate May before doing KNN

test_month = "05_2026"

test = df[
    (df["month_year"] == test_month) &
    (df["price"].notna())
][["id", "name", "neighbourhood",
   "room_type", "price"]].copy()

test = test.rename(
    columns={"price": "actual_price"}
)

history = df[
    (df["month_year"] != test_month) &
    (df["price"].notna())
]

listing_estimates = (
    history.groupby("id")["price"]
    .median()
    .rename("estimated_price")
)

comparison = test.merge(
    listing_estimates,
    left_on="id",
    right_index=True,
    how="left"
)

comparison = comparison.dropna(
    subset=["estimated_price"]
)

comparison["absolute_error"] = abs(
    comparison["actual_price"] -
    comparison["estimated_price"]
)

print(
    comparison
    .sort_values(
        "absolute_error",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)

## inspect that listing across all months:

listing_id = 1291425420035701207

print(
    df[df["id"] == listing_id][
        [
            "id",
            "name",
            "month_year",
            "price",
            "room_type",
            "neighbourhood",
            "minimum_nights",
            "availability_365"
        ]
    ].sort_values("month_year").to_string(index=False)
)

## Check June as well for the same property

print(
    df[
        df["id"] == 1291425420035701207
    ][["month_year", "price"]]
    .sort_values("month_year")
)

## comparing each observed price against that listing's median price:

known = df[df["price"].notna()].copy()

listing_median = (
    known.groupby("id")["price"]
    .median()
    .rename("listing_median")
)

known = known.merge(
    listing_median,
    left_on="id",
    right_index=True
)

known["price_ratio"] = (
    known["price"] /
    known["listing_median"]
)

potential_outliers = known[
    (known["price_ratio"] >= 5) |
    (known["price_ratio"] <= 0.2)
].copy()

print(
    potential_outliers[
        [
            "id",
            "name",
            "month_year",
            "price",
            "listing_median",
            "price_ratio",
            "neighbourhood"
        ]
    ]
    .sort_values("price_ratio", ascending=False)
    .to_string(index=False)
)

## monthly price-statistics table from the previous step:

known_prices = df[df["price"].notna()].copy()

monthly_stats = (
    known_prices
    .groupby("month_year")["price"]
    .agg(
        count="count",
        median="median",
        mean="mean",
        min="min",
        max="max"
    )
)

monthly_stats["q25"] = (
    known_prices.groupby("month_year")["price"]
    .quantile(0.25)
)

monthly_stats["q75"] = (
    known_prices.groupby("month_year")["price"]
    .quantile(0.75)
)

print(
    monthly_stats[
        ["count", "median", "mean",
         "q25", "q75", "min", "max"]
    ].round(2)
)

## KNN validation code

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import (
    StandardScaler,
    OneHotEncoder
)
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    median_absolute_error,
    mean_squared_error
)

import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "latitude",
    "longitude",
    "minimum_nights",
    "availability_365"
]

CATEGORICAL_FEATURES = [
    "room_type",
    "neighbourhood"
]

VALID_MONTHS = [
    "10_2025",
    "11_2025",
    "03_2026",
    "04_2026",
    "05_2026",
    "06_2026"
]

def test_knn_month(df, test_month, k=5):

    # Training = known prices from OTHER months
    train = df[
        (df["month_year"] != test_month) &
        (df["price"].notna())
    ].copy()

    # Test = known prices from target month
    test = df[
        (df["month_year"] == test_month) &
        (df["price"].notna())
    ].copy()

    features = (
        NUMERIC_FEATURES +
        CATEGORICAL_FEATURES
    )

    X_train = train[features]
    y_train = train["price"]

    X_test = test[features]
    y_test = test["price"]

    numeric_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median")
            ),
            (
                "scaler",
                StandardScaler()
            )
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                )
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                numeric_transformer,
                NUMERIC_FEATURES
            ),
            (
                "cat",
                categorical_transformer,
                CATEGORICAL_FEATURES
            )
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "knn",
                KNeighborsRegressor(
                    n_neighbors=k,
                    weights="distance"
                )
            )
        ]
    )

    model.fit(X_train, y_train)

    predicted = model.predict(X_test)

    absolute_errors = np.abs(
        y_test.values - predicted
    )

    mae = mean_absolute_error(
        y_test,
        predicted
    )

    medae = median_absolute_error(
        y_test,
        predicted
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predicted
        )
    )

    return {
        "month": test_month,
        "tested": len(test),

        "MAE": round(mae, 2),
        "Median_AE": round(medae, 2),
        "RMSE": round(rmse, 2),

        "within_25_pct": round(
            (absolute_errors <= 25).mean()
            * 100,
            2
        ),

        "within_50_pct": round(
            (absolute_errors <= 50).mean()
            * 100,
            2
        ),

        "within_100_pct": round(
            (absolute_errors <= 100).mean()
            * 100,
            2
        )
    }

knn_results = []

for month in VALID_MONTHS:

    print(
        f"Testing KNN for {month}..."
    )

    result = test_knn_month(
        df,
        month,
        k=5
    )

    knn_results.append(result)

knn_results_df = pd.DataFrame(
    knn_results
)

print("\n=== KNN VALIDATION ===")

print(
    knn_results_df.to_string(
        index=False
    )
)