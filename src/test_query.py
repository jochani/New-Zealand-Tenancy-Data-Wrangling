import os
import requests

API_URL = "https://koordinates.com/services/query/v1/vector.json"
API_KEY = "59d9b0cf8f4f4aa0a3b83b563e628ad7"
SA2_LAYER_ID = "123515"

# Sample Christchurch coordinates
lat = -43.50961
lon = 172.65552

params = {
    "key": API_KEY,
    "layer": SA2_LAYER_ID,
    "y": lat,
    "x": lon,
    "max_results": 1
}

response = requests.get(API_URL, params=params)
print(f"HTTP Status: {response.status_code}")

# Ensure output directory exists
os.makedirs("output", exist_ok=True)
summary_path = "output/summaries/test_query_summary.txt"

if response.status_code == 200:
    result = response.json()
    layers = result.get("vectorQuery", {}).get("layers", {}).get(SA2_LAYER_ID, {})
    features = layers.get("features", [])
    
    if features:
        props = features[0].get("properties", {})
        loc_id = props.get("SA22026_V1_00")
        loc_name = props.get("SA22026_V1_00_NAME")
        
        # Write summary to a text file
        summary_content = f"""=== Koordinates API Test Query Summary ===
Status: SUCCESS
HTTP Code: {response.status_code}
Coordinates Tested: Lat {lat}, Lon {lon}
Extracted Location ID: {loc_id}
Extracted Location Name: {loc_name}
-------------------------------------------
Raw Response:
{result}
"""
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_content)
            
        print(f"Successfully extracted and saved summary to {summary_path} -> ID: {loc_id}, Name: {loc_name}")
    else:
        print("Response received, but no features found for these coordinates.")
else:
    error_content = f"=== API Test Query Failed ===\nHTTP Code: {response.status_code}\nError: {response.text}"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(error_content)
    print(f"Error: API failed. Saved error log to {summary_path}")