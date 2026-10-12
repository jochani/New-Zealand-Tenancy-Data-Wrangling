import subprocess
import sys

# Base script names without repeating "src/"
scripts = [
    "concatenate_listings.py", # Step 1
    "knime_workflow_listings.py", # Step 2
    "knime_plots_listings.py", # Step 3
    "clean_airbnb_listings.py", # Step 4
    "test_query.py", # Step 5
    "listings_api_enrichment.py", # Step 6
    "clean_rental_bond.py", # Step 7
    "merge_bonds_listings.py", # Step 8
    "inspect_merged_bond_listings.py", # Step 9
    "clean_short_v_long_term_rentals.py", # Step 10
    "short_v_long_rentals_analysis.py", # Step 11
    "short_v_long_rentals_plots.py" # Step 12
]

def run_pipeline():
    print("=== STARTING FULL HOUSING ANALYSIS PIPELINE ===")
    for filename in scripts:
        script_path = f"src/{filename}"
        print(f"\n---> Running: {script_path}")
        result = subprocess.run([sys.executable, script_path], capture_output=False)
        if result.returncode != 0:
            print(f"❌ Error occurred while executing {script_path}. Pipeline halted.")
            sys.exit(1)
    print("\n==================================================")
    print("SUCCESS: Full pipeline executed and outputs updated!")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()