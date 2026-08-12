#importing csv
import pandas as pd

# (1) importing listings_19062026.csv
listings_19_06_2026 = pd.read_csv("listings_19062026.csv")
print(listings_19_06_2026.head())

#display listings_19062026.csv columns
print(listings_19_06_2026.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_19_06_2026['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_19_06_2026 = listings_19_06_2026[listings_19_06_2026['neighbourhood_group'] == 'Christchurch City']
print(listings_19_06_2026)

#add new column for month and year
listings_19_06_2026['month_year'] = '06-2026'
listings_19_06_2026.to_csv('listings_19_06_2026.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_19_06_2026.month_year)

#-----automation loop-----

#files = ["listings_23052026.csv", "listings_16042026.csv", "listings_17032026.csv", "listings_13022026.csv", "listings_16012026.csv", "listings_11122025.csv", "listings_07112025.csv", "listings_05102025.csv", "listings_06092025.csv", "listings_03082025.csv"]

#importing all listings csv files
#for file in files:
    #df_1 = pd.read_csv(file)
    #print(df_1.shape)

#repeating the same steps for the rest of the listings csvs
# (2) importing listings_23052026.csv
import pandas as pd
listings_23_05_2026 = pd.read_csv("listings_23052026.csv")
print(listings_23_05_2026.head())

#display listings_23052026.csv columns
print(listings_23_05_2026.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_23_05_2026['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_23_05_2026 = listings_23_05_2026[listings_23_05_2026['neighbourhood_group'] == 'Christchurch City']
print(listings_23_05_2026)

#add new column for month and year
listings_23_05_2026['month_year'] = '05-2026'
listings_23_05_2026.to_csv('listings_23_05_2026.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_23_05_2026.month_year)

# (3) importing listings_16042026.csv
import pandas as pd
listings_16_04_2026 = pd.read_csv("listings_16042026.csv")
print(listings_16_04_2026.head())

#display listings_16042026.csv columns
print(listings_16_04_2026.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_16_04_2026['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_16_04_2026 = listings_16_04_2026[listings_16_04_2026['neighbourhood_group'] == 'Christchurch City']
print(listings_16_04_2026)

#add new column for month and year
listings_16_04_2026['month_year'] = '04-2026'
listings_16_04_2026.to_csv('listings_16_04_2026.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_16_04_2026.month_year)

# (4) importing listings_17032026.csv
import pandas as pd
listings_17_03_2026 = pd.read_csv("listings_17032026.csv")
print(listings_17_03_2026.head())

#display listings_17032026.csv columns
print(listings_17_03_2026.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_17_03_2026['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_17_03_2026 = listings_17_03_2026[listings_17_03_2026['neighbourhood_group'] == 'Christchurch City']
print(listings_17_03_2026)

#add new column for month and year
listings_17_03_2026['month_year'] = '03-2026'
listings_17_03_2026.to_csv('listings_17_03_2026.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_17_03_2026.month_year)

# (5) importing listings_13022026.csv
import pandas as pd
listings_13_02_2026 = pd.read_csv("listings_13022026.csv")
print(listings_13_02_2026.head())

#display listings_13022026.csv columns
print(listings_13_02_2026.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_13_02_2026['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_13_02_2026 = listings_13_02_2026[listings_13_02_2026['neighbourhood_group'] == 'Christchurch City']
print(listings_13_02_2026)

#add new column for month and year
listings_13_02_2026['month_year'] = '02-2026'
listings_13_02_2026.to_csv('listings_13_02_2026.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_13_02_2026.month_year)

# (6) importing listings_16012026.csv
import pandas as pd
listings_16_01_2026 = pd.read_csv("listings_16012026.csv")
print(listings_16_01_2026.head())

#display listings_16012026.csv columns
print(listings_16_01_2026.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_16_01_2026['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_16_01_2026 = listings_16_01_2026[listings_16_01_2026['neighbourhood_group'] == 'Christchurch City']
print(listings_16_01_2026)

#add new column for month and year
listings_16_01_2026['month_year'] = '01-2026'
listings_16_01_2026.to_csv('listings_16_01_2026.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_16_01_2026.month_year)

# (7) importing listings_11122025.csv
import pandas as pd
listings_11_12_2025 = pd.read_csv("listings_11122025.csv")
print(listings_11_12_2025.head())

#display listings_11122025.csv columns
print(listings_11_12_2025.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_11_12_2025['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_11_12_2025 = listings_11_12_2025[listings_11_12_2025['neighbourhood_group'] == 'Christchurch City']
print(listings_11_12_2025)

#add new column for month and year
listings_11_12_2025['month_year'] = '12-2025'
listings_11_12_2025.to_csv('listings_11_12_2025.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_11_12_2025.month_year)

# (8) importing listings_07112025.csv
import pandas as pd
listings_07_11_2025 = pd.read_csv("listings_07112025.csv")
print(listings_07_11_2025.head())

#display listings_07112025.csv columns
print(listings_07_11_2025.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_07_11_2025['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_07_11_2025 = listings_07_11_2025[listings_07_11_2025['neighbourhood_group'] == 'Christchurch City']
print(listings_07_11_2025)

#add new column for month and year
listings_07_11_2025['month_year'] = '11-2025'
listings_07_11_2025.to_csv('listings_07_11_2025.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_07_11_2025.month_year)

# (9) importing listings_05102025.csv
import pandas as pd
listings_05_10_2025 = pd.read_csv("listings_05102025.csv")
print(listings_05_10_2025.head())

#display listings_05102025.csv columns
print(listings_05_10_2025.columns)

#print column 'neighbourhood_group' values to find name used for Christchurch
print(listings_05_10_2025['neighbourhood_group'].unique())

#filter for listings in 'Christchurch City' only
listings_05_10_2025 = listings_05_10_2025[listings_05_10_2025['neighbourhood_group'] == 'Christchurch City']
print(listings_05_10_2025)

#add new column for month and year
listings_05_10_2025['month_year'] = '10-2025'
listings_05_10_2025.to_csv('listings_05_10_2025.csv', index=False)
print(f"New column 'month_year' added successfully!")

#view new column 'month_year'
print(listings_05_10_2025.month_year)

#concatenate all prepared csvs into one Christchurch file
import glob

listings_files = ["listings_19_06_2026.csv", 
                  "listings_23_05_2026.csv",
                  "listings_16_04_2026.csv",
                  "listings_17_03_2026.csv",
                  "listings_13_02_2026.csv",
                  "listings_16_01_2026.csv",
                  "listings_11_12_2025.csv",
                  "listings_07_11_2025.csv",
                  "listings_05_10_2025.csv"
                  ]
print("Processing files...")

#df = pd.concat((pd.read_csv(f) for f in listings_files),
               #ignore_index=True)

all_dfs = []

for filename in listings_files:

    parts = filename.replace(".csv", "").split("_")

    day = parts[-3]
    month = parts[-2]
    year = parts[-1]

    month_year = f"{month}_{year}"

    publish_date = pd.to_datetime(
        f"{day}/{month}/{year}",
        format="%d/%m/%Y"
    )

    temp_df = pd.read_csv(filename)

    temp_df["month_year"] = month_year
    temp_df["publish_date"] = publish_date

    all_dfs.append(temp_df)

df = pd.concat(all_dfs, ignore_index=True)

print("Concatenation complete")
print(f"Rows: {len(df)}")

df.to_csv("Christchurch_merged_listings_2025_2026.csv", index=False)


#display results in terminal
print(df.head()) # first 5 rows
print(df.shape) # rows, columns
print("Christchurch listings (2025-2026) merged and saved successfully!")

#produce suitable summary statistics

# (1) displaying numerical summary statistics
print("\n=== NUMERICAL SUMMARY STATISTICS ===")
print(df.describe().T.to_string())

# (2) displaying categorical summary statistics
print("\n=== CATEGORICAL SUMMARY STATISTICS ===")
print(df.describe(include='object').T.to_string())

# (3) displaying number of missing values per column
print("\n=== MISSING VALUES SUMMARY STATISTICS ===")
missing_summary = df.isnull().sum().to_frame(name='missing_values')
print(missing_summary.to_string())

#saving all results in a new excel file 'summary_statistics.txt'
with open("summary_statistics.txt", "w", encoding="utf-8") as f:
 f.write("=== NUMERICAL SUMMARY STATISTICS ===\n")
 f.write(df.describe().T.to_string())

 f.write("\n\n=== CATEGORICAL SUMMARY STATISTICS ===\n")
 f.write(df.describe(include='object').T.to_string())

 f.write("\n\n=== MISSING VALUES SUMMARY ===\n")
 f.write(missing_summary.to_string())

#reproduce workflows and plots from Deliverable 2:

#clean up the csv eg. missing values
df_cleaned = df.dropna(subset=['price'])

print(df_cleaned['price'].dtype)

# (1) plot distribution of price as a histogram for only Christchurch City
#importing necessary libraries
import matplotlib.pyplot as plt
import numpy as np

#plot histogram using the 'price' column
plt.hist(df_cleaned['price'], bins=400, edgecolor='black', color='skyblue')

plt.xlim(0,4500) #defining min and max values to use for graph

plt.title('Price Distribution of Airbnb Listings in Christchurch City') #title
plt.xlabel('Price (NZD)') #x-label
plt.ylabel('Number of Listings') #y-label

#display the histogram
plt.show()
plt.close()

# (2) calculate how long ago the last review was in days (difference between scrape/publish date and last review date) & plot new feature
#making sure the 'last_review' column is a date

#extracting the dates from filename instead of the above method
#filename = file.stem
#df["publish_date"] = publish_date
# Example: listings_16_01_2026

#for filename in listings_files:
   # parts = filename.split("_")

   # day = parts[-3]
   # month = parts[-2]
    #year = parts[-1].replace(".csv", "")

   # month_year = f"{month}_{year}"

   # publish_date = pd.to_datetime(
       # f"{day}/{month}/{year}",
      #  format="%d/%m/%Y"
   # )

   # df["publish_date"] = publish_date

   # print(month_year, [publish_date])

#create new column published_date
#df["publish_date"] = publish_date


#df["month_year"] = month_year
#df["publish_date"] = publish_date

#print(df.columns.tolist())

#making sure the last_revies column is a date_time
df["last_review"] = pd.to_datetime(
    df["last_review"],
    format="%Y-%m-%d"
)

print("\n=== DIFFERENCE BETWEEN SCRAPE/PUBLISH DATE AND LAST REVIEW DATE ===")
#calculate the last review date
df["days_since_review"] = (
    df["publish_date"] - df["last_review"]
).dt.days

print(df[["last_review", "publish_date", "days_since_review"]])

#since I had a couple negative values in the days_since_review column, I'm checking to see why
print(
    df[df["days_since_review"] < 0][
        ["last_review", "publish_date", "days_since_review"]
    ].head(20)
)

print(df["publish_date"].value_counts())

print(sorted(df["publish_date"].unique()))

print((df["days_since_review"] < 0).sum())

print(
    (df["days_since_review"] < 0).mean() * 100
)

#print(df["days_since_review"].describe())





# (3) find how many properties get the highest numbers of reviews in Christchurch
print("\n=== TOP 10% MOST REVIEWED PROPERTIES IN CHRISTCHURCH ===")

#calculating top 10% threshold
threshold = df_cleaned['number_of_reviews'].quantile(0.90)

#filter for properties that meet or exceed top 10% mark
top_10 = df_cleaned[df_cleaned['number_of_reviews'] >= threshold]

#display top 10% most reviewed properties in CHC
print(f"Number of properties in the top 10%: {threshold} properties")
print(top_10)










