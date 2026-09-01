"""
Train baseline models: Linear Regression, Random Forest, LSTM, GAT
Using the same data pipeline as CAMATIS.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camatis.stage1_data_loader import DataLoader as CamatisDataLoader
from camatis.config import RANDOM_SEED, MODELS_DIR, RESULTS_DIR

# Set seeds for reproducibility
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

class LSTMModel(nn.Module):
    """Simple LSTM for regression (demand/load factor)"""
    def __init__(self, input_dim, hidden_dim=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2)
        self.regressor = nn.Linear(hidden_dim, 1)
    
    def forward(self, x):
        # x shape: (batch, seq_len, input_dim) - we treat batch as sequence of 1
        # For tabular data, we unsqueeze to add sequence dimension
        if x.dim() == 2:
            x = x.unsqueeze(1)  # (batch, 1, input_dim)
        lstm_out, _ = self.lstm(x)
        out = self.regressor(lstm_out[:, -1, :])
        return out.squeeze()

class GATModel(nn.Module):
    """Simplified Graph Attention Network (using self-attention as proxy)"""
    def __init__(self, input_dim, hidden_dim=64, num_heads=4):
        super().__init__()
        self.attention = nn.MultiheadAttention(input_dim, num_heads, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, x):
        # x: (batch, input_dim) -> (batch, 1, input_dim)
        if x.dim() == 2:
            x = x.unsqueeze(1)
        attn_out, _ = self.attention(x, x, x)
        out = self.fc(attn_out.squeeze(1))
        return out.squeeze()

def train_lstm(X_train, y_train, X_test, y_test, target_name, task='regression'):
    print(f"\n--- Training LSTM for {target_name} ---")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train).to(device)
    y_train_t = torch.FloatTensor(y_train).to(device)
    X_test_t = torch.FloatTensor(X_test).to(device)
    y_test_t = torch.FloatTensor(y_test).to(device)
    
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    
    model = LSTMModel(input_dim=X_train.shape[1]).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    epochs = 100
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            pred = model(batch_X)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch+1) % 20 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.6f}")
    
    model.eval()
    with torch.no_grad():
        y_pred = model(X_test_t).cpu().numpy()
    y_true = y_test
    
    # Metrics
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    print(f"LSTM {target_name} -> R²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")
    return r2, rmse, mae, y_pred

def train_gat(X_train, y_train, X_test, y_test, target_name):
    print(f"\n--- Training GAT for {target_name} ---")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    X_train_t = torch.FloatTensor(X_train).to(device)
    y_train_t = torch.FloatTensor(y_train).to(device)
    X_test_t = torch.FloatTensor(X_test).to(device)
    y_test_t = torch.FloatTensor(y_test).to(device)
    
    train_dataset = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    
    model = GATModel(input_dim=X_train.shape[1]).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    epochs = 100
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            pred = model(batch_X)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch+1) % 20 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.6f}")
    
    model.eval()
    with torch.no_grad():
        y_pred = model(X_test_t).cpu().numpy()
    y_true = y_test
    
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    print(f"GAT {target_name} -> R²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")
    return r2, rmse, mae, y_pred

def main():
    # Load data using CAMATIS loader
    print("Loading data...")
    data_loader = CamatisDataLoader()
    train_df, test_df = data_loader.load_data()
    X_train, X_test, y_train, y_test, feature_names = data_loader.prepare_features(train_df, test_df)
    
    # Targets
    demand_train = y_train['passenger_demand']
    demand_test = y_test['passenger_demand']
    load_train = y_train['load_factor']
    load_test = y_test['load_factor']
    
    results = {}
    
    # 1. Linear Regression
    print("\n=== Linear Regression ===")
    lr_demand = LinearRegression().fit(X_train, demand_train)
    lr_load = LinearRegression().fit(X_train, load_train)
    
    pred_demand_lr = lr_demand.predict(X_test)
    pred_load_lr = lr_load.predict(X_test)
    
    r2_demand_lr = r2_score(demand_test, pred_demand_lr)
    rmse_demand_lr = np.sqrt(mean_squared_error(demand_test, pred_demand_lr))
    mae_demand_lr = mean_absolute_error(demand_test, pred_demand_lr)
    
    r2_load_lr = r2_score(load_test, pred_load_lr)
    rmse_load_lr = np.sqrt(mean_squared_error(load_test, pred_load_lr))
    mae_load_lr = mean_absolute_error(load_test, pred_load_lr)
    
    print(f"Demand -> R²: {r2_demand_lr:.4f}, RMSE: {rmse_demand_lr:.4f}, MAE: {mae_demand_lr:.4f}")
    print(f"Load   -> R²: {r2_load_lr:.4f}, RMSE: {rmse_load_lr:.4f}, MAE: {mae_load_lr:.4f}")
    results['Linear Regression'] = {'demand_r2': r2_demand_lr, 'load_r2': r2_load_lr}
    
    # 2. Random Forest
    print("\n=== Random Forest ===")
    rf_demand = RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
    rf_load = RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)
    rf_demand.fit(X_train, demand_train)
    rf_load.fit(X_train, load_train)
    
    pred_demand_rf = rf_demand.predict(X_test)
    pred_load_rf = rf_load.predict(X_test)
    
    r2_demand_rf = r2_score(demand_test, pred_demand_rf)
    rmse_demand_rf = np.sqrt(mean_squared_error(demand_test, pred_demand_rf))
    mae_demand_rf = mean_absolute_error(demand_test, pred_demand_rf)
    
    r2_load_rf = r2_score(load_test, pred_load_rf)
    rmse_load_rf = np.sqrt(mean_squared_error(load_test, pred_load_rf))
    mae_load_rf = mean_absolute_error(load_test, pred_load_rf)
    
    print(f"Demand -> R²: {r2_demand_rf:.4f}, RMSE: {rmse_demand_rf:.4f}, MAE: {mae_demand_rf:.4f}")
    print(f"Load   -> R²: {r2_load_rf:.4f}, RMSE: {rmse_load_rf:.4f}, MAE: {mae_load_rf:.4f}")
    results['Random Forest'] = {'demand_r2': r2_demand_rf, 'load_r2': r2_load_rf}
    
    # 3. LSTM
    r2_lstm_demand, rmse_lstm_demand, mae_lstm_demand, _ = train_lstm(
        X_train, demand_train, X_test, demand_test, "demand"
    )
    r2_lstm_load, rmse_lstm_load, mae_lstm_load, _ = train_lstm(
        X_train, load_train, X_test, load_test, "load_factor"
    )
    results['LSTM'] = {'demand_r2': r2_lstm_demand, 'load_r2': r2_lstm_load}
    
    # 4. GAT
    r2_gat_demand, rmse_gat_demand, mae_gat_demand, _ = train_gat(
        X_train, demand_train, X_test, demand_test, "demand"
    )
    r2_gat_load, rmse_gat_load, mae_gat_load, _ = train_gat(
        X_train, load_train, X_test, load_test, "load_factor"
    )
    results['GAT'] = {'demand_r2': r2_gat_demand, 'load_r2': r2_gat_load}
    
    # Print summary table
    print("\n" + "="*60)
    print("BASELINE COMPARISON SUMMARY (R² scores)")
    print("="*60)
    print(f"{'Model':<20} {'Demand R²':<12} {'Load R²':<12}")
    print("-"*44)
    for model, metrics in results.items():
        print(f"{model:<20} {metrics['demand_r2']:<12.4f} {metrics['load_r2']:<12.4f}")
    
    # Optionally, save results to JSON
    import json
    with open(os.path.join(RESULTS_DIR, 'baseline_results.json'), 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\nResults saved to {RESULTS_DIR}/baseline_results.json")
    
    # Generate comparison bar chart
    models = list(results.keys())
    demand_r2 = [results[m]['demand_r2'] for m in models]
    load_r2 = [results[m]['load_r2'] for m in models]
    
    x = np.arange(len(models))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10,6))
    bars1 = ax.bar(x - width/2, demand_r2, width, label='Demand Prediction', color='steelblue')
    bars2 = ax.bar(x + width/2, load_r2, width, label='Load Factor Prediction', color='coral')
    
    ax.set_ylabel('R² Score')
    ax.set_title('Baseline Models Performance Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'baseline_comparison.png'), dpi=300)
    plt.show()
    
    print(f"Comparison chart saved to {RESULTS_DIR}/baseline_comparison.png")

if __name__ == "__main__":
    main()