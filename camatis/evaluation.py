"""
Evaluation Module
Comprehensive evaluation metrics and visualization
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import json
from camatis.config import *

class ModelEvaluator:
    def __init__(self):
        self.results = {}
        
    def evaluate_regression(self, y_true, y_pred, task_name):
        """Evaluate regression tasks"""
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
        }
        
        self.results[task_name] = metrics
        return metrics
    
    def evaluate_classification(self, y_true, y_pred, task_name):
        """Evaluate classification tasks"""
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'report': classification_report(y_true, y_pred, output_dict=True)
        }
        
        self.results[task_name] = metrics
        return metrics
    
    def evaluate_all(self, y_true, y_pred):
        """Evaluate all tasks"""
        print("\n" + "="*50)
        print("MODEL EVALUATION RESULTS")
        print("="*50)
        
        # Passenger Demand
        print("\n--- Passenger Demand Prediction ---")
        demand_metrics = self.evaluate_regression(
            y_true['passenger_demand'],
            y_pred['passenger_demand'],
            'passenger_demand'
        )
        for metric, value in demand_metrics.items():
            print(f"{metric.upper()}: {value:.4f}")
        
        # Load Factor
        print("\n--- Load Factor Prediction ---")
        load_metrics = self.evaluate_regression(
            y_true['load_factor'],
            y_pred['load_factor'],
            'load_factor'
        )
        for metric, value in load_metrics.items():
            print(f"{metric.upper()}: {value:.4f}")
        
        # Utilization Status
        print("\n--- Utilization Status Classification ---")
        util_metrics = self.evaluate_classification(
            y_true['utilization_encoded'],
            y_pred['utilization_encoded'],
            'utilization_status'
        )
        print(f"ACCURACY: {util_metrics['accuracy']:.4f}")
        
        return self.results
    
    def plot_predictions(self, y_true, y_pred, save_path=None):
        """Plot prediction vs actual"""
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # Passenger Demand
        axes[0].scatter(y_true['passenger_demand'], y_pred['passenger_demand'], alpha=0.5)
        axes[0].plot([y_true['passenger_demand'].min(), y_true['passenger_demand'].max()],
                     [y_true['passenger_demand'].min(), y_true['passenger_demand'].max()],
                     'r--', lw=2)
        axes[0].set_xlabel('Actual Demand')
        axes[0].set_ylabel('Predicted Demand')
        axes[0].set_title('Passenger Demand Prediction')
        axes[0].grid(True, alpha=0.3)
        
        # Load Factor
        axes[1].scatter(y_true['load_factor'], y_pred['load_factor'], alpha=0.5)
        axes[1].plot([y_true['load_factor'].min(), y_true['load_factor'].max()],
                     [y_true['load_factor'].min(), y_true['load_factor'].max()],
                     'r--', lw=2)
        axes[1].set_xlabel('Actual Load Factor')
        axes[1].set_ylabel('Predicted Load Factor')
        axes[1].set_title('Load Factor Prediction')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
        else:
            plt.savefig(f"{RESULTS_DIR}/predictions_plot.png", dpi=300, bbox_inches='tight')
        
        plt.close()
    
    def plot_uncertainty(self, predictions, confidence_intervals, save_path=None):
        """Plot predictions with uncertainty bands"""
        n_samples = min(500, len(predictions))
        indices = np.arange(n_samples)
        
        fig, axes = plt.subplots(2, 1, figsize=(15, 10))
        
        # Demand with uncertainty
        axes[0].plot(indices, predictions[:n_samples], 'b-', label='Prediction', alpha=0.7)
        axes[0].fill_between(
            indices,
            confidence_intervals['demand_lower'][:n_samples],
            confidence_intervals['demand_upper'][:n_samples],
            alpha=0.3,
            label='95% Confidence Interval'
        )
        axes[0].set_xlabel('Sample Index')
        axes[0].set_ylabel('Passenger Demand')
        axes[0].set_title('Demand Prediction with Uncertainty')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Load Factor with uncertainty
        axes[1].plot(indices, predictions[:n_samples], 'g-', label='Prediction', alpha=0.7)
        axes[1].fill_between(
            indices,
            confidence_intervals['load_lower'][:n_samples],
            confidence_intervals['load_upper'][:n_samples],
            alpha=0.3,
            label='95% Confidence Interval'
        )
        axes[1].set_xlabel('Sample Index')
        axes[1].set_ylabel('Load Factor')
        axes[1].set_title('Load Factor Prediction with Uncertainty')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(f"{RESULTS_DIR}/uncertainty_plot.png", dpi=300, bbox_inches='tight')
        
        plt.close()
    
    def save_results(self, filename='evaluation_results.json'):
        """Save evaluation results"""
        filepath = f"{RESULTS_DIR}/{filename}"
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"Results saved to {filepath}")
