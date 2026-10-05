"""
Add SA2 geographic information to cleaned Christchurch Airbnb data.

DATA422 - New Zealand Tenancy Data Wrangling

Purpose
-------
Assign each unique Christchurch Airbnb coordinate to a Statistical Area 2
(SA2 2026) using latitude and longitude and the Koordinates Vector Query API.

Input
-----
output/processed/christchurch_airbnb_clean.csv

Outputs
-------
output/processed/christchurch_airbnb_clean_with_sa2.csv
output/checkpoints/koordinates_sa2_checkpoint.csv
output/logs/koordinates_failed_queries.csv

Design principles
-----------------
- Use relative project paths.
- Preserve the original cleaned dataset.
- Query each unique coordinate only once.
- Reuse previously resolved coordinates.
- Record failed API queries.
- Preserve progress using a checkpoint.
- Retry temporary API failures.
- Validate row counts after merging.
- Perform a known-location sanity check.
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
    "output/processed/christchurch_airbnb_clean.csv"
)

OUTPUT_FILE = Path(
    "output/processed/christchurch_airbnb_clean_with_sa2.csv"
)

CHECKPOINT_FILE = Path(
    "output/checkpoints/koordinates_sa2_checkpoint.csv"
)

FAILED_FILE = Path(
    "output/logs/koordinates_failed_queries.csv"
)

# Optional backup of an old row-number checkpoint.
OLD_CHECKPOINT_BACKUP = Path(
    "output/checkpoints/koordinates_sa2_checkpoint_row_number_backup.csv"
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
    "latitude",
    "longitude",
    "location_id",
    "location_name",
    "status",
    "error",
]

# Previously verified geographic sanity check.
KNOWN_TEST_LISTING_ID = "40183765"
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

    missing_columns = (
        REQUIRED_COLUMNS - set(airbnb_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Input dataset is missing required columns: "
            f"{sorted(missing_columns)}"
        )


def validate_coordinates(airbnb_df):
    """Validate latitude and longitude ranges."""

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

    airbnb_df = pd.read_csv(
        file_path,
        dtype={
            "id": "string",
        },
        low_memory=False,
    )

    validate_required_columns(airbnb_df)
    validate_coordinates(airbnb_df)

    # Ensure coordinates have consistent numeric types.
    airbnb_df["latitude"] = pd.to_numeric(
        airbnb_df["latitude"],
        errors="coerce",
    )

    airbnb_df["longitude"] = pd.to_numeric(
        airbnb_df["longitude"],
        errors="coerce",
    )

    print(
        f"Loaded Airbnb rows: "
        f"{len(airbnb_df):,}"
    )

    return airbnb_df


def prepare_unique_coordinates(airbnb_df):
    """
    Create one query for each unique coordinate pair.

    The same listing/location may occur in several monthly
    snapshots. Querying unique coordinates avoids unnecessary
    repeated API requests.
    """

    coordinates_df = (
        airbnb_df[
            ["latitude", "longitude"]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    print(
        f"Unique coordinates: "
        f"{len(coordinates_df):,}"
    )

    repeated_count = (
        len(airbnb_df) - len(coordinates_df)
    )

    print(
        f"Repeated coordinate observations avoided: "
        f"{repeated_count:,}"
    )

    return coordinates_df


# ============================================================
# KOORDINATES QUERY
# ============================================================

def calculate_retry_delay(response, attempt):
    """Calculate delay before retrying a temporary API failure."""

    retry_after = response.headers.get(
        "Retry-After"
    )

    if retry_after:
        try:
            return max(
                0,
                float(retry_after),
            )
        except ValueError:
            pass

    return (2 ** attempt) + random.random()


def query_sa2(row, api_key):
    """
    Query Koordinates for one coordinate pair.

    Returns a dictionary suitable for writing directly
    to the checkpoint file.
    """

    latitude, longitude = row

    result = {
        "latitude": latitude,
        "longitude": longitude,
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
                response.status_code
                in RETRYABLE_STATUS_CODES
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
                delay = (
                    (2 ** attempt)
                    + random.random()
                )

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
    """Return True if checkpoint exists and is non-empty."""

    return (
        CHECKPOINT_FILE.exists()
        and CHECKPOINT_FILE.stat().st_size > 0
    )


def detect_old_checkpoint():
    """
    Detect the old row-number checkpoint format.

    Returns True if the existing checkpoint uses row_number
    instead of latitude/longitude.
    """

    if not checkpoint_has_data():
        return False

    try:
        header_df = pd.read_csv(
            CHECKPOINT_FILE,
            nrows=1,
        )
    except pd.errors.EmptyDataError:
        return False

    columns = set(header_df.columns)

    return (
        "row_number" in columns
        and "latitude" not in columns
        and "longitude" not in columns
    )


def backup_old_checkpoint():
    """
    Back up an old row-number checkpoint.

    The old checkpoint cannot safely be reused after the input
    dataset changes because row numbers are positional rather
    than geographic identifiers.
    """

    if not detect_old_checkpoint():
        return

    print(
        "\nOld row-number checkpoint detected."
    )

    OLD_CHECKPOINT_BACKUP.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OLD_CHECKPOINT_BACKUP.exists():
        OLD_CHECKPOINT_BACKUP.unlink()

    CHECKPOINT_FILE.replace(
        OLD_CHECKPOINT_BACKUP
    )

    print(
        "Old checkpoint backed up to:"
    )
    print(
        OLD_CHECKPOINT_BACKUP
    )

    print(
        "A new coordinate-based checkpoint "
        "will be created."
    )


def load_checkpoint():
    """
    Load coordinate-based checkpoint results.

    Returns an empty DataFrame when no checkpoint exists.
    """

    if not checkpoint_has_data():
        print(
            "No coordinate checkpoint. "
            "Starting fresh."
        )

        return pd.DataFrame(
            columns=CHECKPOINT_FIELDS
        )

    try:
        checkpoint_df = pd.read_csv(
            CHECKPOINT_FILE,
            dtype={
                "location_id": "string",
                "location_name": "string",
                "status": "string",
                "error": "string",
            },
        )

    except pd.errors.EmptyDataError:
        print(
            "Checkpoint is empty. "
            "Starting fresh."
        )

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

    checkpoint_df["latitude"] = pd.to_numeric(
        checkpoint_df["latitude"],
        errors="coerce",
    )

    checkpoint_df["longitude"] = pd.to_numeric(
        checkpoint_df["longitude"],
        errors="coerce",
    )

    print(
        f"Checkpoint rows loaded: "
        f"{len(checkpoint_df):,}"
    )

    return checkpoint_df


def get_completed_coordinates(checkpoint_df):
    """
    Return coordinate pairs already successfully processed.
    """

    if checkpoint_df.empty:
        return set()

    completed_df = checkpoint_df.loc[
        checkpoint_df["status"].isin(
            COMPLETED_STATUSES
        )
    ]

    return set(
        zip(
            completed_df["latitude"],
            completed_df["longitude"],
        )
    )


def get_remaining_queries(
    coordinates_df,
    completed_coordinates,
):
    """
    Return coordinates not already resolved in checkpoint.
    """

    if not completed_coordinates:
        return coordinates_df.copy()

    coordinate_pairs = list(
        zip(
            coordinates_df["latitude"],
            coordinates_df["longitude"],
        )
    )

    remaining_mask = [
        pair not in completed_coordinates
        for pair in coordinate_pairs
    ]

    return (
        coordinates_df
        .loc[remaining_mask]
        .copy()
    )


def run_queries(
    remaining_df,
    api_key,
):
    """
    Query remaining coordinates and append results immediately.

    Each result is flushed to disk so progress is preserved if
    processing is interrupted.
    """

    if remaining_df.empty:
        print(
            "No remaining SA2 queries."
        )
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

            future_to_coordinate = {
                executor.submit(
                    query_sa2,
                    row,
                    api_key,
                ): row
                for row in remaining_df.itertuples(
                    index=False,
                    name=None,
                )
            }

            for processed_count, future in enumerate(
                as_completed(
                    future_to_coordinate
                ),
                start=1,
            ):

                coordinate = (
                    future_to_coordinate[future]
                )

                try:
                    result = future.result()

                except Exception as exc:
                    latitude, longitude = coordinate

                    result = {
                        "latitude": latitude,
                        "longitude": longitude,
                        "location_id": "",
                        "location_name": "",
                        "status": "FAILED",
                        "error": str(exc),
                    }

                writer.writerow(result)

                # Preserve progress immediately.
                checkpoint_handle.flush()

                if (
                    processed_count
                    % PROGRESS_EVERY == 0
                    or processed_count
                    == len(remaining_df)
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
    Load checkpoint results and retain one result
    per coordinate pair.

    SUCCESS results are preferred over failed attempts.
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
            "status": "string",
            "error": "string",
        },
    )

    lookup_df["latitude"] = pd.to_numeric(
        lookup_df["latitude"],
        errors="coerce",
    )

    lookup_df["longitude"] = pd.to_numeric(
        lookup_df["longitude"],
        errors="coerce",
    )

    # Prefer completed results over failed attempts.
    lookup_df["completed_priority"] = (
        lookup_df["status"]
        .isin(COMPLETED_STATUSES)
        .astype(int)
    )

    lookup_df = (
        lookup_df
        .sort_values(
            "completed_priority"
        )
        .drop_duplicates(
            subset=[
                "latitude",
                "longitude",
            ],
            keep="last",
        )
        .drop(
            columns="completed_priority"
        )
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
        f"Failed queries: "
        f"{len(failed_df):,}"
    )


# ============================================================
# MERGE
# ============================================================

def merge_sa2_results(
    airbnb_df,
    lookup_df,
):
    """
    Join SA2 results to Airbnb observations using coordinates.

    Many Airbnb monthly observations may share one coordinate,
    therefore this is a many-to-one merge.
    """

    original_row_count = len(airbnb_df)

    lookup_for_merge = lookup_df[
        [
            "latitude",
            "longitude",
            "location_id",
            "location_name",
        ]
    ].copy()

    final_df = airbnb_df.merge(
        lookup_for_merge,
        on=[
            "latitude",
            "longitude",
        ],
        how="left",
        validate="many_to_one",
    )

    if len(final_df) != original_row_count:
        raise AssertionError(
            "Row count changed during SA2 merge. "
            f"Before: {original_row_count:,}; "
            f"after: {len(final_df):,}."
        )

    return final_df


# ============================================================
# SANITY CHECKS
# ============================================================

def sanity_check_known_listing(final_df):
    """
    Validate a previously verified coordinate-to-SA2 mapping.

    Listing 40183765 is expected to map to:
    SA2 316700 - Christchurch Airport.
    """

    test_rows = final_df.loc[
        final_df["id"].astype("string")
        == KNOWN_TEST_LISTING_ID,
        [
            "id",
            "location_id",
            "location_name",
        ],
    ].drop_duplicates()

    if test_rows.empty:
        print(
            "\nSanity check skipped: "
            "known test listing "
            f"{KNOWN_TEST_LISTING_ID} "
            "is not in this dataset."
        )
        return

    print(
        "\nKnown-location sanity check:"
    )

    print(
        test_rows.to_string(
            index=False
        )
    )

    observed_ids = set(
        test_rows["location_id"]
        .dropna()
        .astype(str)
    )

    if EXPECTED_TEST_SA2_ID not in observed_ids:
        raise AssertionError(
            f"Known listing "
            f"{KNOWN_TEST_LISTING_ID} "
            f"did not map to expected SA2 "
            f"{EXPECTED_TEST_SA2_ID} "
            f"({EXPECTED_TEST_SA2_NAME})."
        )

    print(
        "Sanity check passed: "
        "known listing mapped to SA2 "
        f"{EXPECTED_TEST_SA2_ID} "
        f"({EXPECTED_TEST_SA2_NAME})."
    )


def display_query_summary(
    lookup_df,
    final_df,
):
    """Display high-level SA2 processing statistics."""

    print(
        "\nQuery summary:"
    )

    print(
        lookup_df["status"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    rows_with_sa2 = (
        final_df["location_id"]
        .notna()
        .sum()
    )

    missing_sa2 = (
        final_df["location_id"]
        .isna()
        .sum()
    )

    print(
        f"\nRows with SA2: "
        f"{rows_with_sa2:,} / "
        f"{len(final_df):,}"
    )

    print(
        f"Rows without SA2: "
        f"{missing_sa2:,}"
    )


def validate_final_output(
    airbnb_df,
    final_df,
):
    """Perform final structural validation."""

    if len(final_df) != len(airbnb_df):
        raise AssertionError(
            "Final output row count differs "
            "from input row count."
        )

    required_output_columns = {
        "location_id",
        "location_name",
    }

    missing_columns = (
        required_output_columns
        - set(final_df.columns)
    )

    if missing_columns:
        raise AssertionError(
            "Final output is missing SA2 columns: "
            f"{sorted(missing_columns)}"
        )

    print(
        "\nFinal SA2 validation: PASS"
    )

    print(
        f"Final rows: "
        f"{len(final_df):,}"
    )


# ============================================================
# OUTPUT
# ============================================================

def save_output(final_df):
    """Save the SA2-enriched Airbnb dataset as CSV."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        f"\nSaved output:\n"
        f"{OUTPUT_FILE}"
    )


def verify_saved_output(final_df):
    """Reload the CSV and verify its shape."""

    saved_df = pd.read_csv(
        OUTPUT_FILE,
        low_memory=False,
    )

    if saved_df.shape != final_df.shape:
        raise AssertionError(
            "Saved output shape does not match "
            "the in-memory SA2 dataset. "
            f"Expected {final_df.shape}, "
            f"found {saved_df.shape}."
        )

    print(
        "Saved-file verification: PASS"
    )

    print(
        f"Verified shape: "
        f"{saved_df.shape[0]:,} rows x "
        f"{saved_df.shape[1]} columns"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """Run the Airbnb-to-SA2 enrichment pipeline."""

    print("=" * 70)
    print(
        "DATA422 - CHRISTCHURCH AIRBNB SA2 ASSIGNMENT"
    )
    print("=" * 70)

    api_key = get_api_key()

    airbnb_df = load_airbnb_data(
        INPUT_FILE
    )

    coordinates_df = (
        prepare_unique_coordinates(
            airbnb_df
        )
    )

    # Detect an old positional checkpoint before loading
    # the new coordinate-based cache.
    backup_old_checkpoint()

    checkpoint_df = load_checkpoint()

    completed_coordinates = (
        get_completed_coordinates(
            checkpoint_df
        )
    )

    print(
        f"Already cached coordinates: "
        f"{len(completed_coordinates):,}"
    )

    remaining_df = get_remaining_queries(
        coordinates_df,
        completed_coordinates,
    )

    print(
        f"Remaining API queries: "
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

    validate_final_output(
        airbnb_df,
        final_df,
    )

    save_output(
        final_df
    )

    verify_saved_output(
        final_df
    )

    print(
        "\nSA2 assignment completed successfully."
    )


if __name__ == "__main__":
    main()