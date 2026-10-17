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
| `id` | Integer | Unique identifier for each Airbnb listing | 12345678 |
| `name` | String | Name or title of the listing | Modern City Apartment |
| `host_id` | Integer | Unique identifier of the host | 987654 |
| `host_name` | String | Name of the host | John |
| `neighbourhood` | String | Larger geographic grouping, where available | Riccarton |
| `neighbourhood_group` | String | Area or local authority associated with the listing | Christchurch City |
| `latitude` | Decimal (Float) | Geographic latitude of the property | -43.5321 |
| `longitude` | Decimal (Float) | Geographic longitude of the property | 172.6362 |
| `room_type` | Categorical (String) | Type of accommodation | Entire home/apt |
| `price` | Decimal (Currency) | Nightly rental price (NZD) | 185.00 |
| `minimum_nights` | Integer | Minimum nights required for booking | 2 |
| `availability_365` | Integer | Number of available days in the next 365 days | 210 |
| `number_of_reviews` | Integer | Total reviews received | 145 |
| `last_review` | Date | Date of the latest review | 2026-05-12 |
| `reviews_per_month` | Decimal (Float) | Average monthly reviews | 2.34 |
| `number_of_reviews_ltm` | Integer | Reviews received in the last 12 months | 28 |
| `calculated_host_listings_count` | Integer | Total listings managed by the host | 5 |
| `license` | String | Property licence or registration number (if available) | ABC12345 |

## Data Cleaning & Pre-processing:

The combined dataset contained **28,795 observations** covering **October 2025 to June 2026**. No **duplicate listing-month combinations** were identified.

**Four columns were removed:** 
  * Dropped `license` since there are 100% missing values across all snapshots
  * Dropped `neighbourhood_group` because it contained one redundant static text `"Christchurch City"` after filtering out the concatenated dataset for Christchurch City only.
  * Dropped `last_review` and `reviews_per_month` because review activity is outside the focus of the planned rental-price and property-availability analysis.

**Observations:**
  * `latitude`, `longitude` and `neighbourhood` were retained for geographic analysis.
  * The single missing `host_name` was recovered from another observation with the same `host_id`.
  * All 37 missing `minimum_nights` values were recovered using the median observed value for the same listing across other monthly snapshots.
  * Consequently, no observations were removed during these operations.

## Dataset 2

**Dataset:** Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv
- **Dataset Date:** January 2020 to April 2026 (Quarterly)
- **Geographic Coverage:** New Zealand 
- **Source:** https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/
- **Purpose:** Detailed quarterly tenancy bond statistics and rental price metrics for New Zealand residential properties, categorized by location, dwelling type, and bedroom count.

## Important Columns

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `TimeFrame` | Date (`YYYY-MM-DD`) | Quarter start date (`2025-10-01` = Q4 2025). |
| `Location Id` | Numeric | Territorial Authority or Statistical Area code (Statistics NZ / Tenancy Services). |
| `Dwelling Type` | Categorical | Property classification (`House`, `Apartment`, `Flat`, `Room`, `Boarding House`, `ALL`). |
| `Number Of Beds` | Categorical / Numeric | Bedroom count (`1`, `2`, `3`, `4`, `5+`, `ALL`). |
| `Total Bonds` | Integer | New tenancy bonds lodged during the quarter. |
| `Active Bonds` | Integer | Cumulative active tenancy bonds held at quarter end. |
| `Closed Bonds` | Integer | Tenancy bonds closed or refunded during the quarter. |
| `Median Rent` | Currency ($NZD) | Median weekly rent recorded for new bonds lodged in that period. |
| `Geometric Mean Rent` | Currency ($NZD) | Log-transformed mean weekly rent (minimizes outlier bias). |
| `Upper Quartile Rent` | Currency ($NZD) | 75th percentile weekly rental price for the region. |
| `Lower Quartile Rent` | Currency ($NZD) | 25th percentile weekly rental price for the region. |
| `Log Std Dev Weekly Rent` | Float | Standard deviation of the log of weekly rents (measures price dispersion). |

#### Observations and Changes

1. **Updated reporting period:** The downloaded dataset is labelled as covering Q1 2020 to Q3 2026. However, the current analysis uses Q4 2025, Q1 2026, and Q2 2026 to align with the available rental bond comparison periods.

2. **Quarterly rather than monthly reporting:** Unlike the Airbnb dataset, which contains monthly observations, rental bond statistics are reported quarterly. Airbnb months were mapped to their corresponding quarters to enable temporal matching.

3. **Geographic alignment:** Rental bond records use `Location Id` identifiers, which were standardised and matched with the Statistical Area 2 (SA2) identifiers assigned to Airbnb listings.

4. **Filtering and cleaning:** Records were filtered to Christchurch City and the selected quarters. The analysis retained aggregate records where `Dwelling Type = ALL` and `Number Of Beds = ALL`, avoiding comparisons across overlapping property categories.

5. **Data transformation:** The `TimeFrame` column was converted into a standard date format, location identifiers were normalised, and `Median Nightly Rent` was calculated as `Median Rent / 7` to support a descriptive comparison with Airbnb nightly prices.

6. **Dataset size:** The source dataset contained 226,080 rows and 12 columns. After filtering and transformation, the cleaned dataset contained 4,868 rows and 14 columns, covering 1,807 unique locations.

7. **Integration and unmatched records:** The rental bond dataset was joined with the Airbnb dataset using SA2 identifiers and quarter keys. Of 35,796 Airbnb observations, 21,946 matched rental bond records (61.31%), while 13,850 remained unmatched.

8. **July-August 2026 limitation:** The updated Airbnb dataset includes July and August 2026, but the current cleaned rental bond comparison does not include Q3 2026. These Airbnb observations are preserved through a left join, with unavailable rental bond attributes represented as missing values.

#### Important Consideration

Airbnb prices represent short-term accommodation, whereas rental bond statistics represent longer-term residential rentals. Dividing weekly median rent by seven provides a nightly-equivalent comparison but does not make the two markets directly equivalent.

---

## Team Contributions and Development Branches

This project was developed collaboratively by three team members. Each member worked on their own GitHub branch to maintain individual contributions, support independent development, and facilitate code review before integration into the main repository.

| Team Member | GitHub Branch |
|---|---|
| Jayant Ochani | [`jay_deliverable_7`](../../tree/jay_deliverable_7) 
| Carolina Faka'osi | [`carolina-deliverable3`](../../tree/carolina-deliverable3) 
| S M Tahmid Shahriar Arpon | [`tahmid_blip`](../../tree/tahmid_blip) 

### Branch Management

- **`main`** - Final integrated version of the project, used for submission.
- **Individual branches** - Preserve each team member's development work, commits, and implementation history.
- **Collaboration** - Team members developed and reviewed their contributions before integrating agreed changes into the main branch.

### Project Execution

The final automated data wrangling pipeline can be executed from the repository root (`main`) using:

```bash
python run_pipeline.py
```

The pipeline processes the Airbnb and rental bond datasets, performs cleaning and integration, generates SQLite outputs, and updates the analytical plots.

### Contribution History

Individual contributions and development progress can be reviewed through each team member's GitHub branch and commit history.