import os
import sys
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    input_folder = os.path.join('output')
    analysis_folder = os.path.join('output', 'analysis')
    summary_folder = os.path.join('output', 'summaries')
    
    input_file = os.path.join(input_folder, 'processed', 'all_listings.csv')
    
    # Setup text logging so results print to screen AND save to your existing analysis folder
    log_file_path = os.path.join(summary_folder, 'knime_workflow_summary.txt')
    
    class Tee:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, 'w', encoding='utf-8')
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()
        def flush(self):
            self.terminal.flush()
            self.log.flush()

    # Redirect stdout to both the terminal and the summary text file
    sys.stdout = Tee(log_file_path)

    try:
        print(f"\n-- Reproducing KNIME Workflow --\n")
        master_df = pd.read_csv(input_file)

        PUBLISH_DATE = '2026-06-20'
        print(f"Publish Date: {PUBLISH_DATE}")

        # Drop 'license' empty column from data if present
        if 'license' in master_df.columns:
            master_df.drop(columns=['license'], inplace=True)

        # Days since last review calculation
        publish_dt = pd.to_datetime(PUBLISH_DATE)
        last_review_dt = pd.to_datetime(master_df['last_review'])
        master_df['days_since_last_review'] = (publish_dt - last_review_dt).dt.days.astype('Int64')
        print("✔ Calculated 'days_since_last_review' and added as a new column.")

        # Extract Top 10% highest reviewed listings
        total_listings = len(master_df)
        master_df_sorted = master_df.sort_values(by='number_of_reviews', ascending=False)
        top_10_count = int(total_listings * 0.10)
        top_10_df = master_df_sorted.head(top_10_count)

        print(f"✔ Total Number of Christchurch Listings: {total_listings:,}")
        print(f"✔ Top 10% Christchurch Listings with highest number of reviews: {len(top_10_df):,}")

        # Display preview
        print("\n--- Top 10% Highest Reviewed Listings Preview ---\n")
        print(top_10_df[['id', 'name', 'number_of_reviews', 'last_review', 'days_since_last_review']].head(10).to_string())

        # Save Top 10% transformed dataset to CSV in your existing analysis folder
        top_10_output = os.path.join(analysis_folder, 'christchurch_top_10_percent_highest_reviews.csv')
        top_10_df.to_csv(top_10_output, index=False)
        print(f"\nSaved Top 10% dataset to: {top_10_output}\n")

    finally:
        # Restore normal terminal output and close log file properly
        if isinstance(sys.stdout, Tee):
            sys.stdout.log.close()
            sys.stdout = sys.stdout.terminal
        print(f"Workflow text summary saved to: {log_file_path}")