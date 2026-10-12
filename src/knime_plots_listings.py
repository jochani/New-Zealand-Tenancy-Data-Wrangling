import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    # Define directories based on your updated structure
    output_folder = 'output'
    analysis_folder = os.path.join(output_folder, 'analysis')
    plots_folder = os.path.join(output_folder, 'plots')
    
    # Ensure the plots directory exists
    os.makedirs(plots_folder, exist_ok=True)
    
    # Load required datasets
    master_csv = os.path.join(output_folder, 'processed', 'all_listings.csv')
    top_10_csv = os.path.join(analysis_folder, 'christchurch_top_10_percent_highest_reviews.csv')
    
    print(f"Loading master dataset from: {master_csv}")
    master_df = pd.read_csv(master_csv)
    
    # Ensure days_since_last_review exists in master_df on the fly
    PUBLISH_DATE = '2026-06-20'
    publish_dt = pd.to_datetime(PUBLISH_DATE)
    last_review_dt = pd.to_datetime(master_df['last_review'])
    master_df['days_since_last_review'] = (publish_dt - last_review_dt).dt.days.astype('Int64')
    
    print(f"Loading top 10% dataset from: {top_10_csv}")
    top_10_df = pd.read_csv(top_10_csv)

    # ---------------------------------------------------------------
    # E. DATA VISUALIZATIONS / PLOTTING
    # ---------------------------------------------------------------
    print("\n-- Generating Data Visualizations --\n")

    # Styling configuration
    plt.style.use('seaborn-v0_8-whitegrid')
    PLOT_COLOR = "#5874C8"

    # 1. Distribution of Airbnb Prices (With Outliers)
    plt.figure(figsize=(10, 6))
    plt.hist(master_df['price'].dropna(), bins=50, color=PLOT_COLOR, edgecolor='white')
    plt.title('Distribution of Airbnb Prices in Christchurch City', fontsize=14, fontweight='bold')
    plt.xlabel('Price per night (NZD)', fontsize=12)
    plt.ylabel('Number of listings', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    plot_1a_path = os.path.join(plots_folder, 'price_distribution_with_outliers.png')
    plt.savefig(plot_1a_path, dpi=300)
    plt.close()
    print(f"✔ Saved Plot 1A to: {plot_1a_path}")

    # 2. Distribution of Airbnb Prices (Without Outliers <= 1500)
    df_price_filtered = master_df[master_df['price'] <= 1500]

    plt.figure(figsize=(10, 6))
    plt.hist(df_price_filtered['price'], bins=40, color=PLOT_COLOR, edgecolor='white')
    plt.title('Distribution of Airbnb Prices (x=1500)', fontsize=14, fontweight='bold')
    plt.xlabel('Price per night (NZD)', fontsize=12)
    plt.ylabel('Number of listings', fontsize=12)
    plt.xlim(0, 1500)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    plot_1b_path = os.path.join(plots_folder, 'price_distribution_christchurch_without_outliers.png')
    plt.savefig(plot_1b_path, dpi=300)
    plt.close()
    print(f"✔ Saved Plot 1B to: {plot_1b_path}")

    # ===============================================================
    # PLOT 2A: Listing Activity & Recency Status (Bar Chart)
    # ===============================================================
    def get_recency_status(days):
        if pd.isna(days):
            return 'No Reviews'
        elif days <= 30:
            return '0–30 Days'
        elif days <= 90:
            return '31–90 Days'
        elif days <= 365:
            return '91–365 Days'
        else:
            return '>365 Days'

    master_df['recency_status'] = master_df['days_since_last_review'].apply(get_recency_status)

    recency_order = ['>365 Days', '0–30 Days', '91–365 Days', '31–90 Days']
    recency_counts = master_df['recency_status'].value_counts().reindex(recency_order).fillna(0)

    plt.figure(figsize=(10, 6))
    bars = plt.bar(recency_counts.index, recency_counts.values, color=PLOT_COLOR, width=0.55)
    plt.title('Listing Activity According To Date Difference', fontsize=14, fontweight='bold', loc='left')
    plt.xlabel('Listing Recency Status', fontsize=12)
    plt.ylabel('Number of Listings', fontsize=12)
    plt.grid(axis='y', alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + (max(recency_counts.values) * 0.015),
                 f'{int(height):,}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()

    plot_2a_path = os.path.join(plots_folder, 'recency_status.png')
    plt.savefig(plot_2a_path, dpi=300)
    plt.close()
    print(f"✔ Saved Plot 2A to: {plot_2a_path}")

    # ===============================================================
    # PLOT 2B: Distribution of Days Since Last Review (Histogram)
    # ===============================================================
    df_days_filtered = master_df[master_df['days_since_last_review'].between(0, 365)]

    plt.figure(figsize=(10, 6))
    plt.hist(df_days_filtered['days_since_last_review'], bins=30, color=PLOT_COLOR, edgecolor='white')
    plt.title('Distribution of Days Since Last Review', fontsize=14, fontweight='bold', loc='left')
    plt.xlabel('Days Since Last Review', fontsize=12)
    plt.ylabel('Number of Listings', fontsize=12)
    plt.xlim(0, 365)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    plot_2b_path = os.path.join(plots_folder, 'days_since_last_review.png')
    plt.savefig(plot_2b_path, dpi=300)
    plt.close()
    print(f"✔ Saved Plot 2B to: {plot_2b_path}")

    # ===============================================================
    # PLOT 3: Top 10% Days Since Last Review
    # ===============================================================
    top_10_days_filtered = top_10_df[top_10_df['days_since_last_review'].between(0, 365)]

    plt.figure(figsize=(10, 6))
    plt.hist(top_10_days_filtered['days_since_last_review'], bins=30, color=PLOT_COLOR, edgecolor='white')
    plt.title('Distribution of Days Since Last Review of Top 10% Christchurch Listings', fontsize=14, fontweight='bold', loc='left')
    plt.xlabel('Days Since Last Review', fontsize=12)
    plt.ylabel('Number of Listings', fontsize=12)
    plt.xlim(0, 365)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    plot_3_path = os.path.join(plots_folder, 'top_10_percent_days_since_last_review.png')
    plt.savefig(plot_3_path, dpi=300)
    plt.close()
    print(f"✔ Saved Plot 3 to: {plot_3_path}")
    
    print(f"\nAll visual saved to: {plots_folder}\n")