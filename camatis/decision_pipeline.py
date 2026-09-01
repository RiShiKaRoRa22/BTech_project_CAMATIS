'''from camatis.stage1_data_loader import DataLoader
from camatis.stage4_meta_ensemble import MetaEnsemble
from camatis.stage5_uncertainty_anomaly import UncertaintyAnomalyPipeline
from camatis.agents.agent_manager import AgentManager

def run_decision_pipeline():

    # Load new data
    data_loader = DataLoader()
    _, test_df = data_loader.load_data()

    X_test = data_loader.prepare_inference_features(test_df)

    # Load trained models
    meta = MetaEnsemble()
    meta.load_models()

    predictions = meta.predict_meta(X_test)

    # Uncertainty
    uncertainty_pipeline = UncertaintyAnomalyPipeline()
    uncertainty_results = uncertainty_pipeline.process_inference(X_test)

    # Agents
    agent_manager = AgentManager()

    decisions = agent_manager.process(
        route_ids=test_df["route_id"].values,
        demand_mean=predictions["passenger_demand"],
        load_mean=predictions["load_factor"],
        utilization=predictions["utilization_encoded"],
        demand_std=uncertainty_results["uncertainty_predictions"]["demand_std"],
        load_std=uncertainty_results["uncertainty_predictions"]["load_std"],
        ...
    )

    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)

    return decisions'''