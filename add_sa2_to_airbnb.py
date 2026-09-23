import os
import csv
import time
import random
import requests
import pandas as pd

from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "output/processed/christchurch_airbnb_clean.xlsx"

OUTPUT_FILE = "output/processed/christchurch_airbnb_clean_with_sa2.xlsx"
CHECKPOINT_FILE = "output/processed/koordinates_sa2_checkpoint.csv"
FAILED_FILE = "output/processed/koordinates_failed_queries.csv"

LAYER_ID = "123515"

API_KEY = os.getenv("KOORDINATES_API_KEY")

API_URL = "https://api.koordinates.com/api/vectorQuery.json"

# Start conservatively so we don't overload the API.
MAX_WORKERS = 5

# Retry temporary/network failures
MAX_RETRIES = 3

FIELDS = [
    "row_number", "location_id", "location_name",
    "status", "error"
]

# Save checkpoint after this many completed queries
CHECKPOINT_EVERY = 100


# ============================================================
# VALIDATE API KEY
# ============================================================

if not API_KEY:
    raise ValueError(
        "KOORDINATES_API_KEY is not set.\n"
        "Set it before running this script."
    )


# ============================================================
# QUERY ONE COORDINATE
# ============================================================

def query_row(row):
    """Query Koordinates for one Airbnb observation."""

    row_number, latitude, longitude = row

    result = {
        "row_number": row_number,
        "location_id": "",
        "location_name": "",
        "status": "FAILED",
        "error": ""
    }

    if pd.isna(latitude) or pd.isna(longitude):
        result["status"] = "NO_COORDINATES"
        return result

    params = {
        "key": API_KEY,
        "layer": LAYER_ID,
        "x": longitude,
        "y": latitude
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=30
            )

            # Stop rather than repeatedly retrying invalid
            # credentials or an incorrect layer.
            if response.status_code in (400, 401, 403):
                response.raise_for_status()

            # Retry rate limits and temporary server errors.
            if response.status_code == 429 or (
                500 <= response.status_code < 600
            ):
                if attempt < MAX_RETRIES - 1:
                    retry_after = response.headers.get(
                        "Retry-After", ""
                    )
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        delay = 2 ** attempt + random.random()

                    time.sleep(max(0, delay))
                    continue

            response.raise_for_status()
            data = response.json()

            features = (
                data["vectorQuery"]["layers"]
                [LAYER_ID]["features"]
            )

            if not features:
                result["status"] = "NO_MATCH"
                return result

            properties = features[0]["properties"]

            result["location_id"] = properties.get(
                "SA22026_V1_00", ""
            )
            result["location_name"] = properties.get(
                "SA22026_V1_00_NAME", ""
            )
            result["status"] = (
                "SUCCESS" if result["location_id"]
                else "NO_MATCH"
            )
            return result

        except requests.RequestException as exc:
            result["error"] = str(exc)

            if getattr(exc.response, "status_code", None) in (
                400, 401, 403
            ):
                raise RuntimeError(
                    "Check your API key, layer ID and "
                    "request parameters."
                ) from exc

            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt + random.random())

        except (KeyError, ValueError, TypeError) as exc:
            result["error"] = str(exc)
            break

    return result


def main():
    df = pd.read_excel(INPUT_FILE)

    required = {"id", "latitude", "longitude"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Each original row receives its own identifier.
    df["row_number"] = range(len(df))

    print(f"Total rows: {len(df):,}")

    # Load results from previous runs.
    # Load existing checkpoint only if it contains data.
    if (
        os.path.exists(CHECKPOINT_FILE)
        and os.path.getsize(CHECKPOINT_FILE) > 0
    ):
        try:
            checkpoint = pd.read_csv(
                CHECKPOINT_FILE,
                dtype={"location_id": "string"}
            )

            completed = set(
                checkpoint.loc[
                    checkpoint["status"].isin(
                        ["SUCCESS", "NO_MATCH", "NO_COORDINATES"]
                    ),
                    "row_number"
                ].astype(int)
            )

            print(f"Already completed: {len(completed):,}")

        except pd.errors.EmptyDataError:
            completed = set()
            print("Checkpoint is empty. Starting fresh.")

    else:
        completed = set()
        print("No previous results. Starting fresh.")

    remaining = df.loc[
        ~df["row_number"].isin(completed),
        ["row_number", "latitude", "longitude"]
    ]

    print(f"Remaining queries: {len(remaining):,}")

    # Append results as they arrive, so an interrupted
    # run retains its progress.
    checkpoint_exists = (
        os.path.exists(CHECKPOINT_FILE)
        and os.path.getsize(CHECKPOINT_FILE) > 0
    )

    with open(
        CHECKPOINT_FILE, "a",
        newline="", encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(file, fieldnames=FIELDS)

        if not checkpoint_exists or os.path.getsize(
            CHECKPOINT_FILE
        ) == 0:
            writer.writeheader()

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            futures = [
                executor.submit(query_row, row)
                for row in remaining.itertuples(
                    index=False, name=None
                )
            ]

            for count, future in enumerate(
                as_completed(futures), start=1
            ):
                result = future.result()

                writer.writerow(result)
                file.flush()

                if count % 100 == 0:
                    print(
                        f"Processed: {count:,} / "
                        f"{len(remaining):,}"
                    )

    # Read all saved results, including previous runs.
    lookup = pd.read_csv(
        CHECKPOINT_FILE,
        dtype={"location_id": "string"}
    )

    # Retain the most recent successful result for each
    # row, while allowing failed queries to be retried.
    lookup["priority"] = (
        lookup["status"] == "SUCCESS"
    ).astype(int)

    lookup = (
        lookup.sort_values("priority")
        .drop_duplicates("row_number", keep="last")
    )

    failed = lookup[lookup["status"] == "FAILED"]
    failed.to_csv(FAILED_FILE, index=False)

    # Join the results by original row number.
    final = df.merge(
        lookup[
            ["row_number", "location_id", "location_name"]
        ],
        on="row_number",
        how="left",
        validate="one_to_one"
    )

    final = final.drop(columns=["row_number"])

    # Verify that every original observation remains.
    assert len(final) == len(df)

    # Verify the known test listing.
    test = final[final["id"] == 40183765]
    print("\nTest listing:")
    print(
        test[
            ["id", "location_id", "location_name"]
        ].drop_duplicates().to_string(index=False)
    )

    print("\nQuery summary:")
    print(lookup["status"].value_counts())

    print(
        "\nRows with SA2:",
        final["location_id"].notna().sum()
    )

    final.to_excel(OUTPUT_FILE, index=False)
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()