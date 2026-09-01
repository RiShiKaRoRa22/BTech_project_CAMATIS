"""
View CAMATIS Model Results
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, classification_report
from camatis.config import *
from camatis.stage1_data_loader import DataLoader
from camatis.stage3_deep_learning import DeepLearningTrainer
from camatis.stage4_meta_ensemble import MetaEnsemble

def check_saved_models():
    """Check what models are saved"""
    print("\n" + "=" * 70)
    print(" SAVED MODELS")
    print("=" * 70)
    
    if os.path.exists(MODELS_DIR):
        files = os.listdir(MODELS_DIR)
        print(f"\n📁 Models in {MODELS_DIR}:")
        print("-" * 50)
        for f in sorted(files):
            size = os.path.getsize(os.path.join(MODELS_DIR, f)) / (1024 * 1024)
            print(f"   - {f:<35} ({size:.2f} MB)")
        print(f"\n   Total: {len(files)} files")
    else:
        print(f"❌ Models directory not found: {MODELS_DIR}")

def load_and_evaluate():
    """Load trained models and evaluate on test data"""
    print("\n" + "=" * 70)
    print(" MODEL EVALUATION")
    print("=" * 70)
    
    # 1. Load Data
    print("\n📊 Loading test data...")
    data_loader = DataLoader()
    train_df, test_df = data_loader.load_data()
    X_train, X_test, y_train, y_test, feature_cols = data_loader.prepare_features(train_df, test_df)
    print(f"   Test samples: {X_test.shape[0]}")
    print(f"   Features: {X_test.shape[1]}")
    
    # 2. Load Deep Learning Model (CDAGT)
    print("\n🧠 Loading CDAGT model...")
    dl_trainer = DeepLearningTrainer(input_dim=X_train.shape[1])
    dl_predictions = None
    try:
        dl_trainer.load_model()
        dl_predictions = dl_trainer.predict(X_test)
        print("   ✅ CDAGT model loaded successfully")
    except Exception as e:
        print(f"   ❌ Could not load CDAGT model: {e}")
    
    # 3. Load Ensemble Models
    print("\n🤖 Loading Ensemble models...")
    ensemble = MetaEnsemble()
    ensemble_predictions = None
    try:
        ensemble.load_models()
        if dl_predictions is not None:
            ensemble_predictions = ensemble.predict_meta(X_test, dl_predictions)
            print("   ✅ Ensemble models loaded successfully")
        else:
            print("   ⚠️  Skipping ensemble (no DL predictions available)")
    except Exception as e:
        print(f"   ❌ Could not load Ensemble models: {e}")
    
    # 4. Calculate Metrics
    print("\n📈 Calculating evaluation metrics...")
    
    if ensemble_predictions is not None:
        # Demand Metrics
        y_true_demand = y_test['passenger_demand']
        y_pred_demand = ensemble_predictions['passenger_demand']
        
        demand_rmse = np.sqrt(mean_squared_error(y_true_demand, y_pred_demand))
        demand_mae = mean_absolute_error(y_true_demand, y_pred_demand)
        demand_r2 = r2_score(y_true_demand, y_pred_demand)
        
        # Load Factor Metrics
        y_true_load = y_test['load_factor']
        y_pred_load = ensemble_predictions['load_factor']
        
        load_rmse = np.sqrt(mean_squared_error(y_true_load, y_pred_load))
        load_mae = mean_absolute_error(y_true_load, y_pred_load)
        load_r2 = r2_score(y_true_load, y_pred_load)
        
        # Utilization Metrics
        y_true_util = y_test['utilization_encoded']
        y_pred_util = ensemble_predictions['utilization_encoded']
        
        util_accuracy = accuracy_score(y_true_util, y_pred_util)
        
        # Print Results
        print("\n" + "=" * 70)
        print(" 📊 EVALUATION RESULTS")
        print("=" * 70)
        
        print("\n📈 PASSENGER DEMAND PREDICTION (Regression):")
        print(f"   RMSE: {demand_rmse:.4f}")
        print(f"   MAE:  {demand_mae:.4f}")
        print(f"   R²:   {demand_r2:.4f}")
        
        print("\n📈 LOAD FACTOR PREDICTION (Regression):")
        print(f"   RMSE: {load_rmse:.4f}")
        print(f"   MAE:  {load_mae:.4f}")
        print(f"   R²:   {load_r2:.4f}")
        
        print("\n📈 UTILIZATION STATUS CLASSIFICATION:")
        print(f"   Accuracy: {util_accuracy:.4f} ({util_accuracy*100:.2f}%)")
        
        # Classification Report
        print("\n   Classification Report (per class):")
        print("-" * 60)
        report = classification_report(y_true_util, y_pred_util, 
                                       target_names=['Underutilized (0)', 'Normal (1)', 'Overutilized (2)'],
                                       output_dict=True)
        
        # Print formatted report
        print(f"\n   {'Class':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
        print("   " + "-" * 65)
        for class_name, metrics in report.items():
            if class_name in ['Underutilized (0)', 'Normal (1)', 'Overutilized (2)']:
                print(f"   {class_name:<20} {metrics['precision']:<12.3f} {metrics['recall']:<12.3f} "
                      f"{metrics['f1-score']:<12.3f} {metrics['support']:<10}")
        
        # Overall accuracy
        print(f"\n   Overall Accuracy: {report['accuracy']:.4f} ({report['accuracy']*100:.2f}%)")
        
        return {
            'demand': {'rmse': demand_rmse, 'mae': demand_mae, 'r2': demand_r2},
            'load_factor': {'rmse': load_rmse, 'mae': load_mae, 'r2': load_r2},
            'utilization': {'accuracy': util_accuracy}
        }
    
    elif dl_predictions is not None:
        # Use DL predictions directly
        y_true_demand = y_test['passenger_demand']
        y_pred_demand = dl_predictions['passenger_demand']
        
        demand_rmse = np.sqrt(mean_squared_error(y_true_demand, y_pred_demand))
        demand_mae = mean_absolute_error(y_true_demand, y_pred_demand)
        demand_r2 = r2_score(y_true_demand, y_pred_demand)
        
        print("\n" + "=" * 70)
        print(" 📊 EVALUATION RESULTS (CDAGT Only - No Ensemble)")
        print("=" * 70)
        print(f"\n   Demand RMSE: {demand_rmse:.4f}")
        print(f"   Demand MAE:  {demand_mae:.4f}")
        print(f"   Demand R²:   {demand_r2:.4f}")
        
        return None
    
    else:
        print("❌ No predictions available!")
        return None

def view_feature_importance():
    """View feature importance from saved models"""
    print("\n" + "=" * 70)
    print(" FEATURE IMPORTANCE (LightGBM - Demand)")
    print("=" * 70)
    
    try:
        # Load LightGBM models
        lgb_models = joblib.load(f"{MODELS_DIR}/lgb_models.pkl")
        
        if 'demand' in lgb_models:
            importances = lgb_models['demand'].feature_importances_
            
            # Get feature names
            data_loader = DataLoader()
            train_df, test_df = data_loader.load_data()
            _, _, _, _, feature_cols = data_loader.prepare_features(train_df, test_df)
            
            # Sort by importance
            sorted_idx = np.argsort(importances)[::-1]
            
            print("\n📊 Top 15 Most Important Features:")
            print("-" * 65)
            print(f"   {'Rank':<6} {'Feature Name':<35} {'Importance':<15}")
            print("   " + "-" * 65)
            for i, idx in enumerate(sorted_idx[:15]):
                if idx < len(feature_cols):
                    feature_name = feature_cols[idx]
                    importance = importances[idx]
                    # Add arrows for visual indicators
                    bar = "█" * min(int(importance / max(importances) * 30), 30)
                    print(f"   {i+1:<6} {feature_name:<35} {importance:<8.0f} {bar}")
                    
            # Show bottom features too
            print(f"\n   Bottom 5 features:")
            for i, idx in enumerate(sorted_idx[-5:]):
                if idx < len(feature_cols):
                    print(f"      {feature_cols[idx]} ({importances[idx]:.0f})")
                    
        else:
            print("   ⚠️  No demand model found in lgb_models")
            
    except Exception as e:
        print(f"❌ Could not load feature importance: {e}")

def check_results_directory():
    """Check if results directory has any output files"""
    print("\n" + "=" * 70)
    print(" RESULTS DIRECTORY")
    print("=" * 70)
    
    if os.path.exists(RESULTS_DIR):
        files = os.listdir(RESULTS_DIR)
        if files:
            print(f"\n📁 Results in {RESULTS_DIR}:")
            for f in sorted(files):
                size = os.path.getsize(os.path.join(RESULTS_DIR, f)) / 1024
                print(f"   - {f} ({size:.2f} KB)")
        else:
            print(f"\n   No results files found in {RESULTS_DIR}")
    else:
        print(f"\n   Results directory not found: {RESULTS_DIR}")

def view_simulation_summary():
    """Check if simulation results exist"""
    print("\n" + "=" * 70)
    print(" SIMULATION RESULTS")
    print("=" * 70)
    
    sim_file = os.path.join(RESULTS_DIR, "simulation_results.json")
    if os.path.exists(sim_file):
        try:
            with open(sim_file, 'r') as f:
                data = json.load(f)
            print("\n   ✅ Simulation results found!")
            print(f"   Scenarios simulated: {list(data.keys())}")
        except:
            print("   ⚠️  Could not read simulation results")
    else:
        print("   ⚠️  No simulation results found")

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   CAMATIS - Model Results Viewer                                  ║
    ║                                                                   ║
    ║   View trained model performance and evaluation metrics           ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Check saved models
    check_saved_models()
    
    # 2. Check results directory
    check_results_directory()
    
    # 3. Load and evaluate
    results = load_and_evaluate()
    
    # 4. View feature importance
    view_feature_importance()
    
    # 5. Check simulation results
    view_simulation_summary()
    
    print("\n" + "=" * 70)
    print("✅ Results viewing complete!")
    print("=" * 70)