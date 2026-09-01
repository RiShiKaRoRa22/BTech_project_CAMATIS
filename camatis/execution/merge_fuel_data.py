#!/usr/bin/env python
# execution/merge_data_pipeline.py

import pandas as pd

# ========================================
# CONFIGURATION
# ========================================
EXISTING_DATA_PATH = "data/train_engineered.csv"
FUEL_DATA_PATH     = "data/fuel/DATASET.csv"
OUTPUT_PATH        = "data/enriched_data.csv"

FUEL_COLS = [
    'avg_slope', 'mass', 'aircond_ptime',
    'stop_ptime', 'brake_usage', 'accel', 'fuel_per_km'
]

# ========================================
# FUNCTIONS
# ========================================

def load_and_aggregate_fuel(fuel_path):
    """
    Load fuel CSV, convert VehicleID to bus_id,
    and aggregate to (bus_id, hour) level (ignoring date).
    """
    fuel = pd.read_csv(fuel_path, sep=';', parse_dates=['Date-time'])
    fuel = fuel.rename(columns={'Date-time': 'timestamp'})

    # Convert numeric VehicleID to bus_id string (e.g., 12 -> "BUS_12")
    fuel['bus_id'] = fuel['VehicleID'].apply(lambda x: f"BUS_{x:02d}")

    # Extract hour (ignore date)
    fuel['hour'] = fuel['timestamp'].dt.hour

    # Aggregate by (bus_id, hour) – take mean for each fuel feature
    fuel_hourly = fuel.groupby(['bus_id', 'hour'], as_index=False)[FUEL_COLS].mean()
    return fuel_hourly

def merge_and_impute(existing_df, fuel_hourly):
    """
    Merge fuel data into existing using (bus_id, hour) as keys,
    then impute any missing values.
    """
    existing = existing_df.copy()

    # Merge on bus_id and hour (no date)
    merged = existing.merge(fuel_hourly, on=['bus_id', 'hour'], how='left')

    # ---- Imputation ----
    # First, fill with per-bus averages (in case some bus-hour combos missing)
    bus_avgs = merged.groupby('bus_id')[FUEL_COLS].mean()
    for col in FUEL_COLS:
        merged[col] = merged[col].fillna(merged['bus_id'].map(bus_avgs[col]))

    # If still missing, fill with global averages (across all buses)
    global_avgs = merged[FUEL_COLS].mean()
    for col in FUEL_COLS:
        merged[col] = merged[col].fillna(global_avgs[col])

    return merged

# ========================================
# MAIN
# ========================================

def main():
    print("Loading existing dataset...")
    existing = pd.read_csv(EXISTING_DATA_PATH)
    print(f"Loaded {len(existing)} rows.")

    print("Loading and aggregating fuel dataset (by bus_id and hour)...")
    fuel_hourly = load_and_aggregate_fuel(FUEL_DATA_PATH)
    print(f"Aggregated to {len(fuel_hourly)} (bus, hour) records.")

    # Debug: check overlap of bus_ids
    existing_buses = set(existing['bus_id'])
    fuel_buses = set(fuel_hourly['bus_id'])
    common_buses = existing_buses & fuel_buses
    print(f"Existing buses: {len(existing_buses)}, Fuel buses: {len(fuel_buses)}, Common: {len(common_buses)}")
    if not common_buses:
        print("WARNING: No common bus IDs! Check bus_id formatting.")
        print("Sample existing bus_ids:", list(existing_buses)[:5])
        print("Sample fuel bus_ids:", list(fuel_buses)[:5])
        # If no common bus, we can still proceed, but imputation will use global averages only.

    print("Merging and imputing...")
    enriched = merge_and_impute(existing, fuel_hourly)
    print(f"Merged dataset has {len(enriched)} rows and {len(enriched.columns)} columns.")

    # Check missingness after imputation
    missing = enriched[FUEL_COLS].isnull().sum().sum()
    if missing > 0:
        print(f"Warning: {missing} missing values remain in fuel columns after imputation.")
    else:
        print("All fuel columns successfully imputed.")

    print(f"Saving enriched dataset to {OUTPUT_PATH}...")
    enriched.to_csv(OUTPUT_PATH, index=False)
    print("Done.")

if __name__ == "__main__":
    main()