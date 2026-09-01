"""
Stage 3: Causal Dual-Attention Graph Transformer (CDAGT)
Core deep learning model with graph and temporal attention
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
import numpy as np
from camatis.config import *

class CausalGraphAttention(nn.Module):
    """Graph attention layer for route relationships"""
    def __init__(self, in_features, out_features, num_heads=4):
        super().__init__()
        self.num_heads = num_heads
        self.out_features = out_features
        
        self.W = nn.Linear(in_features, out_features * num_heads)
        self.a = nn.Parameter(torch.randn(num_heads, 2 * out_features))
        
    def forward(self, x, adj_matrix=None):
        batch_size = x.size(0)
        h = self.W(x).view(batch_size, self.num_heads, self.out_features)
        
        h_concat = torch.cat([h, h], dim=-1)
        e = torch.matmul(h_concat, self.a.t())
        attention = F.softmax(e, dim=-1)
        
        h_prime = torch.bmm(attention, h)
        h_prime = h_prime.mean(dim=1)
        return h_prime

class TemporalTransformer(nn.Module):
    """Temporal transformer for time-series patterns"""
    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        self.attention = nn.MultiheadAttention(d_model, num_heads, dropout=dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model)
        )
        
    def forward(self, x):
        attn_out, _ = self.attention(x, x, x)
        x = self.norm1(x + attn_out)
        ffn_out = self.ffn(x)
        x = self.norm2(x + ffn_out)
        return x

class CDAGT(nn.Module):
    """Causal Dual-Attention Graph Transformer"""
    def __init__(self, input_dim=45, hidden_dim=256, num_layers=3, num_heads=4, dropout=0.3):
        super().__init__()
        
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        self.graph_attention = CausalGraphAttention(hidden_dim, hidden_dim, num_heads)
        
        self.temporal_layers = nn.ModuleList([
            TemporalTransformer(hidden_dim, num_heads, dropout)
            for _ in range(num_layers)
        ])
        
        self.demand_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        self.load_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        self.utilization_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 3)
        )
        
        self.dropout = nn.Dropout(dropout)
        
        print(f"\n🧠 CDAGT Model Initialized:")
        print(f"   Input Features: {input_dim}")
        print(f"   Hidden Dimension: {hidden_dim}")
        print(f"   Transformer Layers: {num_layers}")
        print(f"   Attention Heads: {num_heads}")
        print(f"   Total Parameters: {sum(p.numel() for p in self.parameters()):,}")
        
    def forward(self, x, mc_dropout=False):
        h = self.input_projection(x)
        h = F.relu(h)
        h = self.graph_attention(h)
        h = self.dropout(h)
        
        for layer in self.temporal_layers:
            h = layer(h.unsqueeze(0)).squeeze(0)
            if mc_dropout or self.training:
                h = self.dropout(h)
        
        demand_pred = self.demand_head(h).squeeze(-1)
        load_pred = self.load_head(h).squeeze(-1)
        util_pred = self.utilization_head(h)
        
        return demand_pred, load_pred, util_pred


class DeepLearningTrainer:
    def __init__(self, input_dim=45):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.model = CDAGT(
            input_dim=input_dim,
            hidden_dim=DEEP_LEARNING_CONFIG.get('hidden_dim', 256),
            num_layers=DEEP_LEARNING_CONFIG.get('num_layers', 3),
            num_heads=DEEP_LEARNING_CONFIG.get('num_heads', 4),
            dropout=DEEP_LEARNING_CONFIG.get('dropout', 0.3)
        ).to(self.device)
        
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=DEEP_LEARNING_CONFIG.get('learning_rate', 0.001)
        )
        
        # Learning Rate Scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=DEEP_LEARNING_CONFIG.get('scheduler_factor', 0.5),
            patience=DEEP_LEARNING_CONFIG.get('scheduler_patience', 5)
        )
        
        self.criterion_regression = nn.MSELoss()
        
        # NEW: Class-weighted cross-entropy loss for utilization
        class_weights = DEEP_LEARNING_CONFIG.get('class_weights', {0: 1.0, 1: 3.0, 2: 1.5})
        weight_tensor = torch.tensor([class_weights[0], class_weights[1], class_weights[2]], 
                                      dtype=torch.float32).to(self.device)
        self.criterion_classification = nn.CrossEntropyLoss(weight=weight_tensor)
        
        print(f"✅ DeepLearningTrainer initialized with {input_dim} input features")
        print(f"   Device: {self.device}")
        print(f"   Scheduler: ReduceLROnPlateau (factor=0.5, patience=5)")
        print(f"   Class Weights: {class_weights}")
        
    def train(self, X_train, y_train, X_val=None, y_val=None):
        print(f"\n🚀 Training CDAGT on device: {self.device}")
        print(f"   Training samples: {X_train.shape[0]}")
        print(f"   Features: {X_train.shape[1]}")
        print("=" * 50)
        
        X_tensor = torch.FloatTensor(X_train).to(self.device)
        y_demand = torch.FloatTensor(y_train['passenger_demand']).to(self.device)
        y_load = torch.FloatTensor(y_train['load_factor']).to(self.device)
        y_util = torch.LongTensor(y_train['utilization_encoded']).to(self.device)
        
        dataset = TensorDataset(X_tensor, y_demand, y_load, y_util)
        dataloader = DataLoader(
            dataset, 
            batch_size=DEEP_LEARNING_CONFIG.get('batch_size', 256), 
            shuffle=True
        )
        
        best_loss = float('inf')
        patience_counter = 0
        epochs = DEEP_LEARNING_CONFIG.get('epochs', 100)
        patience = DEEP_LEARNING_CONFIG.get('patience', 15)
        
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            demand_loss_sum = 0
            load_loss_sum = 0
            util_loss_sum = 0
            
            for batch_X, batch_demand, batch_load, batch_util in dataloader:
                self.optimizer.zero_grad()
                
                pred_demand, pred_load, pred_util = self.model(batch_X)
                
                loss_demand = self.criterion_regression(pred_demand, batch_demand)
                loss_load = self.criterion_regression(pred_load, batch_load)
                loss_util = self.criterion_classification(pred_util, batch_util)
                
                loss = loss_demand + loss_load + loss_util
                
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
                demand_loss_sum += loss_demand.item()
                load_loss_sum += loss_load.item()
                util_loss_sum += loss_util.item()
            
            avg_loss = total_loss / len(dataloader)
            avg_demand_loss = demand_loss_sum / len(dataloader)
            avg_load_loss = load_loss_sum / len(dataloader)
            avg_util_loss = util_loss_sum / len(dataloader)
            
            self.scheduler.step(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                current_lr = self.optimizer.param_groups[0]['lr']
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f} "
                      f"(Demand: {avg_demand_loss:.4f}, Load: {avg_load_loss:.4f}, Util: {avg_util_loss:.4f}) "
                      f"LR: {current_lr:.6f}")
            
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
                torch.save(self.model.state_dict(), f"{MODELS_DIR}/cdagt_best.pth")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"🛑 Early stopping at epoch {epoch+1}")
                    break
        
        print(f"✅ Training completed! Best loss: {best_loss:.4f}")
        self.save_model()

    def save_model(self, path=None):
        if path is None:
            path = os.path.join(MODELS_DIR, "cdagt_best.pth")
        torch.save(self.model.state_dict(), path)
        print(f"✅ Model saved to {path}")

    def load_model(self, path=None):
        if path is None:
            path = os.path.join(MODELS_DIR, "cdagt_best.pth")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model checkpoint not found: {path}")
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.model.eval()
        print(f"✅ Model loaded from {path}")

    def predict(self, X):
        self.model.eval()
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        with torch.no_grad():
            pred_demand, pred_load, pred_util = self.model(X_tensor)
            pred_util_class = torch.argmax(pred_util, dim=1)
        
        return {
            'passenger_demand': pred_demand.cpu().numpy(),
            'load_factor': pred_load.cpu().numpy(),
            'utilization_encoded': pred_util_class.cpu().numpy()
        }
    
    def predict_with_uncertainty(self, X, n_samples=MC_DROPOUT_SAMPLES):
        self.model.train()
        X_tensor = torch.FloatTensor(X).to(self.device)
        
        demand_samples = []
        load_samples = []
        cls_samples = []
        
        for _ in range(n_samples):
            with torch.no_grad():
                pred_demand, pred_load, pred_util = self.model(X_tensor, mc_dropout=True)
                demand_samples.append(pred_demand.cpu().numpy())
                load_samples.append(pred_load.cpu().numpy())
                probs = torch.softmax(pred_util, dim=1)
                cls_samples.append(probs.cpu().numpy())
        
        demand_samples = np.array(demand_samples)
        load_samples = np.array(load_samples)
        cls_samples = np.array(cls_samples)
        
        return {
            'demand_mean': demand_samples.mean(axis=0),
            'demand_std': demand_samples.std(axis=0),
            'load_mean': load_samples.mean(axis=0),
            'load_std': load_samples.std(axis=0),
            'cls_probs': cls_samples.mean(axis=0)
        }