# New-Zealand-Tenancy-Data-Wrangling
A uni repostory for the course DATA422

## Dataset

### Source

This project uses the New Zealand Airbnb listings dataset published by Inside Airbnb.

- **Dataset:** listings.csv
- **Geographic Coverage:** New Zealand
- **Dataset Date:** 19 June 2026
- **Source:** https://insideairbnb.com/get-the-data/
- **Purpose:** Summary information and metrics for Airbnb listings suitable for data analysis and visualisation.

The dataset is stored locally on each team member's computer and is **not committed to GitHub** because of its size.


## Important Columns

| Column | Data Type | Description | Example |
|---------|-----------|-------------|---------|
| id | Integer | Unique identifier for each Airbnb listing | 12345678 |
| name | String | Name or title of the listing | Modern City Apartment |
| host_id | Integer | Unique identifier of the host | 987654 |
| host_name | String | Name of the host | John |
| neighbourhood | String | Larger geographic grouping, where available | Riccarton |
| neighbourhood_group | String | Area or local authority associated with the listing | Christchurch City |
| latitude | Decimal (Float) | Geographic latitude of the property | -43.5321 |
| longitude | Decimal (Float) | Geographic longitude of the property | 172.6362 |
| room_type | Categorical (String) | Type of accommodation | Entire home/apt |
| price | Decimal (Currency) | Nightly rental price (NZD) | 185.00 |
| minimum_nights | Integer | Minimum nights required for booking | 2 |
| availability_365 | Integer | Number of available days in the next 365 days | 210 |
| number_of_reviews | Integer | Total reviews received | 145 |
| last_review | Date | Date of the latest review | 2026-05-12 |
| reviews_per_month | Decimal (Float) | Average monthly reviews | 2.34 |
| number_of_reviews_ltm | Integer | Reviews received in the last 12 months | 28 |
| calculated_host_listings_count | Integer | Total listings managed by the host | 5 |
| license | String | Property licence or registration number (if available) | ABC12345 |