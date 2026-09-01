import pandas as pd
import numpy as np
from math import ceil

# =====================================================
# FILE PATHS
# =====================================================
INPUT_FILE = "data/processed/gtfs_with_demand.csv"
OUTPUT_FILE = "data/processed/gtfs_ridership_fleet_dataset.csv"

# =====================================================
# STEP 1: LOAD GTFS + RIDERSHIP DATA
# =====================================================
df = pd.read_csv(INPUT_FILE)

print("GTFS + Ridership rows:", len(df))

# =====================================================
# PART A: GENERATE SYNTHETIC FLEET DATA
# =====================================================

np.random.seed(42)

TOTAL_BUSES = 20
DEPOT_ID = "Depot_A"

fleet_data = []

for i in range(1, TOTAL_BUSES + 1):
    bus_type = np.random.choice(["Standard", "Mini"], p=[0.7, 0.3])

    if bus_type == "Standard":
        capacity = np.random.randint(45, 56)
    else:
        capacity = np.random.randint(30, 36)

    fleet_data.append({
        "bus_id": f"BUS_{i:02d}",
        "capacity": capacity,
        "bus_type": bus_type,
        "depot_id": DEPOT_ID,
        "status": "Active"
    })

fleet_df = pd.DataFrame(fleet_data)

print("Synthetic fleet created:", len(fleet_df), "buses")

# =====================================================
# PART B: DAILY ROUTE DEMAND COMPUTATION
# =====================================================

route_day_demand = (
    df
    .groupby(["date", "route_id"])
    .agg(
        total_passengers=("estimated_passenger_demand", "sum"),
        avg_trips=("number_of_trips", "mean")
    )
    .reset_index()
)

avg_capacity = fleet_df["capacity"].mean()

route_day_demand["required_buses"] = route_day_demand.apply(
    lambda row: max(
        1,
        ceil(row["total_passengers"] / (avg_capacity * max(row["avg_trips"], 1)))
    ),
    axis=1
)

# =====================================================
# PART C: ASSIGN BUSES TO ROUTES (PER DAY)
# =====================================================

bus_assignments = []
fleet_bus_ids = fleet_df["bus_id"].tolist()

for _, row in route_day_demand.iterrows():
    assigned = np.random.choice(
        fleet_bus_ids,
        size=min(row["required_buses"], len(fleet_bus_ids)),
        replace=False
    )

    for bus_id in assigned:
        bus_assignments.append({
            "date": row["date"],
            "route_id": row["route_id"],
            "bus_id": bus_id
        })

bus_assignment_df = pd.DataFrame(bus_assignments)

print("Bus assignments created:", len(bus_assignment_df))

# =====================================================
# PART D: MERGE FLEET INTO GTFS + RIDERSHIP
# =====================================================

df = df.merge(
    bus_assignment_df,
    on=["date", "route_id"],
    how="left"
)

df = df.merge(
    fleet_df[["bus_id", "capacity", "bus_type"]],
    on="bus_id",
    how="left"
)

# =====================================================
# PART E: UTILIZATION METRICS
# =====================================================

df["load_factor"] = df["estimated_passenger_demand"] / df["capacity"]

def utilization_status(lf):
    if lf > 1.0:
        return "Overloaded"
    elif lf >= 0.6:
        return "Optimal"
    else:
        return "Underutilized"

df["utilization_status"] = df["load_factor"].apply(utilization_status)

# =====================================================
# FINAL DATASET (GTFS + RIDERSHIP + FLEET)
# =====================================================

final_df = df[
    [
        # TIME (GTFS)
        "date",
        "hour",
        "is_weekend",

        # ROUTE (GTFS)
        "route_id",

        # TRAFFIC (GTFS)
        "speed",
        "SRI",
        "congestion_level",

        # RIDERSHIP (PUBLIC + DERIVED)
        "Total Ridership",
        "demand_weight",
        "estimated_passenger_demand",

        # FLEET (SYNTHETIC)
        "bus_id",
        "capacity",
        "bus_type",

        # METRICS
        "load_factor",
        "utilization_status"
    ]
]

# =====================================================
# SAVE OUTPUT
# =====================================================
final_df.to_csv(OUTPUT_FILE, index=False)

print("✅ FINAL GTFS + RIDERSHIP + FLEET DATASET CREATED")
print("Saved at:", OUTPUT_FILE)
