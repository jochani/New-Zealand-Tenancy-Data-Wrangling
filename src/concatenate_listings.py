import os
import glob
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def process_single_dataset(file_path: str) -> pd.DataFrame:
    # filename extraction
    filename = os.path.basename(file_path)
    
    # automatic file conversion from 'listings_October_2025.csv' -> 'October 2025'
    month_year = filename.replace('listings_', '').replace('.csv', '').replace('_', ' ')
    
    # dataset loaded
    df = pd.read_csv(file_path)
    
    # filtered to Christchurch City only
    df_filtered = df[df['neighbourhood_group'] == 'Christchurch City'].copy()
    
    # added column for month + year
    df_filtered['month_year'] = month_year
    
    return df_filtered

if __name__ == '__main__':
    data_folder = 'data/airbnb'
    
    # located file auto inside the 'data/' folder
    csv_files = glob.glob(os.path.join(data_folder, 'listings_*.csv'))
    
    processed_dfs = []
    
    print("\n--- Processing Files ---")
    for file_path in csv_files:
        df_processed = process_single_dataset(file_path)
        processed_dfs.append(df_processed)
        
        month_label = df_processed['month_year'].iloc[0] if not df_processed.empty else "Unknown"
        print(f"Processed {os.path.basename(file_path)} -> Label: '{month_label}' ({len(df_processed)} rows)")

    # concat all processed datasets
    master_df = pd.concat(processed_dfs, ignore_index=True)
    print(f"\nConcatenation complete. Total Christchurch rows: {len(master_df)}")

    # saved concat dataset to a new CSV file
    output_folder = os.path.join('output', 'processed')
    os.makedirs(output_folder, exist_ok=True)

    output_file = os.path.join(output_folder, 'all_listings.csv')
    master_df.to_csv(output_file, index=False)
    print(f"Combined dataset saved to: {output_file}\n")

    # summary statistics
    print("\n-- Missing Values Per Column --\n")
    print(master_df.isnull().sum())
    
    print("\n-- Numerical Summary Statistics --\n")
    print(master_df.describe().T)

    print("\n-- Categorical Summary Statistics --\n")
    print(master_df.describe(include=['object']).T)
    print("\n")