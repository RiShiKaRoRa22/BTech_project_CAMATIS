import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler

# ---------------- PATHS ----------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

train_path = DATA_DIR / "final_train.csv"
test_path = DATA_DIR / "final_test.csv"

train = pd.read_csv(train_path)
test = pd.read_csv(test_path)

print("Train shape:", train.shape)
print("Test shape:", test.shape)

# Combine temporarily for consistent feature engineering
df = pd.concat([train, test], ignore_index=True)

# ---------------- TIME FEATURES ----------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")

df["day_of_week"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month

# Peak hour flag
df["is_peak"] = df["hour"].apply(
    lambda x: 1 if x in [8, 9, 10, 17, 18, 19, 20] else 0
)

# ---------------- TRANSPORT FEATURES ----------------
df["demand_capacity_ratio"] = df["passenger_demand"] / df["capacity"]

df["speed_congestion_ratio"] = df["speed"] / (df["congestion_level"] + 1)

df["utilization_score"] = (
    df["load_factor"] + df["congestion_level"] + df["passenger_demand"]
)

# ---------------- CATEGORICAL ENCODING ----------------
df["utilization_status"] = df["utilization_status"].astype(str)

status_map = {
    "Underutilized": 0,
    "Optimal": 1,
    "Overloaded": 2
}

df["utilization_encoded"] = df["utilization_status"].map(status_map)

# ---------------- ROUTE AGG FEATURES ----------------
route_stats = (
    df.groupby("route_id")
    .agg(
        route_avg_speed=("speed", "mean"),
        route_avg_demand=("passenger_demand", "mean"),
        route_avg_congestion=("congestion_level", "mean"),
    )
    .reset_index()
)

df = df.merge(route_stats, on="route_id", how="left")

# ---------------- NORMALIZATION ----------------
num_cols = [
    "speed", "SRI", "passenger_demand",
    "capacity", "load_factor",
    "demand_capacity_ratio",
    "speed_congestion_ratio",
    "utilization_score",
    "route_avg_speed",
    "route_avg_demand",
    "route_avg_congestion"
]

scaler = StandardScaler()
df[num_cols] = scaler.fit_transform(df[num_cols])

# ---------------- SPLIT BACK ----------------
train_fe = df.iloc[:len(train)]
test_fe = df.iloc[len(train):]

train_fe.to_csv(DATA_DIR / "train_engineered.csv", index=False)
test_fe.to_csv(DATA_DIR / "test_engineered.csv", index=False)

print("\n✅ Feature engineering complete")
print("New train shape:", train_fe.shape)
print("New test shape:", test_fe.shape)
print("\nColumns:")
print(train_fe.columns.tolist())
print(df.head(10))
