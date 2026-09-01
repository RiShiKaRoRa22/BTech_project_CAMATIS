# CAMATIS - Causal-Adaptive Multi-Agent Transport Intelligence System

## Quick Start

### 1. Install Dependencies
```bash
pip install -r camatis_requirements.txt
```

### 2. Verify Setup
```bash
python test_setup.py
```

### 3. Run Pipeline
```bash
python run_camatis.py
```

### 4. Launch Metrics Dashboard
```bash
# Comprehensive metrics dashboard (recommended)
python launch_metrics_dashboard.py

# Or run directly
streamlit run camatis/metrics_dashboard.py

# Original dashboard
streamlit run camatis/dashboard.py
```

## Project Structure

```
camatis/                    # Main pipeline code
├── stage1_data_loader.py          # Data loading
├── stage2_causal_features.py      # Causal intelligence
├── stage3_deep_learning.py        # Deep learning (CDAGT)
├── stage4_meta_ensemble.py        # Meta-ensemble
├── stage5_uncertainty_anomaly.py  # Uncertainty & anomaly detection
├── stage6_optimization.py         # Multi-objective optimization
├── stage7_simulation.py           # Scenario simulation
├── main_pipeline.py               # Pipeline orchestrator
├── evaluation.py                  # Evaluation metrics
├── dashboard.py                   # Streamlit dashboard
└── config.py                      # Configuration

data/                       # Training data
├── train_engineered.csv
└── test_engineered.csv

src/                        # Data preprocessing scripts
├── feature_engineering.py
├── final_preprocessing.py
├── integrate_fleet_data.py
├── integrate_ridership.py
└── prepare_multiday_dataset.py
```

## Output

After running, results will be saved in:
- `camatis/models_saved/` - Trained models
- `camatis/results/` - Evaluation results and plots
- `camatis/logs/` - Execution logs

## Requirements

- Python 3.8+
- PyTorch 2.0.1+
- LightGBM, CatBoost, XGBoost
- See `camatis_requirements.txt` for full list( removed torch due to gpu dependency issues, install according to system configs)



# AGENTS INTEGRATION 
Dataset (45k rows)
        ↓
Feature Engineering
        ↓
CDAGT Deep Learning Model
(Graph + Transformer)
        ↓
Meta Ensemble (LightGBM + CatBoost)
        ↓
Uncertainty Estimation (MC Dropout)
        ↓
Anomaly Detection (Isolation Forest)
        ↓
Multi-Agent Decision System
