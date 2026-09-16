# New-Zealand-Tenancy-Data-Wrangling
A uni repostory for the course DATA422

## Dataset 1

### Source

This project uses the New Zealand Airbnb listings dataset published by Inside Airbnb.

- **Dataset:** listings.csv
- **Geographic Coverage:** New Zealand
- **Dataset Date:** 19 June 2026 (Quarterly)
- **Source:** https://insideairbnb.com/get-the-data/
- **Purpose:** Summary information and metrics for Airbnb listings suitable for data analysis and visualisation.

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


## Dataset 2

**Dataset:** Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv
- **Dataset Date:** January 2020 to April 2026
- **Geographic Coverage:** New Zealand 
- **Source:** https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/
- **Purpose:** Detailed quarterly tenancy bond statistics and rental price metrics for New Zealand residential properties, categorized by location, dwelling type, and bedroom count.

## Important Columns

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| **TimeFrame** | Date (`YYYY-MM-DD`) | Quarter start date (`2025-10-01` = Q4 2025). |
| **Location Id** | Numeric | Territorial Authority or Statistical Area code (Statistics NZ / Tenancy Services). |
| **Dwelling Type** | Categorical | Property classification (`House`, `Apartment`, `Flat`, `Room`, `Boarding House`, `ALL`). |
| **Number Of Beds** | Categorical / Numeric | Bedroom count (`1`, `2`, `3`, `4`, `5+`, `ALL`). |
| **Total Bonds** | Integer | New tenancy bonds lodged during the quarter. |
| **Active Bonds** | Integer | Cumulative active tenancy bonds held at quarter end. |
| **Closed Bonds** | Integer | Tenancy bonds closed or refunded during the quarter. |
| **Median Rent** | Currency ($NZD) | Median weekly rent recorded for new bonds lodged in that period. |
| **Geometric Mean Rent** | Currency ($NZD) | Log-transformed mean weekly rent (minimizes outlier bias). |
| **Upper Quartile Rent** | Currency ($NZD) | 75th percentile weekly rental price for the region. |
| **Lower Quartile Rent** | Currency ($NZD) | 25th percentile weekly rental price for the region. |
| **Log Std Dev Weekly Rent** | Float | Standard deviation of the log of weekly rents (measures price dispersion). |
