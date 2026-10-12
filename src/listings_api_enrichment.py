import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Configuration & Paths ---
INPUT_FILE = "output/processed/christchurch_listings_clean.csv"
OUTPUT_FILE = "output/data_sa2/airbnb_listings_spatial.csv"

API_URL = "https://koordinates.com/services/query/v1/vector.json"  # URL used from previous test_query script summary
API_KEY = "59d9b0cf8f4f4aa0a3b83b563e628ad7" # My API key generated from Koordinates 
SA2_LAYER_ID = "123515" # Statistical Area 2 2026 layer ID

# --- Setup Requests Session with Retries (In case a row misses loc name and id) ---
def create_robust_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

session = create_robust_session()

# --- Spatial Query Function for Individual Listings ---
def fetch_spatial_data(row_idx, lat, lon):
    """Queries the Koordinates API for a given latitude and longitude pair."""
    params = {
        "key": API_KEY,
        "layer": SA2_LAYER_ID,
        "y": lat,
        "x": lon,
        "max_results": 1
    }
    
    try:
        response = session.get(API_URL, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            
            layers = result.get("vectorQuery", {}).get("layers", {}).get(SA2_LAYER_ID, {})
            features = layers.get("features", [])
            
            if features:
                props = features[0].get("properties", {})
                location_id = props.get("SA22026_V1_00", None)
                location_name = props.get("SA22026_V1_00_NAME", None)
                return row_idx, location_id, location_name
    except Exception:
        pass
    
    return row_idx, None, None

# --- Main Execution ---
def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Input file not found at {INPUT_FILE}. Please check your path.")
    
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows from {INPUT_FILE}.")
    
    print("Starting parallel spatial enrichment using ThreadPoolExecutor...")
    
    location_ids = [None] * len(df)
    location_names = [None] * len(df)
    
    # Using ThreadPoolExecutor for concurrent requests
    max_workers = 10
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_spatial_data, idx, row['latitude'], row['longitude']): idx 
            for idx, row in df.iterrows()
        }
        
        completed = 0
        for future in as_completed(futures):
            row_idx, loc_id, loc_name = future.result()
            location_ids[row_idx] = loc_id
            location_names[row_idx] = loc_name
            
            completed += 1
            if completed % 100 == 0 or completed == len(df):
                print(f"Processed {completed}/{len(df)} listings...")

    # Assign results back to dataFrame
    df['location_id'] = location_ids
    df['location_name'] = location_names
    
    # Quality check for null mappings
    null_count = df['location_id'].isna().sum()
    print(f"Spatial enrichment complete. Unmapped records: {null_count}/{len(df)}")
    
    # Ensure output directory exists and save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Enriched dataset successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()