import pandas as pd
import numpy as np

# =====================================================
# FILE PATHS (MATCH YOUR PROJECT STRUCTURE)
# =====================================================
GTFS_FILE = "data/processed/pune_gtfs_traffic_30days_encoded.csv"
RIDERSHIP_FILE = "data/raw/metro_ridership.csv"
OUTPUT_FILE = "data/processed/gtfs_with_demand.csv"

# =====================================================
# STEP 1: LOAD DATA
# =====================================================
gtfs_df = pd.read_csv(GTFS_FILE)
metro_df = pd.read_csv(RIDERSHIP_FILE)

print("GTFS rows:", len(gtfs_df))
print("Metro ridership rows:", len(metro_df))

# =====================================================
# STEP 2: PREPARE METRO RIDERSHIP DATA
# =====================================================
metro_df["Date"] = pd.to_datetime(metro_df["Date"], format="%d-%m-%Y")
metro_df = metro_df[["Date", "Total Ridership"]]
metro_df.rename(columns={"Date": "date"}, inplace=True)

avg_ridership = metro_df["Total Ridership"].mean()
metro_df["demand_weight"] = metro_df["Total Ridership"] / avg_ridership

# =====================================================
# STEP 3: MERGE AT DATE LEVEL
# =====================================================
gtfs_df["date"] = pd.to_datetime(gtfs_df["date"])

combined_df = gtfs_df.merge(
    metro_df,
    on="date",
    how="left"
)

# =====================================================
# STEP 4: HANDLE MISSING RIDERSHIP DATES
# =====================================================
combined_df["demand_weight"] = combined_df["demand_weight"].fillna(1.0)
combined_df["Total Ridership"] = combined_df["Total Ridership"].fillna(avg_ridership)

# =====================================================
# STEP 5: CLEAN route_id NaNs
# =====================================================
combined_df["route_id"] = combined_df["route_id"].fillna(-1)

# =====================================================
# STEP 6: CLEAN SRI NaNs (SAFE, WARNING-FREE)
# =====================================================
global_sri_median = combined_df["SRI"].median()

def fill_sri(group):
    if group.isna().all():
        return group.fillna(global_sri_median)
    else:
        return group.fillna(group.median())

combined_df["SRI"] = (
    combined_df
    .groupby("route_id")["SRI"]
    .transform(fill_sri)
)

# =====================================================
# STEP 7: CONGESTION IMPACT FACTOR
# =====================================================
congestion_factor_map = {
    0: 1.00,
    1: 0.90,
    2: 0.75,
    3: 0.60
}

combined_df["congestion_factor"] = combined_df["congestion_level"].map(
    congestion_factor_map
)

# =====================================================
# STEP 8: ESTIMATE PASSENGER DEMAND
# =====================================================
combined_df["estimated_passenger_demand"] = (
    combined_df["number_of_trips"]
    * combined_df["demand_weight"]
    * combined_df["congestion_factor"]
)

# =====================================================
# 🔥 STEP 9: REMOVE ALL REMAINING NaNs (NEW STEP)
# =====================================================
print("Rows before NaN removal:", len(combined_df))

combined_df = combined_df.dropna()

print("Rows after NaN removal:", len(combined_df))
print("Rows removed:", len(gtfs_df) - len(combined_df))

# =====================================================
# STEP 10: FINAL COLUMN SELECTION
# =====================================================
final_df = combined_df[
    [
        "date",
        "hour",
        "is_weekend",
        "route_id",
        "stop_id_from",
        "stop_id_to",
        "speed",
        "SRI",
        "congestion_level",
        "number_of_trips",
        "Total Ridership",
        "demand_weight",
        "estimated_passenger_demand"
    ]
]

# =====================================================
# STEP 11: SAVE OUTPUT
# =====================================================
final_df.to_csv(OUTPUT_FILE, index=False)

print("✅ GTFS + Ridership integrated dataset created successfully (NaN-free)")
print("Saved at:", OUTPUT_FILE)

# =====================================================
# FINAL CLEANUP: REMOVE ALL ROWS WITH ANY NaN
# =====================================================
print("Rows before removing NaNs:", len(combined_df))

combined_df = combined_df.dropna()

print("Rows after removing NaNs:", len(combined_df))
print("Rows removed:", 2007390 - len(combined_df))
