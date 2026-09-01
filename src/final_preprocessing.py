import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# =====================================================
# FILE PATHS
# =====================================================
INPUT_FILE = "data/processed/gtfs_ridership_fleet_dataset.csv"
TRAIN_FILE = "data/processed/final_train.csv"
TEST_FILE = "data/processed/final_test.csv"

# =====================================================
# STEP 0: LOAD DATA
# =====================================================
df = pd.read_csv(INPUT_FILE)
print("Initial rows:", len(df))

# =====================================================
# STEP 1: BASIC CLEANING
# =====================================================

# Remove duplicate rows
df = df.drop_duplicates()

# Fix datatypes
df["date"] = pd.to_datetime(df["date"])
df["hour"] = df["hour"].astype(int)
df["route_id"] = df["route_id"].astype(int)

# Fill missing demand safely
df["estimated_passenger_demand"] = df["estimated_passenger_demand"].fillna(0)

print("After cleaning rows:", len(df))

# =====================================================
# STEP 2: HANDLE INFINITE / EXTREME VALUES (CRITICAL)
# =====================================================

# Replace inf and -inf with NaN
df.replace([np.inf, -np.inf], np.nan, inplace=True)

# Fill numeric NaNs safely
df["speed"] = df["speed"].fillna(df["speed"].median())
df["SRI"] = df["SRI"].fillna(df["SRI"].median())
df["estimated_passenger_demand"] = df["estimated_passenger_demand"].fillna(0)

# =====================================================
# STEP 3: NORMALIZATION
# =====================================================

scaler = MinMaxScaler()

df[["speed", "SRI", "estimated_passenger_demand"]] = scaler.fit_transform(
    df[["speed", "SRI", "estimated_passenger_demand"]]
)

# =====================================================
# STEP 4: AGGREGATION (MANDATORY)
# date × route_id × hour × bus
# =====================================================

agg_df = df.groupby(
    ["date", "route_id", "hour", "is_weekend", "bus_id", "capacity"],
    as_index=False
).agg(
    passenger_demand=("estimated_passenger_demand", "sum"),
    speed=("speed", "mean"),
    SRI=("SRI", "mean"),
    congestion_level=("congestion_level", "mean")
)

print("After aggregation rows:", len(agg_df))

# =====================================================
# STEP 5: UTILIZATION METRICS
# =====================================================

agg_df["load_factor"] = agg_df["passenger_demand"] / agg_df["capacity"]

def classify_utilization(lf):
    if lf > 1.0:
        return "Overloaded"
    elif lf >= 0.6:
        return "Optimal"
    else:
        return "Underutilized"

agg_df["utilization_status"] = agg_df["load_factor"].apply(classify_utilization)

# =====================================================
# STEP 6: FINAL FEATURE SELECTION
# =====================================================

final_df = agg_df[
    [
        "date",
        "hour",
        "is_weekend",
        "route_id",
        "speed",
        "SRI",
        "congestion_level",
        "passenger_demand",
        "bus_id",
        "capacity",
        "load_factor",
        "utilization_status"
    ]
]

# =====================================================
# STEP 7: TIME-AWARE TRAIN–TEST SPLIT
# =====================================================

final_df = final_df.sort_values("date")

split_idx = int(len(final_df) * 0.8)
train_df = final_df.iloc[:split_idx]
test_df = final_df.iloc[split_idx:]

# =====================================================
# STEP 8: SAVE OUTPUTS
# =====================================================

train_df.to_csv(TRAIN_FILE, index=False)
test_df.to_csv(TEST_FILE, index=False)

print("✅ FINAL PREPROCESSING COMPLETE")
print("Train rows:", len(train_df))
print("Test rows:", len(test_df))
