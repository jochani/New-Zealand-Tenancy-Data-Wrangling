# DATA422 – Data Pipeline Design Principles

## Christchurch Airbnb and Rental Bond Data Wrangling Project

**Course:** DATA422 – Data Wrangling  
**Project:** New Zealand Tenancy Data Wrangling  
**AI used:** ChatGPT by OpenAI (GPT-5.6 Sol)

---

## Purpose

This document describes the design principles used in our Christchurch
Airbnb and rental bond data-wrangling pipeline.

ChatGPT was used to help construct the initial version of this document.
The generated document was then manually compared with our actual project
structure, Python scripts, generated outputs, and intended workflow.

Where the proposed design did not match the implementation, either the
code/project organisation was corrected or the document was changed so
that it accurately describes the current pipeline.

The overall aim of the pipeline is to prepare and integrate Christchurch
Airbnb data with New Zealand rental bond data so that short-term
accommodation activity can be compared with the long-term rental market.

---

# 1. Pipeline Inputs

The pipeline uses three main sources of information.

## 1.1 Airbnb Data

The primary input consists of monthly Airbnb listing datasets obtained
from Inside Airbnb.

Our analysis focuses on Christchurch City and covers the study period:

**October 2025 to June 2026**

The Airbnb data contains variables used throughout the project, including:

- listing ID
- listing name
- host ID
- latitude
- longitude
- neighbourhood
- neighbourhood group
- room type
- price
- number of reviews
- last review date
- reviews in the last twelve months

The original Airbnb files are retained as source data and are not
intentionally overwritten by the processing pipeline.

---

## 1.2 Rental Bond Data

The second major input is New Zealand rental bond data.

Important variables include:

- TimeFrame
- Location Id
- Dwelling Type
- Number Of Beds
- Total Bonds
- Active Bonds
- Closed Bonds
- Median Rent
- Geometric Mean Rent
- Upper Quartile Rent
- Lower Quartile Rent

The rental bond data provides information about the long-term rental
market that can be compared with Airbnb activity.

---

## 1.3 Geographic / SA2 Information

The Airbnb data contains latitude and longitude coordinates, while the
rental bond data uses geographic location identifiers.

SA2 (Statistical Area 2) information is therefore used to create a common
geographic basis for the datasets.

The project uses geographic lookup information to assign Airbnb
observations to SA2 areas.

---

# 2. Pipeline Outputs

Generated datasets are stored separately from the original source data.

The main processed outputs currently include:

### Cleaned Airbnb data

`output/processed/christchurch_airbnb_clean.csv.gz`

and

`output/processed/christchurch_airbnb_clean.xlsx`

These contain the cleaned Christchurch Airbnb observations used in later
pipeline stages.

### Airbnb data with SA2 information

`output/processed/christchurch_airbnb_clean_with_sa2.xlsx`

This contains cleaned Airbnb observations after geographic SA2
information has been added.

### Cleaned rental bond data

`output/processed/rental_bonds_clean.csv`

This contains rental bond information prepared for integration with the
Airbnb data.

### Joined Airbnb and rental bond data

`output/processed/christchurch_airbnb_bonds_joined.csv`

This is an important integrated dataset produced after Airbnb observations
and rental bond information are aligned and joined.

### Unmatched observations

`output/processed/airbnb_unmatched_bonds.csv`

This output allows observations that could not be matched during the
integration stage to be examined rather than silently discarded.

### SA2 processing support files

The geographic processing stage also produces:

`output/processed/koordinates_sa2_checkpoint.csv`

and

`output/processed/koordinates_failed_queries.csv`

The checkpoint file supports the SA2 assignment process, while the failed
query file makes unsuccessful geographic lookups visible for investigation.

The pipeline also produces analytical summaries and comparisons from the
processed datasets.

---

# 3. Main Pipeline Steps

The current pipeline can be summarised as:

Airbnb source data
        |
        v
Clean and filter Airbnb data
        |
        v
Combine Christchurch observations
        |
        v
Assign SA2 geographic areas
        |
        v
Airbnb data with SA2
        |
        +--------------------------+
                                   |
Rental bond source data            |
        |                          |
        v                          |
Clean rental bond data             |
        |                          |
        +------------+-------------+
                     |
                     v
        Align geographic/time information
                     |
                     v
          Join Airbnb and bond data
                     |
                     v
              Validate results
                     |
                     v
             Analysis / summaries


## Step 1 – Load Airbnb Data

The pipeline reads the Airbnb source files from the project data
directories.

Relative paths are used instead of paths that depend on a particular
user's computer.

For example:

```python
Path("data/airbnb")