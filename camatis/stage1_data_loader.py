"""
Stage 1: Data Foundation - FINAL ENHANCED VERSION
With interaction features, weather lag, and month cyclical
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
from camatis.config import *

class DataLoader:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_data(self):
        """Load train and test datasets"""
        print("Loading datasets...")
        train_df = pd.read_csv(TRAIN_FILE)
        test_df = pd.read_csv(TEST_FILE)
        
        print(f"Train shape: {train_df.shape}")
        print(f"Test shape: {test_df.shape}")
        
        return train_df, test_df
    
    def prepare_features(self, train_df, test_df):
        """Prepare feature matrices and target variables"""
        train_df = train_df.copy()
        test_df = test_df.copy()
        
        # ============================================================================
        # ADD CYCLICAL TIME FEATURES
        # ============================================================================
        
        for df in [train_df, test_df]:
            # Hour cyclical
            if 'hour' in df.columns:
                df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
                df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            
            # Day of week cyclical
            if 'day_of_week' in df.columns:
                df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
                df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
            # Month cyclical (NEW!)
            if 'month' in df.columns:
                df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
                df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        print("✅ Added cyclical features: hour_sin/cos, day_sin/cos, month_sin/cos")
        
        # ============================================================================
        # ADD INTERACTION FEATURES
        # ============================================================================
        
        for df in [train_df, test_df]:
            # congestion_speed_ratio
            if 'congestion_level' in df.columns and 'speed' in df.columns:
                df['congestion_speed_ratio'] = df['congestion_level'] / (df['speed'] + 1e-8)
            
            # peak_weather
            if 'is_peak' in df.columns and 'precipitation' in df.columns:
                df['peak_weather'] = df['is_peak'] * df['precipitation']
            
            # demand_temp_interaction (only for training data, using target)
            # This is created separately for train/test
        
        print("✅ Added interaction features: congestion_speed_ratio, peak_weather")
        
        # ============================================================================
        # ADD WEATHER LAG FEATURES
        # ============================================================================
        
        for df in [train_df, test_df]:
            # Sort by date and hour for proper lag
            if 'date' in df.columns and 'hour' in df.columns:
                df = df.sort_values(['date', 'hour']).reset_index(drop=True)
            
            # Rain lag (2 hours)
            if 'rain' in df.columns:
                df['rain_lag_2h'] = df['rain'].shift(2)
                df['rain_lag_2h'] = df['rain_lag_2h'].fillna(0)
            
            # Snowfall lag (2 hours)
            if 'snowfall' in df.columns:
                df['snowfall_lag_2h'] = df['snowfall'].shift(2)
                df['snowfall_lag_2h'] = df['snowfall_lag_2h'].fillna(0)
        
        print("✅ Added weather lag features: rain_lag_2h, snowfall_lag_2h")
        
        # ============================================================================
        # ENCODE CATEGORICAL VARIABLES
        # ============================================================================
        
        if 'bus_id' in train_df.columns and 'bus_id' in test_df.columns:
            le_bus = LabelEncoder()
            train_df['bus_id_encoded'] = le_bus.fit_transform(train_df['bus_id'].astype(str))
            test_df['bus_id_encoded'] = le_bus.transform(test_df['bus_id'].astype(str))
            self.label_encoders['bus_id'] = le_bus
            print(f"✅ Encoded bus_id: {len(le_bus.classes_)} unique buses")
        
        # Conditional route_id encoding
        if REMOVE_ROUTE_ID:
            print("⚠️  REMOVING route_id for generalization mode")
        else:
            if 'route_id' in train_df.columns:
                le_route = LabelEncoder()
                train_df['route_id_encoded'] = le_route.fit_transform(train_df['route_id'].astype(str))
                if 'route_id' in test_df.columns:
                    test_df['route_id_encoded'] = le_route.transform(test_df['route_id'].astype(str))
                else:
                    test_df['route_id_encoded'] = 0
                self.label_encoders['route_id'] = le_route
                print(f"✅ Encoded route_id: {len(le_route.classes_)} unique routes")
        
        # Encode utilization_status (target)
        if 'utilization_status' in train_df.columns and 'utilization_status' in test_df.columns:
            le_util = LabelEncoder()
            train_df['utilization_status_encoded'] = le_util.fit_transform(train_df['utilization_status'].astype(str))
            test_df['utilization_status_encoded'] = le_util.transform(test_df['utilization_status'].astype(str))
            self.label_encoders['utilization_status'] = le_util
            print(f"✅ Encoded utilization_status: {len(le_util.classes_)} classes")
        
        if 'driver_class' in train_df.columns and 'driver_class' in test_df.columns:
            le_driver = LabelEncoder()
            train_df['driver_class_encoded'] = le_driver.fit_transform(train_df['driver_class'].astype(str))
            test_df['driver_class_encoded'] = le_driver.transform(test_df['driver_class'].astype(str))
            self.label_encoders['driver_class'] = le_driver
            print(f"✅ Encoded driver_class: {len(le_driver.classes_)} classes: {le_driver.classes_.tolist()}")
        
        # ============================================================================
        # BUILD FEATURE LIST
        # ============================================================================
        
        feature_cols = (
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
            WEATHER_LAG_FEATURES +        # 2 (NEW!)
            ENCODED_FEATURES              # 1 or 2
        )
        
        feature_cols = list(dict.fromkeys(feature_cols))
        
        # ============================================================================
        # VALIDATE FEATURES
        # ============================================================================
        
        available_feature_cols = []
        for col in feature_cols:
            if col in train_df.columns and col in test_df.columns:
                available_feature_cols.append(col)
        
        if not available_feature_cols:
            raise ValueError("No matching features found!")
        
        feature_cols = available_feature_cols
        
        # ============================================================================
        # EXTRACT FEATURES AND TARGETS
        # ============================================================================
        
        X_train = train_df[feature_cols].values
        X_test = test_df[feature_cols].values
        
        y_train = {
            'passenger_demand': train_df['passenger_demand'].values,
            'load_factor': train_df['load_factor'].values,
            'utilization_encoded': train_df['utilization_encoded'].values
        }
        
        y_test = {
            'passenger_demand': test_df['passenger_demand'].values,
            'load_factor': test_df['load_factor'].values,
            'utilization_encoded': test_df['utilization_encoded'].values
        }
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("\n" + "=" * 60)
        print("DATA PREPARATION SUMMARY (FINAL ENHANCED)")
        print("=" * 60)
        print(f"\n📊 FEATURES (Total: {len(feature_cols)}):")
        print(f"   {feature_cols}")
        print(f"\n🔄 NEW FEATURES ADDED:")
        print("   - month_sin, month_cos (month cyclical)")
        print("   - congestion_speed_ratio (interaction)")
        print("   - peak_weather (interaction)")
        print("   - rain_lag_2h, snowfall_lag_2h (weather lag)")
        print(f"\n⚖️ CLASS WEIGHTS:")
        print(f"   Underutilized (0): {UTILIZATION_CLASS_WEIGHTS[0]}")
        print(f"   Normal (1): {UTILIZATION_CLASS_WEIGHTS[1]} (increased for imbalance)")
        print(f"   Overutilized (2): {UTILIZATION_CLASS_WEIGHTS[2]}")
        if REMOVE_ROUTE_ID:
            print(f"\n🔧 MODE: Generalizable (route_id removed)")
        else:
            print(f"\n🔧 MODE: Route-specific (route_id kept)")
        print(f"\n📈 SHAPES:")
        print(f"   X_train: {X_train_scaled.shape}")
        print(f"   X_test: {X_test_scaled.shape}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test, feature_cols
    
    def save_preprocessor(self):
        joblib.dump(self.scaler, f"{MODELS_DIR}/scaler.pkl")
        joblib.dump(self.label_encoders, f"{MODELS_DIR}/label_encoders.pkl")
        print("✅ Preprocessors saved.")