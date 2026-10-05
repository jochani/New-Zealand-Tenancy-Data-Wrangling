"""
DATA422 - Automated Data Wrangling Pipeline

Runs the complete Christchurch Airbnb and rental bond workflow
from one command.

Run from the project root:

    python run_pipeline.py
"""

import subprocess
import sys
import time
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"


PIPELINE_STAGES = [
    (
        "Join monthly Airbnb files",
        SRC_DIR / "join_airbnb_files.py",
    ),
    (
        "Clean Airbnb data",
        SRC_DIR / "clean_airbnb.py",
    ),
    (
        "Add SA2 geographic information",
        SRC_DIR / "add_sa2_to_airbnb.py",
    ),
    (
        "Clean rental bond data",
        SRC_DIR / "clean_rental_bonds.py",
    ),
    (
        "Join Airbnb and rental bond data",
        SRC_DIR / "join_airbnb_bonds.py",
    ),
    (
        "Create SQLite database and run SQL analysis",
        SRC_DIR / "sqlite_airbnb_bonds.py",
    ),
    (
        "Generate updated plots",
        SRC_DIR / "generate_updated_plots.py",
    ),
]


# ============================================================
# DISPLAY
# ============================================================

def print_header():
    """Print the pipeline heading."""

    print("\n" + "=" * 72)
    print("DATA422 - AUTOMATED DATA WRANGLING PIPELINE")
    print("=" * 72)

    print(f"\nProject directory:\n{PROJECT_ROOT}")

    print(f"\nPython executable:\n{sys.executable}")


# ============================================================
# SCRIPT VALIDATION
# ============================================================

def validate_stage_files():
    """Check that all required pipeline scripts exist."""

    print("\n" + "=" * 72)
    print("PIPELINE SCRIPT VALIDATION")
    print("=" * 72)

    missing_files = []

    for stage_name, script_path in PIPELINE_STAGES:

        relative_path = script_path.relative_to(
            PROJECT_ROOT
        )

        if script_path.exists():

            print(
                f"PASS: {relative_path}"
            )

        else:

            print(
                f"FAIL: {relative_path}"
            )

            missing_files.append(
                script_path
            )

    if missing_files:

        raise FileNotFoundError(
            "One or more required pipeline "
            "scripts are missing:\n"
            + "\n".join(
                str(path)
                for path in missing_files
            )
        )

    print("\nPipeline script validation: PASS")


# ============================================================
# RUN INDIVIDUAL STAGE
# ============================================================

def run_stage(
    stage_number,
    total_stages,
    stage_name,
    script_path,
):
    """Run one pipeline stage."""

    print("\n" + "=" * 72)

    print(
        f"STAGE {stage_number}/{total_stages}: "
        f"{stage_name}"
    )

    print("=" * 72)

    relative_script = script_path.relative_to(
        PROJECT_ROOT
    )

    print(
        f"Running: {relative_script}\n"
    )

    start_time = time.perf_counter()

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=PROJECT_ROOT,
    )

    elapsed_seconds = (
        time.perf_counter()
        - start_time
    )

    if result.returncode != 0:

        print("\n" + "!" * 72)

        print(
            f"PIPELINE FAILED AT STAGE "
            f"{stage_number}: {stage_name}"
        )

        print(
            f"Exit code: {result.returncode}"
        )

        print(
            f"Elapsed time: "
            f"{elapsed_seconds:.2f} seconds"
        )

        print("!" * 72)

        raise RuntimeError(
            f"Pipeline stage failed: "
            f"{stage_name}"
        )

    print(
        f"\nSTAGE {stage_number} PASS "
        f"({elapsed_seconds:.2f} seconds)"
    )


# ============================================================
# FINAL OUTPUT VALIDATION
# ============================================================

def validate_final_outputs():
    """Check the important outputs produced by the pipeline."""

    print("\n" + "=" * 72)
    print("FINAL OUTPUT VALIDATION")
    print("=" * 72)

    expected_outputs = [

        # Airbnb processing
        Path(
            "output/processed/"
            "christchurch_airbnb_joined_file.csv"
        ),

        Path(
            "output/processed/"
            "christchurch_airbnb_clean.csv"
        ),

        Path(
            "output/processed/"
            "christchurch_airbnb_clean_with_sa2.csv"
        ),

        # Rental bond processing
        Path(
            "output/processed/"
            "rental_bonds_clean.csv"
        ),

        # Pandas Airbnb / bond integration
        Path(
            "output/processed/"
            "christchurch_airbnb_bonds_joined.csv"
        ),

        Path(
            "output/logs/"
            "airbnb_unmatched_bonds.csv"
        ),

        # SQLite analysis
        Path(
            "output/sqlite/"
            "christchurch_rentals.db"
        ),

        Path(
            "output/sqlite/"
            "sql_joined_airbnb_bonds.csv"
        ),

        Path(
            "output/sqlite/"
            "sql_area_price_gaps.csv"
        ),

        # Updated analysis
        Path(
            "output/plots/"
            "monthly_summary.csv"
        ),

        Path(
            "output/plots/"
            "monthly_listing_count.png"
        ),

        Path(
            "output/plots/"
            "monthly_median_price.png"
        ),

        Path(
            "output/plots/"
            "monthly_missing_price_percentage.png"
        ),

        Path(
            "output/plots/"
            "sa2_airbnb_rental_price_gap.png"
        ),
    ]

    missing_outputs = []

    for relative_path in expected_outputs:

        output_path = (
            PROJECT_ROOT / relative_path
        )

        if output_path.exists():

            file_size = (
                output_path.stat().st_size
            )

            print(
                f"PASS: {relative_path} "
                f"({file_size:,} bytes)"
            )

        else:

            print(
                f"FAIL: {relative_path}"
            )

            missing_outputs.append(
                relative_path
            )

    if missing_outputs:

        raise AssertionError(
            "Pipeline completed but expected "
            "outputs are missing:\n"
            + "\n".join(
                str(path)
                for path in missing_outputs
            )
        )

    print("\nFinal output validation: PASS")


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    """Run the complete DATA422 pipeline."""

    pipeline_start = time.perf_counter()

    print_header()

    try:

        validate_stage_files()

        total_stages = len(
            PIPELINE_STAGES
        )

        for stage_number, (
            stage_name,
            script_path,
        ) in enumerate(
            PIPELINE_STAGES,
            start=1,
        ):

            run_stage(
                stage_number,
                total_stages,
                stage_name,
                script_path,
            )

        validate_final_outputs()

    except Exception as error:

        total_elapsed = (
            time.perf_counter()
            - pipeline_start
        )

        print("\n" + "=" * 72)
        print("PIPELINE STATUS: FAILED")
        print("=" * 72)

        print(
            f"\nReason:\n{error}"
        )

        print(
            f"\nElapsed time: "
            f"{total_elapsed:.2f} seconds"
        )

        sys.exit(1)

    total_elapsed = (
        time.perf_counter()
        - pipeline_start
    )

    print("\n" + "=" * 72)
    print("PIPELINE STATUS: SUCCESS")
    print("=" * 72)

    print(
        "\nAll DATA422 processing stages "
        "completed successfully."
    )

    print(
        f"\nTotal pipeline time: "
        f"{total_elapsed:.2f} seconds"
    )

    print(
        "\nFinal processed Airbnb dataset:"
    )

    print(
        "output/processed/"
        "christchurch_airbnb_clean_with_sa2.csv"
    )

    print(
        "\nAirbnb / rental bond joined dataset:"
    )

    print(
        "output/processed/"
        "christchurch_airbnb_bonds_joined.csv"
    )

    print(
        "\nSQLite joined dataset:"
    )

    print(
        "output/sqlite/"
        "sql_joined_airbnb_bonds.csv"
    )

    print(
        "\nUpdated plots:"
    )

    print(
        "output/plots/"
    )


if __name__ == "__main__":
    main()