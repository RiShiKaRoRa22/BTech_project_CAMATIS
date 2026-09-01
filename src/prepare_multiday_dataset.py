import pandas as pd
import numpy as np

# =====================================================
# CONFIGURATION
# =====================================================
INPUT_FILE = "data/raw/pune_gtfs_traffic_data.csv"
OUTPUT_FILE = "data/processed/pune_gtfs_traffic_30days_encoded.csv"

START_DATE = "2024-01-01"
NUM_DAYS = 30

# =====================================================
# STEP 1: LOAD BASE DATA (1 DAY)
# =====================================================
df = pd.read_csv(INPUT_FILE)
print(f"Loaded base dataset with {len(df)} rows")

# =====================================================
# STEP 2: FEATURE EXTRACTION & NORMALIZATION
# =====================================================

# Convert arrival_time → extract hour
df["arrival_time"] = pd.to_datetime(df["arrival_time"], format="%H:%M:%S")
df["hour"] = df["arrival_time"].dt.hour

# Extract route_id from trip_id
# Example: NORMAL_333_Pune Station... → 333
df["route_id"] = df["trip_id"].str.extract(r"NORMAL_(\d+)")

# Normalize column names
df.rename(
    columns={
        "Degree_of_congestion": "congestion_label",
        "Number_of_trips": "number_of_trips"
    },
    inplace=True
)

# Drop unused columns
df.drop(columns=["arrival_time"], inplace=True)

# =====================================================
# STEP 3: TEMPORAL EXPANSION (MULTI-DAY)
# =====================================================
date_range = pd.date_range(start=START_DATE, periods=NUM_DAYS)

expanded = []
for date in date_range:
    temp = df.copy()
    temp["date"] = date
    expanded.append(temp)

df_full = pd.concat(expanded, ignore_index=True)
print(f"Expanded dataset to {len(df_full)} rows")

# =====================================================
# STEP 4: ADD WEEKDAY / WEEKEND
# =====================================================
df_full["day_type"] = df_full["date"].dt.weekday.apply(
    lambda x: "Weekend" if x >= 5 else "Weekday"
)

# =====================================================
# STEP 5: REALISTIC TRAFFIC VARIATION
# =====================================================

# Peak hour slowdown
peak_hours = [8, 9, 18, 19]
df_full.loc[df_full["hour"].isin(peak_hours), "speed"] *= 0.90

# Weekend smoother traffic
df_full.loc[df_full["day_type"] == "Weekend", "speed"] *= 1.10

# Heavy congestion penalty
df_full.loc[
    df_full["congestion_label"] == "Heavy congestion", "speed"
] *= 0.85

# =====================================================
# STEP 6: RECOMPUTE SRI
# =====================================================
free_flow_speed = df_full.groupby("route_id")["speed"].transform("max")
df_full["SRI"] = (free_flow_speed - df_full["speed"]) / free_flow_speed

# =====================================================
# STEP 7: ENCODING (IMPORTANT PART)
# =====================================================

# Ordinal encoding for congestion
congestion_map = {
    "Very smooth": 0,
    "Smooth": 1,
    "Mild congestion": 2,
    "Heavy congestion": 3
}
df_full["congestion_level"] = df_full["congestion_label"].map(congestion_map)

# Binary encoding for weekday/weekend
df_full["is_weekend"] = df_full["day_type"].map({
    "Weekday": 0,
    "Weekend": 1
})

# =====================================================
# STEP 8: FINAL CLEANUP
# =====================================================

df_full["date"] = df_full["date"].astype(str)

# Drop text columns (encoded versions exist)
df_full.drop(columns=["congestion_label", "day_type"], inplace=True)

# Reorder columns (clean & ML-friendly)
df_full = df_full[
    [
        "date",
        "hour",
        "is_weekend",
        "route_id",
        "stop_id_from",
        "stop_id_to",
        "speed",
        "time",
        "number_of_trips",
        "SRI",
        "congestion_level"
    ]
]

# =====================================================
# STEP 9: SAVE DATASET
# =====================================================
df_full.to_csv(OUTPUT_FILE, index=False)

print("✅ Multi-day ML-ready dataset WITH encoding created successfully")
print(f"Saved at: {OUTPUT_FILE}")
