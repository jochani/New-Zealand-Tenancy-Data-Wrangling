"""
Add SA2 geographic information to cleaned Christchurch Airbnb data.

DATA422 - New Zealand Tenancy Data Wrangling

Purpose
-------
Assign each Christchurch Airbnb observation to a Statistical Area 2
(SA2 2026) using latitude and longitude and the Koordinates Vector Query
API.

Input
-----
output/processed/christchurch_airbnb_clean.xlsx

Outputs
-------
output/processed/christchurch_airbnb_clean_with_sa2.xlsx
output/processed/koordinates_sa2_checkpoint.csv
output/processed/koordinates_failed_queries.csv

Design principles
-----------------
- Use relative project paths.
- Preserve the original input dataset.
- Keep configuration values visible.
- Separate processing into small, focused functions.
- Validate inputs before processing.
- Record failed API queries rather than silently discarding them.
- Preserve progress using a checkpoint file.
- Use sanity checks to validate the processed output.
"""

import csv
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path(
    "output/processed/christchurch_airbnb_clean.xlsx"
)

OUTPUT_FILE = Path(
    "output/processed/christchurch_airbnb_clean_with_sa2.xlsx"
)

CHECKPOINT_FILE = Path(
    "output/checkpoints/koordinates_sa2_checkpoint.csv"
)

FAILED_FILE = Path(
    "output/logs/koordinates_failed_queries.csv"
)

API_URL = "https://api.koordinates.com/api/vectorQuery.json"
LAYER_ID = "123515"

SA2_ID_FIELD = "SA22026_V1_00"
SA2_NAME_FIELD = "SA22026_V1_00_NAME"

API_KEY_ENV_VAR = "KOORDINATES_API_KEY"

MAX_WORKERS = 5
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30
PROGRESS_EVERY = 100

RETRYABLE_STATUS_CODES = {429}
FATAL_STATUS_CODES = {400, 401, 403}

COMPLETED_STATUSES = {
    "SUCCESS",
    "NO_MATCH",
    "NO_COORDINATES",
}

REQUIRED_COLUMNS = {
    "id",
    "latitude",
    "longitude",
}

CHECKPOINT_FIELDS = [
    "row_number",
    "location_id",
    "location_name",
    "status",
    "error",
]

# Known observation used as a geographic sanity check.
KNOWN_TEST_LISTING_ID = 40183765
EXPECTED_TEST_SA2_ID = "316700"
EXPECTED_TEST_SA2_NAME = "Christchurch Airport"


# ============================================================
# VALIDATION
# ============================================================

def get_api_key():
    """Return the Koordinates API key from the environment."""

    api_key = os.getenv(API_KEY_ENV_VAR)

    if not api_key:
        raise EnvironmentError(
            f"{API_KEY_ENV_VAR} is not set. "
            "Set the environment variable before running the script."
        )

    return api_key


def validate_input_file(file_path):
    """Check that the required input file exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path.resolve()}"
        )


def validate_required_columns(airbnb_df):
    """Check that required Airbnb columns are available."""

    missing_columns = REQUIRED_COLUMNS - set(airbnb_df.columns)

    if missing_columns:
        raise ValueError(
            "Input dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def validate_coordinates(airbnb_df):
    """
    Report obviously invalid latitude and longitude values.

    Missing coordinates are allowed because they are recorded separately
    as NO_COORDINATES.
    """

    latitude = pd.to_numeric(
        airbnb_df["latitude"],
        errors="coerce",
    )

    longitude = pd.to_numeric(
        airbnb_df["longitude"],
        errors="coerce",
    )

    invalid_latitude = (
        latitude.notna()
        & ~latitude.between(-90, 90)
    )

    invalid_longitude = (
        longitude.notna()
        & ~longitude.between(-180, 180)
    )

    invalid_count = (
        invalid_latitude | invalid_longitude
    ).sum()

    if invalid_count:
        raise ValueError(
            f"Found {invalid_count:,} rows with invalid "
            "latitude or longitude values."
        )


# ============================================================
# INPUT
# ============================================================

def load_airbnb_data(file_path):
    """Load and validate the cleaned Airbnb dataset."""

    validate_input_file(file_path)

    airbnb_df = pd.read_excel(file_path)

    validate_required_columns(airbnb_df)
    validate_coordinates(airbnb_df)

    # Preserve a stable identifier for each source row.
    airbnb_df = airbnb_df.copy()
    airbnb_df["row_number"] = range(len(airbnb_df))

    print(f"Loaded Airbnb rows: {len(airbnb_df):,}")

    return airbnb_df


# ============================================================
# KOORDINATES QUERY
# ============================================================

def calculate_retry_delay(response, attempt):
    """Calculate delay before retrying a temporary API failure."""

    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            return max(0, float(retry_after))
        except ValueError:
            pass

    return (2 ** attempt) + random.random()


def query_sa2(row, api_key):
    """
    Query Koordinates for the SA2 corresponding to one Airbnb row.

    Returns a dictionary suitable for writing directly to the
    checkpoint file.
    """

    row_number, latitude, longitude = row

    result = {
        "row_number": row_number,
        "location_id": "",
        "location_name": "",
        "status": "FAILED",
        "error": "",
    }

    if pd.isna(latitude) or pd.isna(longitude):
        result["status"] = "NO_COORDINATES"
        return result

    params = {
        "key": api_key,
        "layer": LAYER_ID,
        "x": longitude,
        "y": latitude,
    }

    for attempt in range(MAX_RETRIES):

        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            if response.status_code in FATAL_STATUS_CODES:
                response.raise_for_status()

            is_server_error = (
                500 <= response.status_code < 600
            )

            if (
                response.status_code in RETRYABLE_STATUS_CODES
                or is_server_error
            ):
                if attempt < MAX_RETRIES - 1:
                    delay = calculate_retry_delay(
                        response,
                        attempt,
                    )
                    time.sleep(delay)
                    continue

            response.raise_for_status()

            response_data = response.json()

            features = (
                response_data
                .get("vectorQuery", {})
                .get("layers", {})
                .get(LAYER_ID, {})
                .get("features", [])
            )

            if not features:
                result["status"] = "NO_MATCH"
                return result

            properties = features[0].get(
                "properties",
                {},
            )

            result["location_id"] = properties.get(
                SA2_ID_FIELD,
                "",
            )

            result["location_name"] = properties.get(
                SA2_NAME_FIELD,
                "",
            )

            if result["location_id"]:
                result["status"] = "SUCCESS"
            else:
                result["status"] = "NO_MATCH"

            return result

        except requests.RequestException as exc:

            result["error"] = str(exc)

            status_code = getattr(
                exc.response,
                "status_code",
                None,
            )

            if status_code in FATAL_STATUS_CODES:
                raise RuntimeError(
                    "Koordinates request failed. "
                    "Check the API key, layer ID, and "
                    "request parameters."
                ) from exc

            if attempt < MAX_RETRIES - 1:
                delay = (2 ** attempt) + random.random()
                time.sleep(delay)

        except (ValueError, TypeError) as exc:
            result["error"] = (
                f"Invalid API response: {exc}"
            )
            break

    return result


# ============================================================
# CHECKPOINT MANAGEMENT
# ============================================================

def checkpoint_has_data():
    """Return True when the checkpoint exists and is non-empty."""

    return (
        CHECKPOINT_FILE.exists()
        and CHECKPOINT_FILE.stat().st_size > 0
    )


def load_checkpoint():
    """
    Load results from a previous run.

    Returns an empty DataFrame when no usable checkpoint exists.
    """

    if not checkpoint_has_data():
        print("No previous checkpoint. Starting fresh.")

        return pd.DataFrame(
            columns=CHECKPOINT_FIELDS
        )

    try:
        checkpoint_df = pd.read_csv(
            CHECKPOINT_FILE,
            dtype={
                "location_id": "string",
                "location_name": "string",
            },
        )

    except pd.errors.EmptyDataError:
        print("Checkpoint is empty. Starting fresh.")

        return pd.DataFrame(
            columns=CHECKPOINT_FIELDS
        )

    missing_fields = (
        set(CHECKPOINT_FIELDS)
        - set(checkpoint_df.columns)
    )

    if missing_fields:
        raise ValueError(
            "Checkpoint is missing required columns: "
            f"{sorted(missing_fields)}"
        )

    print(
        f"Checkpoint rows loaded: "
        f"{len(checkpoint_df):,}"
    )

    return checkpoint_df


def get_completed_rows(checkpoint_df):
    """Return row numbers already successfully resolved."""

    if checkpoint_df.empty:
        return set()

    completed_rows = checkpoint_df.loc[
        checkpoint_df["status"].isin(
            COMPLETED_STATUSES
        ),
        "row_number",
    ]

    completed_rows = pd.to_numeric(
        completed_rows,
        errors="coerce",
    ).dropna()

    return set(completed_rows.astype(int))


def get_remaining_queries(
    airbnb_df,
    completed_rows,
):
    """Return Airbnb rows that still require an API query."""

    return airbnb_df.loc[
        ~airbnb_df["row_number"].isin(
            completed_rows
        ),
        [
            "row_number",
            "latitude",
            "longitude",
        ],
    ]


def run_queries(
    remaining_df,
    api_key,
):
    """
    Query remaining Airbnb coordinates and append each result
    immediately to the checkpoint.

    Writing each completed result protects progress if execution
    is interrupted.
    """

    if remaining_df.empty:
        print("No remaining SA2 queries.")
        return

    CHECKPOINT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_header = not checkpoint_has_data()

    with CHECKPOINT_FILE.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as checkpoint_handle:

        writer = csv.DictWriter(
            checkpoint_handle,
            fieldnames=CHECKPOINT_FIELDS,
        )

        if write_header:
            writer.writeheader()

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            future_to_row = {
                executor.submit(
                    query_sa2,
                    row,
                    api_key,
                ): row[0]
                for row in remaining_df.itertuples(
                    index=False,
                    name=None,
                )
            }

            for processed_count, future in enumerate(
                as_completed(future_to_row),
                start=1,
            ):
                row_number = future_to_row[future]

                try:
                    result = future.result()

                except Exception as exc:
                    # Unexpected worker failures are retained
                    # rather than silently losing the row.
                    result = {
                        "row_number": row_number,
                        "location_id": "",
                        "location_name": "",
                        "status": "FAILED",
                        "error": str(exc),
                    }

                writer.writerow(result)

                # Save progress after every completed query.
                checkpoint_handle.flush()

                if (
                    processed_count % PROGRESS_EVERY == 0
                    or processed_count == len(remaining_df)
                ):
                    print(
                        f"Processed this run: "
                        f"{processed_count:,} / "
                        f"{len(remaining_df):,}"
                    )


# ============================================================
# PREPARE LOOKUP RESULTS
# ============================================================

def prepare_lookup():
    """
    Load checkpoint results and retain one result per source row.

    Successful results receive priority over failed attempts.
    """

    if not checkpoint_has_data():
        raise RuntimeError(
            "No checkpoint results are available."
        )

    lookup_df = pd.read_csv(
        CHECKPOINT_FILE,
        dtype={
            "location_id": "string",
            "location_name": "string",
        },
    )

    lookup_df["row_number"] = pd.to_numeric(
        lookup_df["row_number"],
        errors="raise",
    ).astype(int)

    # SUCCESS is preferred if a row has both failed and
    # successful attempts recorded.
    lookup_df["success_priority"] = (
        lookup_df["status"] == "SUCCESS"
    ).astype(int)

    lookup_df = (
        lookup_df
        .sort_values("success_priority")
        .drop_duplicates(
            subset="row_number",
            keep="last",
        )
        .drop(columns="success_priority")
    )

    return lookup_df


def save_failed_queries(lookup_df):
    """Save unresolved API failures for investigation."""

    failed_df = lookup_df.loc[
        lookup_df["status"] == "FAILED"
    ].copy()

    FAILED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    failed_df.to_csv(
        FAILED_FILE,
        index=False,
    )

    print(
        f"Failed queries: {len(failed_df):,}"
    )


# ============================================================
# MERGE
# ============================================================

def merge_sa2_results(
    airbnb_df,
    lookup_df,
):
    """Join SA2 lookup results to the original Airbnb observations."""

    original_row_count = len(airbnb_df)

    final_df = airbnb_df.merge(
        lookup_df[
            [
                "row_number",
                "location_id",
                "location_name",
            ]
        ],
        on="row_number",
        how="left",
        validate="one_to_one",
    )

    if len(final_df) != original_row_count:
        raise AssertionError(
            "Row count changed during SA2 merge. "
            f"Before: {original_row_count:,}; "
            f"after: {len(final_df):,}."
        )

    return final_df.drop(
        columns=["row_number"]
    )


# ============================================================
# SANITY CHECKS
# ============================================================

def sanity_check_known_listing(final_df):
    """
    Check a previously verified coordinate-to-SA2 mapping.

    Listing 40183765 is expected to map to SA2 316700,
    Christchurch Airport.
    """

    test_rows = final_df.loc[
        final_df["id"] == KNOWN_TEST_LISTING_ID,
        [
            "id",
            "location_id",
            "location_name",
        ],
    ].drop_duplicates()

    if test_rows.empty:
        print(
            "Sanity check skipped: known test listing "
            f"{KNOWN_TEST_LISTING_ID} is not in this dataset."
        )
        return

    print("\nKnown-location sanity check:")
    print(test_rows.to_string(index=False))

    observed_ids = set(
        test_rows["location_id"]
        .dropna()
        .astype(str)
    )

    if EXPECTED_TEST_SA2_ID not in observed_ids:
        raise AssertionError(
            f"Known listing {KNOWN_TEST_LISTING_ID} "
            f"did not map to expected SA2 "
            f"{EXPECTED_TEST_SA2_ID} "
            f"({EXPECTED_TEST_SA2_NAME})."
        )

    print(
        "Sanity check passed: known listing mapped "
        f"to SA2 {EXPECTED_TEST_SA2_ID} "
        f"({EXPECTED_TEST_SA2_NAME})."
    )


def display_query_summary(
    lookup_df,
    final_df,
):
    """Display high-level SA2 processing statistics."""

    print("\nQuery summary:")
    print(
        lookup_df["status"]
        .value_counts(dropna=False)
        .to_string()
    )

    rows_with_sa2 = (
        final_df["location_id"]
        .notna()
        .sum()
    )

    print(
        f"\nRows with SA2: "
        f"{rows_with_sa2:,} / "
        f"{len(final_df):,}"
    )


# ============================================================
# OUTPUT
# ============================================================

def save_output(final_df):
    """Save the SA2-enriched Airbnb dataset."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_df.to_excel(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved output: {OUTPUT_FILE}"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """Run the Airbnb-to-SA2 enrichment pipeline."""

    print("=" * 60)
    print("Christchurch Airbnb SA2 Assignment")
    print("=" * 60)

    api_key = get_api_key()

    airbnb_df = load_airbnb_data(
        INPUT_FILE
    )

    checkpoint_df = load_checkpoint()

    completed_rows = get_completed_rows(
        checkpoint_df
    )

    print(
        f"Already completed: "
        f"{len(completed_rows):,}"
    )

    remaining_df = get_remaining_queries(
        airbnb_df,
        completed_rows,
    )

    print(
        f"Remaining queries: "
        f"{len(remaining_df):,}"
    )

    run_queries(
        remaining_df,
        api_key,
    )

    lookup_df = prepare_lookup()

    save_failed_queries(
        lookup_df
    )

    final_df = merge_sa2_results(
        airbnb_df,
        lookup_df,
    )

    sanity_check_known_listing(
        final_df
    )

    display_query_summary(
        lookup_df,
        final_df,
    )

    save_output(
        final_df
    )


if __name__ == "__main__":
    main()