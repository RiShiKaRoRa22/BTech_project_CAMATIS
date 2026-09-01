#!/usr/bin/env python
# execution/add_driver_data.py

import pandas as pd
import numpy as np

# ========================================
# CONFIGURATION
# ========================================
INPUT_PATH = "data/enriched_data.csv"          # Fuel-enriched dataset
DRIVER_PATH = "data/driver/Driver_Behavior.csv"     # Driver behavior dataset
OUTPUT_PATH = "data/enriched_with_driver.csv"

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Features to take from driver dataset (all except label)
DRIVER_FEATURES = [
    'speed_kmph', 'accel_x', 'accel_y', 'brake_pressure',
    'steering_angle', 'throttle', 'lane_deviation',
    'phone_usage', 'headway_distance', 'reaction_time'
]

# ========================================
# FUNCTIONS
# ========================================

def find_label_column(df):
    """
    Find the column that contains the behavior labels.
    Tries to match by name (case-insensitive) or by content.
    """
    # Common names for label column
    candidates = ['label', 'behavior', 'class', 'driver_type', 'type', 'category']
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in candidates:
            return col
    # If none found, try to find a column with string values like 'Safe', 'Aggressive', 'Distracted'
    for col in df.columns:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) <= 5:  # likely categorical
            # Check if values contain typical labels
            if any(isinstance(v, str) and v.lower() in ['safe', 'aggressive', 'distracted'] for v in unique_vals):
                return col
    # Fallback: assume last column is label
    print("Warning: Could not auto-detect label column. Assuming the last column is the label.")
    return df.columns[-1]

def load_driver_profiles(driver_path):
    """
    Load driver dataset and compute average feature vector per behavior class.
    Returns a DataFrame with class as index and feature means as columns.
    """
    driver = pd.read_csv(driver_path)
    print("Driver dataset columns:", driver.columns.tolist())

    label_col = find_label_column(driver)
    print(f"Using '{label_col}' as the label column.")

    # Rename to 'Label' for consistency
    driver = driver.rename(columns={label_col: 'Label'})

    # Ensure Label is string type (in case it's numeric)
    driver['Label'] = driver['Label'].astype(str)

    # Compute means per class
    profiles = driver.groupby('Label')[DRIVER_FEATURES].mean().reset_index()
    print("Class profiles:\n", profiles)
    return profiles

def assign_driver_classes(bus_ids, profiles, seed=42):
    """
    Randomly assign a behavior class to each bus.
    Returns a dict {bus_id: class_name}.
    """
    np.random.seed(seed)
    classes = profiles['Label'].unique()
    assignment = {bus: np.random.choice(classes) for bus in bus_ids}
    return assignment

def merge_driver_features(main_df, profiles, assignment):
    """
    Add driver features to main_df based on bus->class assignment.
    """
    class_feature_map = profiles.set_index('Label')[DRIVER_FEATURES].to_dict(orient='index')

    # For each row, fetch the features based on its bus's assigned class
    driver_data = []
    for _, row in main_df.iterrows():
        bus = row['bus_id']
        cls = assignment[bus]
        feat_vals = class_feature_map[cls]
        driver_data.append(feat_vals)

    driver_df = pd.DataFrame(driver_data, columns=DRIVER_FEATURES)

    # Add class label as a column
    main_with_driver = pd.concat([main_df, driver_df], axis=1)
    main_with_driver['driver_class'] = main_df['bus_id'].map(assignment)

    return main_with_driver

# ========================================
# MAIN
# ========================================

def main():
    print("Loading fuel-enriched dataset...")
    main = pd.read_csv(INPUT_PATH)
    print(f"Loaded {len(main)} rows.")

    print("Loading driver dataset and computing class profiles...")
    profiles = load_driver_profiles(DRIVER_PATH)

    bus_ids = main['bus_id'].unique()
    print(f"Found {len(bus_ids)} unique buses.")

    print("Assigning a random driver class to each bus...")
    assignment = assign_driver_classes(bus_ids, profiles, seed=RANDOM_SEED)
    print("Assignment:", assignment)

    print("Merging driver features...")
    final_df = merge_driver_features(main, profiles, assignment)

    print(f"Final dataset has {len(final_df)} rows and {len(final_df.columns)} columns.")

    print(f"Saving to {OUTPUT_PATH}...")
    final_df.to_csv(OUTPUT_PATH, index=False)
    print("Done.")

if __name__ == "__main__":
    main()