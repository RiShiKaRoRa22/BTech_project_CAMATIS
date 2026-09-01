"""
CAMATIS Configuration - FINAL ENHANCED VERSION
With class weighting, interaction features, and cyclical encoding
"""

import os
import numpy as np

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.path.join(BASE_DIR, "camatis", "data")
MODELS_DIR = os.path.join(BASE_DIR, "camatis", "models_saved")
RESULTS_DIR = os.path.join(BASE_DIR, "camatis", "results")
LOGS_DIR = os.path.join(BASE_DIR, "camatis", "logs")

for dir_path in [MODELS_DIR, RESULTS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Data Configuration
TRAIN_FILE = os.path.join(DATA_DIR, "train_engineered.csv")
TEST_FILE = os.path.join(DATA_DIR, "test_engineered.csv")

# ============================================================================
# FEATURE GROUPS - WITH ALL ENHANCEMENTS
# ============================================================================

# Temporal Features (5) - Original
TEMPORAL_FEATURES = ['hour', 'day_of_week', 'month', 'is_weekend', 'is_peak']

# Cyclical Time Features (4) - For better time representation
CYCLICAL_FEATURES = [
    'hour_sin',      # sin(2*pi*hour/24)
    'hour_cos',      # cos(2*pi*hour/24)  
    'day_sin',       # sin(2*pi*day_of_week/7)
    'day_cos'        # cos(2*pi*day_of_week/7)
]

# NEW: Month Cyclical Features (2) - Month also has cyclical nature
MONTH_CYCLICAL_FEATURES = [
    'month_sin',     # sin(2*pi*month/12)
    'month_cos'      # cos(2*pi*month/12)
]

# Operational Features (3)
OPERATIONAL_FEATURES = ['speed', 'SRI', 'congestion_level']

# NEW: Interaction Features (3) - Capture combined effects
INTERACTION_FEATURES = [
    'congestion_speed_ratio',    # congestion_level / speed
    'demand_temp_interaction',   # passenger_demand * temp_max (for training only)
    'peak_weather'               # is_peak * precipitation
]

# Bus Features (1)
BUS_FEATURES = ['capacity']

# ============================================================================
# NEW FEATURES (SAFE - direct measurements)
# ============================================================================

# Fuel Features (7)
FUEL_FEATURES = [
    'avg_slope',
    'mass',
    'aircond_ptime',
    'stop_ptime',
    'brake_usage',
    'accel',
    'fuel_per_km'
]

# Driver Behavior Features (10)
DRIVER_FEATURES = [
    'speed_kmph',
    'accel_x',
    'accel_y',
    'brake_pressure',
    'steering_angle',
    'throttle',
    'lane_deviation',
    'phone_usage',
    'headway_distance',
    'reaction_time'
]

# Driver Class (1)
DRIVER_CLASS_FEATURES = ['driver_class_encoded']

# Weather Features (7)
WEATHER_FEATURES = [
    'temp_max',
    'temp_min',
    'precipitation',
    'rain',
    'snowfall',
    'wind_speed_max',
    'wind_gust_max'
]

# NEW: Weather Lag Features (2) - Weather effects may have delay
WEATHER_LAG_FEATURES = [
    'rain_lag_2h',       # Rain 2 hours ago
    'snowfall_lag_2h'    # Snowfall 2 hours ago
]

# Encoded ID Features
# OPTION 1: Keep route_id for route-specific predictions (default)
# OPTION 2: Remove for generalizable model (set REMOVE_ROUTE_ID = True)
REMOVE_ROUTE_ID = False  # Set to True to remove route_id for generalization

if REMOVE_ROUTE_ID:
    ENCODED_FEATURES = ['bus_id_encoded']  # Remove route_id
else:
    ENCODED_FEATURES = ['bus_id_encoded', 'route_id_encoded']  # Keep route_id

# ============================================================================
# COMPLETE FEATURE LIST
# ============================================================================

ALL_FEATURES = (
    TEMPORAL_FEATURES +           # 5
    CYCLICAL_FEATURES +           # 4
    MONTH_CYCLICAL_FEATURES +     # 2 (NEW!)
    OPERATIONAL_FEATURES +        # 3
    INTERACTION_FEATURES +        # 3 (NEW!)
    BUS_FEATURES +                # 1
    FUEL_FEATURES +               # 7
    DRIVER_FEATURES +             # 10
    DRIVER_CLASS_FEATURES +       # 1
    WEATHER_FEATURES +            # 7
    WEATHER_LAG_FEATURES          # 2 (NEW!)
)  # Total: 45 features

FEATURES_WITH_ENCODED = ALL_FEATURES + ENCODED_FEATURES

# Feature count
TOTAL_FEATURES = len(FEATURES_WITH_ENCODED)

# ============================================================================
# TARGET VARIABLES
# ============================================================================

TARGET_VARIABLES = ['passenger_demand', 'load_factor', 'utilization_encoded']

# ============================================================================
# CLASS WEIGHTS FOR IMBALANCED DATA
# ============================================================================

# Class weights for utilization (Underutilized=0, Normal=1, Overutilized=2)
# Normal class needs more weight since it's underrepresented
UTILIZATION_CLASS_WEIGHTS = {
    0: 1.0,   # Underutilized - well represented
    1: 3.0,   # Normal - underrepresented, give more weight
    2: 1.5    # Overutilized - slightly underrepresented
}

# ============================================================================
# MODEL HYPERPARAMETERS (Enhanced)
# ============================================================================

DEEP_LEARNING_CONFIG = {
    'input_dim': TOTAL_FEATURES,
    'hidden_dim': 256,
    'num_layers': 3,
    'num_heads': 4,
    'dropout': 0.3,
    'learning_rate': 0.001,
    'batch_size': 256,
    'epochs': 100,
    'patience': 15,
    'scheduler_factor': 0.5,
    'scheduler_patience': 5,
    'class_weights': UTILIZATION_CLASS_WEIGHTS  # NEW!
}

LIGHTGBM_CONFIG = {
    'num_leaves': 31,
    'learning_rate': 0.05,
    'n_estimators': 300,
    'max_depth': -1,
    'min_child_samples': 20,
    'reg_alpha': 0.1,
    'reg_lambda': 0.1,
    'min_split_gain': 0.01,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'class_weight': 'balanced'  # NEW! - handles class imbalance
}

CATBOOST_CONFIG = {
    'iterations': 300,
    'learning_rate': 0.05,
    'depth': 6,
    'l2_leaf_reg': 3,
    'verbose': False,
    'early_stopping_rounds': 50
}

XGBOOST_META_CONFIG = {
    'n_estimators': 150,
    'learning_rate': 0.05,
    'max_depth': 5,
    'subsample': 0.8,
    'reg_alpha': 0.1,
    'reg_lambda': 0.1,
    'colsample_bytree': 0.8,
    'scale_pos_weight': 3.0  # NEW! - for Normal class
}

# ============================================================================
# OTHER CONFIGURATIONS
# ============================================================================

MC_DROPOUT_SAMPLES = 50
CONFIDENCE_LEVEL = 0.95

OPTIMIZATION_OBJECTIVES = ['waiting_time', 'fuel_cost', 'utilization', 'fairness']
POPULATION_SIZE = 100
N_GENERATIONS = 50

SIMULATION_SCENARIOS = ['normal', 'festival_surge', 'congestion_spike', 'fleet_breakdown']
SIMULATION_DURATION = 24

RANDOM_SEED = 42

def add_cyclical_features(df):
    """
    Add cyclical time features to dataframe
    """
    df = df.copy()
    
    # Hour cyclical (0-23)
    if 'hour' in df.columns:
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    
    # Day of week cyclical (0-6)
    if 'day_of_week' in df.columns:
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    # Month cyclical (1-12)
    if 'month' in df.columns:
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    return df

def add_interaction_features(df):
    """
    Add interaction features to dataframe
    """
    df = df.copy()
    
    # congestion_speed_ratio = congestion_level / speed
    if 'congestion_level' in df.columns and 'speed' in df.columns:
        df['congestion_speed_ratio'] = df['congestion_level'] / (df['speed'] + 1e-8)
    
    # peak_weather = is_peak * precipitation
    if 'is_peak' in df.columns and 'precipitation' in df.columns:
        df['peak_weather'] = df['is_peak'] * df['precipitation']
    
    # demand_temp_interaction (only for training, will be created in data loader with target)
    
    return df

def add_weather_lag_features(df):
    """
    Add lag features for weather (rain and snowfall from 2 hours ago)
    Note: This requires the data to have sequential order
    """
    df = df.copy()
    
    # Sort by date and hour
    if 'date' in df.columns and 'hour' in df.columns:
        df = df.sort_values(['date', 'hour'])
    
    # Create lag features (shift by 2 positions)
    if 'rain' in df.columns:
        df['rain_lag_2h'] = df['rain'].shift(2)
        df['rain_lag_2h'] = df['rain_lag_2h'].fillna(0)
    
    if 'snowfall' in df.columns:
        df['snowfall_lag_2h'] = df['snowfall'].shift(2)
        df['snowfall_lag_2h'] = df['snowfall_lag_2h'].fillna(0)
    
    return df

def print_config_summary():
    """Print configuration summary"""
    print("=" * 60)
    print("CAMATIS CONFIGURATION SUMMARY (FINAL ENHANCED)")
    print("=" * 60)
    print(f"\n📊 FEATURES (Total: {TOTAL_FEATURES}):")
    print(f"   Temporal: {len(TEMPORAL_FEATURES)}")
    print(f"   Cyclical: {len(CYCLICAL_FEATURES)}")
    print(f"   Month Cyclical: {len(MONTH_CYCLICAL_FEATURES)} (NEW!)")
    print(f"   Operational: {len(OPERATIONAL_FEATURES)}")
    print(f"   Interaction: {len(INTERACTION_FEATURES)} (NEW!)")
    print(f"   Bus: {len(BUS_FEATURES)}")
    print(f"   Fuel: {len(FUEL_FEATURES)}")
    print(f"   Driver Behavior: {len(DRIVER_FEATURES)}")
    print(f"   Driver Class: {len(DRIVER_CLASS_FEATURES)}")
    print(f"   Weather: {len(WEATHER_FEATURES)}")
    print(f"   Weather Lag: {len(WEATHER_LAG_FEATURES)} (NEW!)")
    print(f"   Encoded IDs: {len(ENCODED_FEATURES)}")
    print(f"\n⚖️ CLASS WEIGHTS:")
    print(f"   Underutilized (0): {UTILIZATION_CLASS_WEIGHTS[0]}")
    print(f"   Normal (1): {UTILIZATION_CLASS_WEIGHTS[1]} (increased weight!)")
    print(f"   Overutilized (2): {UTILIZATION_CLASS_WEIGHTS[2]}")
    print(f"\n🧠 DEEP LEARNING:")
    print(f"   Epochs: {DEEP_LEARNING_CONFIG['epochs']}")
    print(f"   Patience: {DEEP_LEARNING_CONFIG['patience']}")
    print(f"   MC Dropout Samples: {MC_DROPOUT_SAMPLES}")
    if REMOVE_ROUTE_ID:
        print(f"\n🔧 MODE: Generalizable (route_id removed)")
    else:
        print(f"\n🔧 MODE: Route-specific (route_id kept)")
    print("=" * 60)