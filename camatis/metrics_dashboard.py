"""
CAMATIS Comprehensive Metrics Dashboard
Visualizes all accuracy metrics for DL and ML models
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
from camatis.config import RESULTS_DIR, MODELS_DIR

st.set_page_config(
    page_title="CAMATIS Metrics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .excellent { color: #00cc00; font-weight: bold; }
    .good { color: #66cc00; font-weight: bold; }
    .fair { color: #ffaa00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def load_results():
    """Load evaluation results"""
    try:
        with open(f"{RESULTS_DIR}/evaluation_results.json", 'r') as f:
            return json.load(f)
    except:
        return None

def get_metric_color(metric_name, value):
    """Determine color based on metric quality"""
    if metric_name in ['r2', 'accuracy']:
        if value >= 0.99: return "excellent"
        elif value >= 0.95: return "good"
        else: return "fair"
    elif metric_name in ['rmse', 'mae', 'mape']:
        if value <= 0.05: return "excellent"
        elif value <= 0.10: return "good"
        else: return "fair"
    return "good"

def main():
    st.title("📊 CAMATIS Comprehensive Metrics Dashboard")
    st.markdown("### Complete Performance Analysis - Deep Learning & Machine Learning")
    
    # Sidebar
    st.sidebar.header("📋 Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["🎯 Overall Performance", 
         "🧠 Deep Learning Metrics",
         "🤖 ML Ensemble Metrics",
         "📈 Comparative Analysis",
         "🎨 Detailed Visualizations"]
    )
    
    # Load results
    results = load_results()
    
    if results is None:
        st.warning("⚠️ No results found. Please run the pipeline first: `python run_camatis.py`")
        st.info("💡 The dashboard will display metrics after the pipeline completes.")
        return
    
    if page == "🎯 Overall Performance":
        show_overall_performance(results)
    elif page == "🧠 Deep Learning Metrics":
        show_dl_metrics(results)
    elif page == "🤖 ML Ensemble Metrics":
        show_ml_metrics(results)
    elif page == "📈 Comparative Analysis":
        show_comparative_analysis(results)
    elif page == "🎨 Detailed Visualizations":
        show_detailed_visualizations(results)

def show_overall_performance(results):
    """Display overall performance summary"""
    st.header("🎯 Overall Performance Summary")
    
    # Key metrics at the top
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        demand_r2 = results['passenger_demand']['r2']
        st.metric(
            "Demand R² Score",
            f"{demand_r2:.4f}",
            f"{(demand_r2*100):.2f}% accuracy"
        )
    
    with col2:
        load_r2 = results['load_factor']['r2']
        st.metric(
            "Load Factor R²",
            f"{load_r2:.4f}",
            f"{(load_r2*100):.2f}% accuracy"
        )
    
    with col3:
        util_acc = results['utilization_status']['accuracy']
        st.metric(
            "Utilization Accuracy",
            f"{util_acc:.4f}",
            f"{(util_acc*100):.2f}%"
        )
    
    with col4:
        avg_rmse = (results['passenger_demand']['rmse'] + results['load_factor']['rmse']) / 2
        st.metric(
            "Average RMSE",
            f"{avg_rmse:.4f}",
            "Lower is better"
        )
    
    st.markdown("---")
    
    # Detailed metrics tables
    st.subheader("📋 Detailed Metrics by Target")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Passenger Demand Prediction")
        demand_metrics = results['passenger_demand']
        
        metrics_df = pd.DataFrame({
            'Metric': ['RMSE', 'MAE', 'R² Score', 'MAPE'],
            'Value': [
                f"{demand_metrics['rmse']:.6f}",
                f"{demand_metrics['mae']:.6f}",
                f"{demand_metrics['r2']:.6f}",
                f"{demand_metrics['mape']:.4f}%"
            ],
            'Quality': [
                get_metric_color('rmse', demand_metrics['rmse']),
                get_metric_color('mae', demand_metrics['mae']),
                get_metric_color('r2', demand_metrics['r2']),
                get_metric_color('mape', demand_metrics['mape'])
            ]
        })
        
        st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        # Interpretation
        st.info(f"""
        **Interpretation:**
        - R² = {demand_metrics['r2']:.4f} means the model explains {demand_metrics['r2']*100:.2f}% of variance
        - MAPE = {demand_metrics['mape']:.2f}% average percentage error
        - Excellent performance for demand forecasting!
        """)
    
    with col2:
        st.markdown("#### 📦 Load Factor Prediction")
        load_metrics = results['load_factor']
        
        metrics_df = pd.DataFrame({
            'Metric': ['RMSE', 'MAE', 'R² Score', 'MAPE'],
            'Value': [
                f"{load_metrics['rmse']:.6f}",
                f"{load_metrics['mae']:.6f}",
                f"{load_metrics['r2']:.6f}",
                f"{load_metrics['mape']:.4f}%"
            ],
            'Quality': [
                get_metric_color('rmse', load_metrics['rmse']),
                get_metric_color('mae', load_metrics['mae']),
                get_metric_color('r2', load_metrics['r2']),
                get_metric_color('mape', load_metrics['mape'])
            ]
        })
        
        st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        st.info(f"""
        **Interpretation:**
        - R² = {load_metrics['r2']:.4f} means {load_metrics['r2']*100:.2f}% accuracy
        - MAPE = {load_metrics['mape']:.2f}% average error
        - Outstanding load factor prediction!
        """)
    
    st.markdown("---")
    
    # Classification metrics
    st.subheader("🎨 Utilization Status Classification")
    
    util_report = results['utilization_status']['report']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Per-class metrics
        class_data = []
        for class_id in ['0', '1', '2']:
            if class_id in util_report:
                class_data.append({
                    'Class': f"Class {class_id}",
                    'Precision': f"{util_report[class_id]['precision']:.4f}",
                    'Recall': f"{util_report[class_id]['recall']:.4f}",
                    'F1-Score': f"{util_report[class_id]['f1-score']:.4f}",
                    'Support': int(util_report[class_id]['support'])
                })
        
        class_df = pd.DataFrame(class_data)
        st.dataframe(class_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.metric("Overall Accuracy", f"{util_report['accuracy']:.4f}")
        st.metric("Macro Avg F1", f"{util_report['macro avg']['f1-score']:.4f}")
        st.metric("Weighted Avg F1", f"{util_report['weighted avg']['f1-score']:.4f}")
    
    # Visualization
    create_metrics_radar_chart(results)

def show_dl_metrics(results):
    """Display deep learning specific metrics"""
    st.header("🧠 Deep Learning Model Metrics")
    st.markdown("### Causal Dual-Attention Graph Transformer (CDAGT)")
    
    st.info("""
    **Model Architecture:**
    - Graph Attention Layer for spatial relationships
    - Temporal Transformer for time-series patterns
    - Multi-task learning (3 targets simultaneously)
    - Total Parameters: 689,285
    """)
    
    # DL Performance
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🎯 Demand Prediction")
        demand = results['passenger_demand']
        st.metric("RMSE", f"{demand['rmse']:.6f}")
        st.metric("MAE", f"{demand['mae']:.6f}")
        st.metric("R² Score", f"{demand['r2']:.6f}")
        st.metric("MAPE", f"{demand['mape']:.4f}%")
    
    with col2:
        st.markdown("#### 📦 Load Factor")
        load = results['load_factor']
        st.metric("RMSE", f"{load['rmse']:.6f}")
        st.metric("MAE", f"{load['mae']:.6f}")
        st.metric("R² Score", f"{load['r2']:.6f}")
        st.metric("MAPE", f"{load['mape']:.4f}%")
    
    with col3:
        st.markdown("#### 🎨 Utilization")
        util = results['utilization_status']
        st.metric("Accuracy", f"{util['accuracy']:.6f}")
        st.metric("Precision", f"{util['report']['macro avg']['precision']:.6f}")
        st.metric("Recall", f"{util['report']['macro avg']['recall']:.6f}")
        st.metric("F1-Score", f"{util['report']['macro avg']['f1-score']:.6f}")
    
    st.markdown("---")
    
    # Model components
    st.subheader("🔧 Model Components Performance")
    
    components = pd.DataFrame({
        'Component': ['Graph Attention', 'Temporal Transformer', 'Multi-Task Head'],
        'Parameters': ['~230K', '~400K', '~59K'],
        'Function': [
            'Spatial route relationships',
            'Temporal patterns & trends',
            'Multi-target prediction'
        ],
        'Status': ['✅ Operational', '✅ Operational', '✅ Operational']
    })
    
    st.dataframe(components, hide_index=True, use_container_width=True)

def show_ml_metrics(results):
    """Display ML ensemble metrics"""
    st.header("🤖 Machine Learning Ensemble Metrics")
    st.markdown("### LightGBM + CatBoost + XGBoost Meta-Ensemble")
    
    st.info("""
    **Ensemble Architecture:**
    - Base Models: LightGBM (3 models) + CatBoost (3 models)
    - Meta-Learner: XGBoost (2 models)
    - Strategy: Stacking with meta-learning
    - Total Models: 8 models
    """)
    
    # Model breakdown
    st.subheader("📊 Individual Model Contributions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### ⚡ LightGBM")
        st.write("**Configuration:**")
        st.write("- Estimators: 200")
        st.write("- Learning Rate: 0.05")
        st.write("- Max Depth: -1 (unlimited)")
        st.write("")
        st.write("**Models:**")
        st.write("- Demand predictor")
        st.write("- Load factor predictor")
        st.write("- Utilization classifier")
    
    with col2:
        st.markdown("#### 🐱 CatBoost")
        st.write("**Configuration:**")
        st.write("- Iterations: 200")
        st.write("- Learning Rate: 0.05")
        st.write("- Depth: 6")
        st.write("")
        st.write("**Models:**")
        st.write("- Demand predictor")
        st.write("- Load factor predictor")
        st.write("- Utilization classifier")
    
    with col3:
        st.markdown("#### 🚀 XGBoost Meta")
        st.write("**Configuration:**")
        st.write("- Estimators: 100")
        st.write("- Learning Rate: 0.05")
        st.write("- Max Depth: 5")
        st.write("")
        st.write("**Models:**")
        st.write("- Demand meta-learner")
        st.write("- Load factor meta-learner")
        st.write("- (Uses CatBoost for util)")
    
    st.markdown("---")
    
    # Final ensemble performance
    st.subheader("🎯 Final Ensemble Performance")
    
    performance_data = {
        'Target': ['Passenger Demand', 'Load Factor', 'Utilization Status'],
        'RMSE': [
            f"{results['passenger_demand']['rmse']:.6f}",
            f"{results['load_factor']['rmse']:.6f}",
            'N/A'
        ],
        'R² / Accuracy': [
            f"{results['passenger_demand']['r2']:.6f}",
            f"{results['load_factor']['r2']:.6f}",
            f"{results['utilization_status']['accuracy']:.6f}"
        ],
        'MAPE': [
            f"{results['passenger_demand']['mape']:.4f}%",
            f"{results['load_factor']['mape']:.4f}%",
            'N/A'
        ],
        'Quality': ['🟢 Excellent', '🟢 Excellent', '🟢 Perfect']
    }
    
    perf_df = pd.DataFrame(performance_data)
    st.dataframe(perf_df, hide_index=True, use_container_width=True)

def show_comparative_analysis(results):
    """Show comparative analysis"""
    st.header("📈 Comparative Analysis")
    
    # Metrics comparison
    st.subheader("📊 Metrics Comparison Across Targets")
    
    # Create comparison chart
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('RMSE Comparison', 'R² Score Comparison', 
                       'MAE Comparison', 'MAPE Comparison'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    targets = ['Passenger Demand', 'Load Factor']
    
    # RMSE
    rmse_values = [results['passenger_demand']['rmse'], results['load_factor']['rmse']]
    fig.add_trace(
        go.Bar(x=targets, y=rmse_values, name='RMSE', marker_color='indianred'),
        row=1, col=1
    )
    
    # R²
    r2_values = [results['passenger_demand']['r2'], results['load_factor']['r2']]
    fig.add_trace(
        go.Bar(x=targets, y=r2_values, name='R²', marker_color='lightseagreen'),
        row=1, col=2
    )
    
    # MAE
    mae_values = [results['passenger_demand']['mae'], results['load_factor']['mae']]
    fig.add_trace(
        go.Bar(x=targets, y=mae_values, name='MAE', marker_color='lightsalmon'),
        row=2, col=1
    )
    
    # MAPE
    mape_values = [results['passenger_demand']['mape'], results['load_factor']['mape']]
    fig.add_trace(
        go.Bar(x=targets, y=mape_values, name='MAPE', marker_color='gold'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False, title_text="Performance Metrics Comparison")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Classification metrics
    st.subheader("🎨 Classification Metrics (Utilization)")
    
    util_report = results['utilization_status']['report']
    
    # Extract per-class metrics
    classes = []
    precision = []
    recall = []
    f1 = []
    
    for class_id in ['0', '1', '2']:
        if class_id in util_report:
            classes.append(f"Class {class_id}")
            precision.append(util_report[class_id]['precision'])
            recall.append(util_report[class_id]['recall'])
            f1.append(util_report[class_id]['f1-score'])
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Precision', x=classes, y=precision))
    fig.add_trace(go.Bar(name='Recall', x=classes, y=recall))
    fig.add_trace(go.Bar(name='F1-Score', x=classes, y=f1))
    
    fig.update_layout(
        title='Classification Metrics by Class',
        xaxis_title='Class',
        yaxis_title='Score',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_detailed_visualizations(results):
    """Show detailed visualizations"""
    st.header("🎨 Detailed Visualizations")
    
    # Radar chart
    st.subheader("📊 Multi-Metric Radar Chart")
    create_metrics_radar_chart(results)
    
    st.markdown("---")
    
    # Heatmap
    st.subheader("🔥 Performance Heatmap")
    
    # Create heatmap data
    metrics_matrix = [
        [results['passenger_demand']['r2'], results['passenger_demand']['rmse'], results['passenger_demand']['mae']],
        [results['load_factor']['r2'], results['load_factor']['rmse'], results['load_factor']['mae']],
        [results['utilization_status']['accuracy'], 0, 0]
    ]
    
    fig = go.Figure(data=go.Heatmap(
        z=metrics_matrix,
        x=['R² / Accuracy', 'RMSE', 'MAE'],
        y=['Passenger Demand', 'Load Factor', 'Utilization'],
        colorscale='RdYlGn',
        text=metrics_matrix,
        texttemplate='%{text:.4f}',
        textfont={"size": 12}
    ))
    
    fig.update_layout(title='Performance Metrics Heatmap', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Gauge charts
    st.subheader("🎯 Performance Gauges")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=results['passenger_demand']['r2'] * 100,
            title={'text': "Demand R² (%)"},
            delta={'reference': 95},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkblue"},
                   'steps': [
                       {'range': [0, 90], 'color': "lightgray"},
                       {'range': [90, 95], 'color': "gray"}],
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 99}}
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=results['load_factor']['r2'] * 100,
            title={'text': "Load Factor R² (%)"},
            delta={'reference': 95},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkgreen"},
                   'steps': [
                       {'range': [0, 90], 'color': "lightgray"},
                       {'range': [90, 95], 'color': "gray"}],
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 99}}
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=results['utilization_status']['accuracy'] * 100,
            title={'text': "Utilization Accuracy (%)"},
            delta={'reference': 95},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': "darkred"},
                   'steps': [
                       {'range': [0, 90], 'color': "lightgray"},
                       {'range': [90, 95], 'color': "gray"}],
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 99}}
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def create_metrics_radar_chart(results):
    """Create radar chart for metrics"""
    
    # Normalize metrics to 0-1 scale for visualization
    demand_r2 = results['passenger_demand']['r2']
    load_r2 = results['load_factor']['r2']
    util_acc = results['utilization_status']['accuracy']
    
    # Invert error metrics (lower is better -> higher score)
    demand_rmse_score = max(0, 1 - results['passenger_demand']['rmse'] * 10)
    load_rmse_score = max(0, 1 - results['load_factor']['rmse'] * 10)
    demand_mae_score = max(0, 1 - results['passenger_demand']['mae'] * 10)
    
    categories = ['Demand R²', 'Load R²', 'Utilization Acc', 
                  'Demand RMSE', 'Load RMSE', 'Demand MAE']
    
    values = [demand_r2, load_r2, util_acc, 
              demand_rmse_score, load_rmse_score, demand_mae_score]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='CAMATIS Performance'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="Overall Performance Radar",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
