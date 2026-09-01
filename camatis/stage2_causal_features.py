"""
Stage 2: Causal Feature Intelligence
Learn causal relationships between features for better interpretability
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import networkx as nx
from camatis.config import *

class CausalFeatureIntelligence:
    """
    Main causal feature intelligence class
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.causal_models = {}
        self.edge_weights = {}
        
    def build_causal_graph(self, df_sample=None):
        """
        Build causal graph with all features including new fuel, driver, weather data
        
        Causal relationships based on domain knowledge:
        - Weather → Passenger Demand (rain increases demand)
        - Weather → Fuel Consumption (temperature affects AC usage)
        - Driver Behavior → Fuel Consumption (aggressive driving uses more fuel)
        - Driver Behavior → Safety (aggressive = higher risk)
        - Fuel → Operational Cost (higher fuel = higher cost)
        - Congestion → Speed (congestion reduces speed)
        - Speed → Demand (faster buses attract more passengers)
        - Demand → Load (more passengers = higher load)
        - Load → Utilization (higher load = better utilization)
        - Is_Peak → Demand (peak hours = higher demand)
        - Capacity → Load (higher capacity = lower load)
        """
        print("Building causal graph with enriched features...")
        
        # If sample is provided, check for feature availability
        if df_sample is not None:
            available_features = df_sample.columns.tolist()
            print(f"   Sample features available: {len(available_features)}")
        
        # ======================================================================
        # 1. EXISTING RELATIONSHIPS (from original 17 features)
        # ======================================================================
        
        # Core operational relationships
        self._add_causal_edge('congestion_level', 'speed', 'negative')
        self._add_causal_edge('speed', 'passenger_demand', 'positive')
        self._add_causal_edge('passenger_demand', 'load_factor', 'positive')
        self._add_causal_edge('load_factor', 'utilization_encoded', 'positive')
        self._add_causal_edge('is_peak', 'passenger_demand', 'positive')
        self._add_causal_edge('capacity', 'load_factor', 'negative')
        
        # ======================================================================
        # 2. FUEL DATA RELATIONSHIPS (7 new features)
        # ======================================================================
        
        # Fuel consumption drivers
        self._add_causal_edge('avg_slope', 'fuel_per_km', 'positive')      # Steeper = more fuel
        self._add_causal_edge('mass', 'fuel_per_km', 'positive')           # Heavier = more fuel
        self._add_causal_edge('accel', 'fuel_per_km', 'positive')          # More acceleration = more fuel
        self._add_causal_edge('brake_usage', 'fuel_per_km', 'positive')    # More braking = more fuel
        self._add_causal_edge('stop_ptime', 'fuel_per_km', 'positive')     # Idling = more fuel
        self._add_causal_edge('aircond_ptime', 'fuel_per_km', 'positive')  # AC = more fuel
        
        # Fuel impact on operations
        self._add_causal_edge('fuel_per_km', 'congestion_level', 'positive')    # More fuel = more congestion
        self._add_causal_edge('fuel_per_km', 'utilization_encoded', 'negative')  # More fuel = lower utilization
        
        # ======================================================================
        # 3. DRIVER DATA RELATIONSHIPS (11 new features)
        # ======================================================================
        
        # Driver behavior impacts (using ENCODED version to avoid categorical issues)
        self._add_causal_edge('driver_class_encoded', 'fuel_per_km', 'positive')      # Aggressive = more fuel
        self._add_causal_edge('driver_class_encoded', 'speed', 'positive')            # Aggressive = faster
        self._add_causal_edge('driver_class_encoded', 'brake_usage', 'positive')      # Aggressive = more braking
        self._add_causal_edge('driver_class_encoded', 'accel', 'positive')            # Aggressive = more acceleration
        self._add_causal_edge('driver_class_encoded', 'passenger_demand', 'negative') # Aggressive = fewer passengers
        self._add_causal_edge('driver_class_encoded', 'load_factor', 'negative')      # Aggressive = lower load
        
        # Driver metrics relationships
        self._add_causal_edge('speed_kmph', 'speed', 'positive')           # Driver speed = bus speed
        self._add_causal_edge('brake_pressure', 'brake_usage', 'positive') # More pressure = more braking
        self._add_causal_edge('throttle', 'accel', 'positive')             # More throttle = more acceleration
        
        # Safety-related relationships
        self._add_causal_edge('lane_deviation', 'safety_risk', 'positive') # Lane deviation = higher risk
        self._add_causal_edge('phone_usage', 'safety_risk', 'positive')    # Phone usage = higher risk
        self._add_causal_edge('reaction_time', 'safety_risk', 'negative')  # Slower reaction = higher risk
        
        # ======================================================================
        # 4. WEATHER DATA RELATIONSHIPS (8 new features)
        # ======================================================================
        
        # Weather impacts on demand
        self._add_causal_edge('precipitation', 'passenger_demand', 'positive')   # Rain = more bus users
        self._add_causal_edge('rain', 'passenger_demand', 'positive')            # Rain = more bus users
        self._add_causal_edge('snowfall', 'passenger_demand', 'positive')        # Snow = more bus users
        self._add_causal_edge('temp_max', 'passenger_demand', 'negative')        # Extreme heat = fewer riders
        self._add_causal_edge('temp_min', 'passenger_demand', 'negative')        # Extreme cold = fewer riders
        
        # Weather impacts on operations
        self._add_causal_edge('precipitation', 'congestion_level', 'positive')   # Rain = more congestion
        self._add_causal_edge('snowfall', 'congestion_level', 'positive')        # Snow = more congestion
        self._add_causal_edge('wind_speed_max', 'speed', 'negative')             # High wind = slower speed
        
        # Weather impacts on fuel (via AC and heating)
        self._add_causal_edge('temp_max', 'aircond_ptime', 'positive')           # Hot = more AC
        self._add_causal_edge('temp_min', 'aircond_ptime', 'negative')           # Cold = less AC
        self._add_causal_edge('temp_max', 'fuel_per_km', 'positive')             # Hot = more fuel (AC)
        self._add_causal_edge('temp_min', 'fuel_per_km', 'positive')             # Cold = more fuel (heating)
        
        # Weather impacts on utilization
        self._add_causal_edge('precipitation', 'load_factor', 'positive')        # Rain = higher load
        self._add_causal_edge('precipitation', 'utilization_encoded', 'positive') # Rain = better utilization
        
        # Weather impacts on driver behavior
        self._add_causal_edge('precipitation', 'reaction_time', 'positive')      # Rain = slower reaction
        self._add_causal_edge('snowfall', 'reaction_time', 'positive')           # Snow = slower reaction
        self._add_causal_edge('wind_speed_max', 'lane_deviation', 'positive')    # Wind = more lane deviation
        
        # ======================================================================
        # 5. DERIVED FEATURE RELATIONSHIPS
        # ======================================================================
        
        self._add_causal_edge('demand_capacity_ratio', 'load_factor', 'positive')
        self._add_causal_edge('speed_congestion_ratio', 'congestion_level', 'negative')
        self._add_causal_edge('utilization_score', 'utilization_encoded', 'positive')
        
        # ======================================================================
        # 6. SUMMARY
        # ======================================================================
        
        print(f"✅ Causal graph constructed with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges")
        
        # Print summary stats
        nodes_list = list(self.graph.nodes)
        edges_list = list(self.graph.edges)
        
        print(f"   Total Nodes: {len(nodes_list)}")
        print(f"   Total Edges: {len(edges_list)}")
        
        # Categorize edges
        fuel_edges = [e for e in edges_list if 'fuel' in e[0] or 'fuel' in e[1]]
        driver_edges = [e for e in edges_list if 'driver' in e[0] or 'driver' in e[1] or 'speed_kmph' in e[0] or 'brake_pressure' in e[0]]
        weather_edges = [e for e in edges_list if 'temp' in e[0] or 'precip' in e[0] or 'wind' in e[0] or 'snow' in e[0]]
        
        print(f"   Fuel-related edges: {len(fuel_edges)}")
        print(f"   Driver-related edges: {len(driver_edges)}")
        print(f"   Weather-related edges: {len(weather_edges)}")
        
        return self.graph
    
    def _add_causal_edge(self, cause, effect, direction='positive'):
        """Add a causal edge with direction"""
        self.graph.add_edge(cause, effect, direction=direction)
        self.edge_weights[(cause, effect)] = 1.0 if direction == 'positive' else -1.0
    
    def _is_numeric_column(self, df, col):
        """Check if a column is numeric"""
        try:
            return pd.api.types.is_numeric_dtype(df[col])
        except:
            return False
    
    def learn_causal_weights(self, df, features):
        """
        Learn the actual strength of causal relationships using linear regression
        
        Args:
            df: DataFrame with features
            features: List of feature names
        """
        print("Learning causal relationship strengths...")
        
        success_count = 0
        skip_count = 0
        
        # Iterate through all edges
        for cause, effect in self.graph.edges():
            if cause in df.columns and effect in df.columns:
                try:
                    # Check if columns are numeric
                    if not self._is_numeric_column(df, cause) or not self._is_numeric_column(df, effect):
                        skip_count += 1
                        continue
                    
                    X = df[[cause]].values
                    y = df[effect].values
                    
                    # Handle missing values
                    mask = ~(np.isnan(X.flatten()) | np.isnan(y))
                    X_clean = X[mask].reshape(-1, 1)
                    y_clean = y[mask]
                    
                    if len(X_clean) > 10:
                        model = LinearRegression()
                        model.fit(X_clean, y_clean)
                        
                        self.edge_weights[(cause, effect)] = model.coef_[0]
                        self.causal_models[(cause, effect)] = model
                        success_count += 1
                except Exception as e:
                    skip_count += 1
                    pass
        
        print(f"✅ Causal models learned! ({success_count} edges learned, {skip_count} skipped)")
        return self.edge_weights
    
    # Alias for backward compatibility with main_pipeline.py
    def learn_causal_relationships(self, df):
        """Alias for learn_causal_weights for backward compatibility"""
        features = df.columns.tolist()
        return self.learn_causal_weights(df, features)
    
    def get_causal_graph(self):
        """Return the causal graph"""
        return self.graph
    
    def get_edge_weights(self):
        """Return edge weights"""
        return self.edge_weights
    
    def get_feature_influence(self, feature):
        """Get all features influenced by a given feature"""
        influences = {}
        for (cause, effect), weight in self.edge_weights.items():
            if cause == feature:
                influences[effect] = weight
        return influences
    
    def get_causal_paths(self, source, target):
        """Find all causal paths between source and target"""
        try:
            paths = list(nx.all_simple_paths(self.graph, source, target))
            return paths
        except:
            return []
    
    def get_feature_importance_summary(self):
        """Get summary of feature importance based on causal graph"""
        summary = {}
        for node in self.graph.nodes():
            outgoing = len(list(self.graph.successors(node)))
            incoming = len(list(self.graph.predecessors(node)))
            
            summary[node] = {
                'causes': outgoing,
                'effects': incoming,
                'total_connections': outgoing + incoming
            }
        
        return summary


# Alias for backward compatibility
CausalFeatureEngine = CausalFeatureIntelligence