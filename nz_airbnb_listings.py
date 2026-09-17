import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

#   Reusable Pipeline Function
def process_single_dataset(file_path: str) -> pd.DataFrame:
    
    #filename extraction
    filename = os.path.basename(file_path)
    
    #automatic file convertion from 'listings_October_2025.csv' -> 'October 2025'
    month_year = filename.replace('listings_', '').replace('.csv', '').replace('_', ' ')
    
    #dataset loaded
    df = pd.read_csv(file_path)
    
    #filtered to on Christchurch City only
    df_filtered = df[df['neighbourhood_group'] == 'Christchurch City'].copy()
    
    #added column for month + year
    df_filtered['month_year'] = month_year
    
    return df_filtered

#the real deal!!!
if __name__ == '__main__':
    data_folder = 'data'
    
    #located file auto inside the 'data/' folder
    csv_files = glob.glob(os.path.join(data_folder, 'listings_*.csv'))
    
    processed_dfs = []
    
    print("\n--- Processing Files ---")
    for file_path in csv_files:
        df_processed = process_single_dataset(file_path)
        processed_dfs.append(df_processed)
        
        #pulled month_year value to print a confirmation
        month_label = df_processed['month_year'].iloc[0] if not df_processed.empty else "Unknown"
        print(f"Processed {os.path.basename(file_path)} -> Label: '{month_label}' ({len(df_processed)} rows)")

    #concat all processed datasets
    master_df = pd.concat(processed_dfs, ignore_index=True)
    print(f"\nConcatenation complete. Total Christchurch rows: {len(master_df)}")

    #saved concat dataset to a new CSV file
    output_file = os.path.join(data_folder, 'christchurch_combined_2025_2026.csv')
    master_df.to_csv(output_file, index=False)
    print(f"Combined dataset saved to: {output_file}\n")

    #summary statistics (ta da!!!)
    print("\n-- Missing Values Per Column --\n")
    print(master_df.isnull().sum())
    
    print("\n-- Numerical Summary Statistics --\n")
    print(master_df.describe().T)

    print("\n-- Categorical Summary Statistics --\n")
    print(master_df.describe(include=['object']).T)
    print("\n")
    
#   KNIME Workflow Reproduction
print("\n-- Reproducing KNIME Workflow --\n")

PUBLISH_DATE = '2026-06-20'
print(f"Publish Date: {PUBLISH_DATE}")

#deleted 'license' empty column from data
if 'license' in master_df.columns:
    master_df.drop(columns=['license'], inplace=True)

# days since last review
publish_dt = pd.to_datetime(PUBLISH_DATE)
last_review_dt = pd.to_datetime(master_df['last_review'])
master_df['days_since_last_review'] = (publish_dt - last_review_dt).dt.days.astype('Int64')
print("✔ Calculated 'days_since_last_review' and Added as a new column.")

#extracted Top 10% highest reviewed listings
total_listings = len(master_df)
master_df_sorted = master_df.sort_values(by='number_of_reviews', ascending=False)
top_10_count = int(total_listings * 0.10)
top_10_df = master_df_sorted.head(top_10_count)

print(f"✔ Total Number of Christchurch Listings: {total_listings:,}")
print(f"✔ Top 10% Christchurch Listings with highest number of reviews: {len(top_10_df):,}")

# --- Top 10% ---
print("\n--- Top 10% Highest Reviewed Listings ---\n")
print(top_10_df[['id', 'name', 'number_of_reviews', 'last_review', 'days_since_last_review']].head(10))

# Save Top 10% transformed dataset to CSV
top_10_output = os.path.join('data', 'christchurch_top_10_percent_highest_reviews.csv')
top_10_df.to_csv(top_10_output, index=False)
print(f"\nSaved Top 10% dataset to: {top_10_output}")
print("\n")

# ---------------------------------------------------------------
# E. DATA VISUALIZATIONS / PLOTTING
# ---------------------------------------------------------------
print("\n-- Data Visualization--\n")

# styling configuration
plt.style.use('seaborn-v0_8-whitegrid')
PLOT_COLOR = "#5874C8"

#Distribution of Airbnb Prices (With Outliers)
plt.figure(figsize=(10, 6))
plt.hist(master_df['price'].dropna(), bins=50, color=PLOT_COLOR, edgecolor='white')
plt.title('Distribution of Airbnb Prices in Christchurch City', fontsize=14, fontweight='bold')
plt.xlabel('Price per night (NZD)', fontsize=12)
plt.ylabel('Number of listings', fontsize=12)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

plot_1a_path = os.path.join('data', 'price_distribution_with_outliers.png')
plt.savefig(plot_1a_path, dpi=300)
plt.close()
print(f"✔ Saved Plot 1A to: {plot_1a_path}")

#Distribution of Airbnb Prices (Without Outliers <= 1500)
df_price_filtered = master_df[master_df['price'] <= 1500]

plt.figure(figsize=(10, 6))
plt.hist(df_price_filtered['price'], bins=40, color=PLOT_COLOR, edgecolor='white')
plt.title('Distribution of Airbnb Prices (x=1500)', fontsize=14, fontweight='bold')
plt.xlabel('Price per night (NZD)', fontsize=12)
plt.ylabel('Number of listings', fontsize=12)
plt.xlim(0, 1500)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

plot_1b_path = os.path.join('data', 'price_distribution_christchurch_without_outliers.png')
plt.savefig(plot_1b_path, dpi=300)
plt.close()
print(f"✔ Saved Plot 1B to: {plot_1b_path}")

# ===============================================================
# PLOT 2A: Listing Activity & Recency Status (Bar Chart)
# ===============================================================
# Define recency categories
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

# Align category order to match KNIME layout
recency_order = ['>365 Days', '0–30 Days', '91–365 Days', '31–90 Days']
recency_counts = master_df['recency_status'].value_counts().reindex(recency_order).fillna(0)

plt.figure(figsize=(10, 6))
bars = plt.bar(recency_counts.index, recency_counts.values, color=PLOT_COLOR, width=0.55)
plt.title('Listing Activity According To Date Difference', fontsize=14, fontweight='bold', loc='left')
plt.xlabel('Listing Recency Status', fontsize=12)
plt.ylabel('Number of Listings', fontsize=12)
plt.grid(axis='y', alpha=0.3)

# Annotate count values above each bar
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + (max(recency_counts.values) * 0.015),
                f'{int(height):,}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()

plot_2a_path = os.path.join('data', 'recency_status.png')
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

plot_2b_path = os.path.join('data', 'days_since_last_review.png')
plt.savefig(plot_2b_path, dpi=300)
plt.close()
print(f"✔ Saved Plot 2B to: {plot_2b_path}")

# ===============================================================
#Days Since Last Review (Top 10% Highest Reviewed Listings)
top_10_days_filtered = top_10_df[top_10_df['days_since_last_review'].between(0, 365)]

plt.figure(figsize=(10, 6))
plt.hist(top_10_days_filtered['days_since_last_review'], bins=30, color=PLOT_COLOR, edgecolor='white')
plt.title('Distribution of Days Since Last Review of Top 10% Christchurch Listings', fontsize=14, fontweight='bold', loc='left')
plt.xlabel('Days Since Last Review', fontsize=12)
plt.ylabel('Number of Listings', fontsize=12)
plt.xlim(0, 365)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

plot_3_path = os.path.join('data', 'top_10_percent_days_since_last_review.png')
plt.savefig(plot_3_path, dpi=300)
plt.close()
print(f"✔ Saved Plot 3 to: {plot_3_path}")
print("\n")