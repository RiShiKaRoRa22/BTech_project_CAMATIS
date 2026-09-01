"""
Stage 5: Uncertainty & Anomaly Intelligence
Provides confidence intervals and detects anomalies
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from scipy import stats
import joblib
from camatis.config import *

class UncertaintyEngine:
    def __init__(self):
        self.confidence_level = CONFIDENCE_LEVEL
        
    def compute_confidence_intervals(self, predictions_with_uncertainty):
        """
        Compute confidence intervals from MC Dropout predictions
        """
        z_score = stats.norm.ppf((1 + self.confidence_level) / 2)
        
        demand_mean = predictions_with_uncertainty['demand_mean']
        demand_std = predictions_with_uncertainty['demand_std']
        
        load_mean = predictions_with_uncertainty['load_mean']
        load_std = predictions_with_uncertainty['load_std']
        
        confidence_intervals = {
            'demand_lower': demand_mean - z_score * demand_std,
            'demand_upper': demand_mean + z_score * demand_std,
            'demand_std': demand_std,
            'load_lower': load_mean - z_score * load_std,
            'load_upper': load_mean + z_score * load_std,
            'load_std': load_std
        }
        
        return confidence_intervals
    
    def identify_high_uncertainty_samples(self, confidence_intervals, threshold_percentile=90):
        """Identify samples with high prediction uncertainty"""
        demand_uncertainty = confidence_intervals['demand_std']
        load_uncertainty = confidence_intervals['load_std']
        
        demand_threshold = np.percentile(demand_uncertainty, threshold_percentile)
        load_threshold = np.percentile(load_uncertainty, threshold_percentile)
        
        high_uncertainty_mask = (
            (demand_uncertainty > demand_threshold) | 
            (load_uncertainty > load_threshold)
        )
        
        print(f"High uncertainty samples: {high_uncertainty_mask.sum()} / {len(high_uncertainty_mask)}")
        
        return high_uncertainty_mask

class AnomalyDetector:
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=RANDOM_SEED,
            n_estimators=100
        )
        
    def fit(self, X_train):
        """Train anomaly detector"""
        print("Training anomaly detector...")
        self.isolation_forest.fit(X_train)
        
    def detect_anomalies(self, X):
        """
        Detect anomalies:
        - Festival surges
        - Abnormal congestion
        - Fleet misallocation
        """
        anomaly_scores = self.isolation_forest.score_samples(X)
        anomaly_labels = self.isolation_forest.predict(X)
        
        # -1 for anomalies, 1 for normal
        is_anomaly = anomaly_labels == -1
        
        print(f"Detected anomalies: {is_anomaly.sum()} / {len(is_anomaly)}")
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_scores': anomaly_scores
        }
    
    def categorize_anomalies(self, X, anomaly_mask, feature_names):
        """Categorize types of anomalies"""
        if anomaly_mask.sum() == 0:
            return {}
        
        anomalous_samples = X[anomaly_mask]
        
        # Find feature indices
        demand_idx = feature_names.index('passenger_demand') if 'passenger_demand' in feature_names else None
        congestion_idx = feature_names.index('congestion_level') if 'congestion_level' in feature_names else None
        
        categories = {
            'high_demand_surge': [],
            'congestion_spike': [],
            'capacity_mismatch': []
        }
        
        for i, sample in enumerate(anomalous_samples):
            if demand_idx and sample[demand_idx] > 2.0:
                categories['high_demand_surge'].append(i)
            if congestion_idx and sample[congestion_idx] > 2.0:
                categories['congestion_spike'].append(i)
        
        return categories
    
    def save_detector(self):
        """Save anomaly detector"""
        joblib.dump(self.isolation_forest, f"{MODELS_DIR}/anomaly_detector.pkl")
        print("Anomaly detector saved!")

    def load_detector(self):
        """Load trained anomaly detector"""
        self.isolation_forest = joblib.load(f"{MODELS_DIR}/anomaly_detector.pkl")
        print("Anomaly detector loaded!")

class UncertaintyAnomalyPipeline:
    def __init__(self):
        self.uncertainty_engine = UncertaintyEngine()
        self.anomaly_detector = AnomalyDetector()
        
    def process(self, X_train, X_test, dl_trainer):
        """Complete uncertainty and anomaly analysis"""
        # Train anomaly detector
        self.anomaly_detector.fit(X_train)
        
        # Get uncertainty-aware predictions
        print("Computing uncertainty estimates...")
        uncertainty_preds = dl_trainer.predict_with_uncertainty(X_test)
        
        # Compute confidence intervals
        confidence_intervals = self.uncertainty_engine.compute_confidence_intervals(uncertainty_preds)
        
        # Identify high uncertainty samples
        high_uncertainty = self.uncertainty_engine.identify_high_uncertainty_samples(confidence_intervals)
        
        # Detect anomalies
        anomaly_results = self.anomaly_detector.detect_anomalies(X_test)
        
        return {
            'uncertainty_predictions': uncertainty_preds,
            'confidence_intervals': confidence_intervals,
            'high_uncertainty_mask': high_uncertainty,
            'anomaly_results': anomaly_results
        }
    
    def process_inference(self, X_train, X_test, dl_trainer):

        from sklearn.preprocessing import StandardScaler

        # ---------------------------
        # SCALE DATA (VERY IMPORTANT)
        # ---------------------------
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # ---------------------------
        # TRAIN ANOMALY DETECTOR
        # ---------------------------
        self.anomaly_detector.isolation_forest.set_params(contamination=0.03)
        self.anomaly_detector.fit(X_train_scaled)

        # ---------------------------
        # UNCERTAINTY (MC DROPOUT)
        # ---------------------------
        print("Computing uncertainty estimates...")
        uncertainty_preds = dl_trainer.predict_with_uncertainty(X_test)

        confidence_intervals = self.uncertainty_engine.compute_confidence_intervals(uncertainty_preds)

        high_uncertainty = self.uncertainty_engine.identify_high_uncertainty_samples(confidence_intervals)

        # ---------------------------
        # ANOMALY DETECTION
        # ---------------------------
        anomaly_results = self.anomaly_detector.detect_anomalies(X_test_scaled)

        print("Anomaly %:", anomaly_results['is_anomaly'].mean())

        return {
            'uncertainty_predictions': uncertainty_preds,
            'confidence_intervals': confidence_intervals,
            'high_uncertainty_mask': high_uncertainty,
            'anomaly_results': anomaly_results
        }
