"""
CAMATIS Decision Pipeline
Runs trained models + agents WITHOUT retraining
"""

import os
import sys
import numpy as np

# Ensure the repository root is on the Python path when executed as a script
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from camatis.config import *
from camatis.stage1_data_loader import DataLoader
from camatis.stage3_deep_learning import DeepLearningTrainer
from camatis.stage4_meta_ensemble import MetaEnsemble
from camatis.stage5_uncertainty_anomaly import UncertaintyAnomalyPipeline
from camatis.agents.agent_manager import AgentManager
from camatis.optimization.decision_optimizer import DecisionOptimizer

from camatis.execution.action_engine import TransportState, ExecutionEngine
from camatis.simulation.stage7_simulation import ScenarioSimulator

class CAMATISDecisionPipeline:

    def __init__(self):

        print("\n" + "="*70)
        print(" CAMATIS DECISION SYSTEM")
        print("="*70)

        self.data_loader = DataLoader()
        self.meta_ensemble = MetaEnsemble()
        self.uncertainty_pipeline = UncertaintyAnomalyPipeline()
        self.agent_manager = AgentManager()

    def run(self):

        # --------------------------------------------------
        # Load data
        # --------------------------------------------------
        train_df, test_df = self.data_loader.load_data()
        from camatis.stage2_causal_features import CausalFeatureEngine

        causal_engine = CausalFeatureEngine()

        # Build causal graph
        causal_engine.build_causal_graph()

        # Learn relationships
        causal_engine.learn_causal_relationships(train_df)

        # Generate counterfactual features
        
        test_df = causal_engine.generate_counterfactual_features(test_df)

        X_train, X_test, y_train, y_test, feature_names = \
            self.data_loader.prepare_features(train_df, test_df)

        # --------------------------------------------------
        # Load trained ensemble models
        # --------------------------------------------------
        self.meta_ensemble.load_models()

        # --------------------------------------------------
        # Load trained DL model
        # --------------------------------------------------
        dl_trainer = DeepLearningTrainer(input_dim=X_test.shape[1])
        dl_trainer.load_model()

        dl_predictions_test = dl_trainer.predict(X_test)

        # --------------------------------------------------
        # Meta ensemble predictions
        # --------------------------------------------------
        final_predictions = self.meta_ensemble.predict_meta(
            X_test, dl_predictions_test
        )
        


        # ========== ADD DENORMALIZATION HERE ==========
        print("\n" + "="*50)
        print("DENORMALIZING PREDICTIONS")
        print("="*50)

        print(f"[BEFORE] Demand range: {final_predictions['passenger_demand'].min():.2f} to {final_predictions['passenger_demand'].max():.2f}")
        print(f"[BEFORE] Load range: {final_predictions['load_factor'].min():.2f} to {final_predictions['load_factor'].max():.2f}")

        # Denormalize passenger demand
        # Your standardized demand ranges from ~-2 to 2, actual demand should be 50-2000
        # Using a realistic mapping: actual = (normalized + 2) / 4 * 2000 + 50
        demand_normalized = final_predictions['passenger_demand']
        actual_demand = ((demand_normalized + 2) / 4) * 1950 + 50  # Maps -2→50, 2→2000
        final_predictions['passenger_demand'] = np.maximum(actual_demand, 20)  # Minimum 20 passengers

        # Denormalize load factor
        # Standardized load ranges from ~-2 to 2, actual load factor should be 0-1
        load_normalized = final_predictions['load_factor']
        actual_load = (load_normalized + 2) / 4  # Maps -2→0, 2→1
        final_predictions['load_factor'] = np.clip(actual_load, 0.05, 0.95)  # Clamp between 5% and 95%

        print(f"\n[AFTER] Demand range: {final_predictions['passenger_demand'].min():.0f} to {final_predictions['passenger_demand'].max():.0f}")
        print(f"[AFTER] Load range: {final_predictions['load_factor'].min():.3f} to {final_predictions['load_factor'].max():.3f}")
        print("="*50 + "\n")
        demand_scale_factor = 0.25  # Reduce to 25% of original
        final_predictions['passenger_demand'] = final_predictions['passenger_demand'] * demand_scale_factor

        print(f"[SCALED] Demand range: {final_predictions['passenger_demand'].min():.0f} to {final_predictions['passenger_demand'].max():.0f}")

        # --------------------------------------------------
        # Uncertainty + anomaly
        # --------------------------------------------------
        uncertainty_results = self.uncertainty_pipeline.process_inference(
    X_train, X_test, dl_trainer
    )
        


    # ========== DENORMALIZE UNCERTAINTY PREDICTIONS ==========
        if 'demand_mean' in uncertainty_results['uncertainty_predictions']:
            demand_mean_norm = uncertainty_results['uncertainty_predictions']['demand_mean']
            demand_std_norm = uncertainty_results['uncertainty_predictions']['demand_std']
            
            # Denormalize mean
            actual_demand_mean = ((demand_mean_norm + 2) / 4) * 1950 + 50
            uncertainty_results['uncertainty_predictions']['demand_mean'] = np.maximum(actual_demand_mean, 20)
            
            # Scale standard deviation proportionally
            uncertainty_results['uncertainty_predictions']['demand_std'] = demand_std_norm * 500  # Scale std to actual range
            
            # Denormalize load mean
            load_mean_norm = uncertainty_results['uncertainty_predictions']['load_mean']
            actual_load_mean = (load_mean_norm + 2) / 4
            uncertainty_results['uncertainty_predictions']['load_mean'] = np.clip(actual_load_mean, 0.05, 0.95)
            uncertainty_results['uncertainty_predictions']['load_std'] = uncertainty_results['uncertainty_predictions']['load_std'] * 0.3

        # --------------------------------------------------
        # Run agents
        # --------------------------------------------------
        decisions = self.agent_manager.process(

            route_ids=test_df["route_id"].values,

            demand_mean=final_predictions['passenger_demand'],
            load_mean=final_predictions['load_factor'],
            utilization=final_predictions['utilization_encoded'],

            demand_std=uncertainty_results['uncertainty_predictions']['demand_std'],
            load_std=uncertainty_results['uncertainty_predictions']['load_std'],

            cls_probs=uncertainty_results['uncertainty_predictions']['cls_probs'],
            high_uncertainty_mask=uncertainty_results['high_uncertainty_mask'],
            anomaly_mask=uncertainty_results['anomaly_results']['is_anomaly']
        )

      
        # -----------------------------------
# OPTIMIZATION LAYER (NEW)
# -----------------------------------

        optimizer = DecisionOptimizer()

        # Convert decisions → route map
        route_actions = {}

        for d in decisions:
            route = d["route_id"]
            actions = d.get("actions", [d.get("action", "No Action")])
            route_actions.setdefault(route, []).extend(actions)

       # 🔥 MERGE ML + UNCERTAINTY
        merged_predictions = {
            **final_predictions,
            **uncertainty_results['uncertainty_predictions'],
            "cf_load_diff": test_df["cf_load_diff"].values,
            "cf_speed_diff": test_df["cf_speed_diff"].values
        }

        print("\n[DEBUG] Merged predictions sample:")
        print(f"  passenger_demand shape: {merged_predictions['passenger_demand'].shape}")
        print(f"  First 5 demand values: {merged_predictions['passenger_demand'][:5]}")

        optimized = optimizer.optimize_actions(
            route_ids=test_df["route_id"].values,
            predictions=merged_predictions,
            agent_outputs=route_actions
        )

        print("\n=== OPTIMIZATION DEBUG ===")

        for route, plan in list(optimized.items())[:10]:
            print(f"Route {route}: {plan}")

        
        
   
   
    

        # --------------------------------------------------
# ACTION EXECUTION LAYER (ADD HERE)
# --------------------------------------------------

        #from camatis.execution.action_engine import TransportState, ExecutionEngine

        state = TransportState()
        engine = ExecutionEngine(state)

        print("\nExecuting Actions...\n")

        print("\nExecuting Optimized Actions...\n")

        for route, plan in optimized.items():

            print(f"\nRoute {route} Optimization:")

            freq = plan["frequency_multiplier"]
            buses = plan["buses_to_add"]
            reroute = plan["reroute_to"]

            print(f"→ Frequency Multiplier: {round(freq,2)}x")
            print(f"→ Buses to Add: {buses}")

            if reroute is not None:
                print(f"→ Reroute to: Route {reroute}")
           
            engine.execute_optimized(route, plan)

        simulator = ScenarioSimulator()

        sim, sim_results = simulator.run(
            predictions=merged_predictions,
            uncertainty_info=uncertainty_results,
            optimized_actions=optimized,
            test_df=test_df,
            duration=480
        )

        # After simulation runs, build final output
        final_output = []

        # Get all routes from optimized_actions
        all_routes = list(optimized.keys())

        for route in all_routes:
            plan = optimized.get(route, {})
            
            # Find decision entry from agent decisions
            route_decisions = [d for d in decisions if d.get("route_id") == route]
            
            actions = []
            anomaly_flag = False
            uncertainty_flag = False
            
            for d in route_decisions:
                if "actions" in d:
                    actions.extend(d["actions"])
                if d.get("action") == "Investigate Anomaly":
                    anomaly_flag = True
                if d.get("demand_uncertainty", 0) > 0.1:
                    uncertainty_flag = True
            
            actions = list(set(actions)) if actions else ["No action"]
            
            # FIXED: Use route_states from sim instead of routes
            waiting_passengers = 0
            demand_after = 0
            
            if hasattr(sim, 'route_states') and route in sim.route_states:
                state = sim.route_states[route]
                waiting_passengers = state.waiting_passengers
                demand_after = state.current_demand
            elif hasattr(sim, 'dynamic_demand') and route in sim.dynamic_demand:
                demand_after = sim.dynamic_demand.get(route, 0)
                waiting_passengers = sim.route_queues.get(route, 0)
            else:
                # Fallback to predictions
                route_list = list(optimized.keys())
                if route in route_list:
                    idx = route_list.index(route)
                    if idx < len(final_predictions.get('passenger_demand', [])):
                        demand_after = float(final_predictions['passenger_demand'][idx])
                    else:
                        demand_after = 200.0
                else:
                    demand_after = 200.0
            
            final_output.append({
                "route_id": int(route) if route != -1 else -1,
                "demand_after": float(round(demand_after, 2)),
                "waiting_passengers": float(round(waiting_passengers, 2)),
                "actions": [str(a) for a in actions],
                "frequency_multiplier": float(round(plan.get("frequency_multiplier", 1), 2)),
                "buses_added": int(plan.get("buses_to_add", 0)),
                "rerouted_to": int(plan["reroute_to"]) if plan.get("reroute_to") is not None and plan.get("reroute_to") != -1 else None,
                "anomaly": bool(anomaly_flag),
                "high_uncertainty": bool(uncertainty_flag)
            })

        print("\n=== FINAL ROUTE OUTPUT ===")
        for r in final_output[:10]:
            print(r)

        # Save to JSON
        import json
        with open("final_output.json", "w") as f:
            json.dump(final_output, f, indent=2)

        print(f"\n✓ Saved {len(final_output)} routes to final_output.json")
       

        '''print("\n=== ROUTE LEVEL STATE ===")

        for r in list(sim.routes.keys())[:10]:
            print(f"Route {r}: waiting={round(sim.routes[r]['waiting'],2)}")


        print("\n=== DEMAND AFTER DECISIONS ===")

        for r in list(sim.dynamic_demand.keys())[:10]:
            print(f"Route {r}: demand={round(sim.dynamic_demand[r],2)}")'''

        '''print("\n=== SIMULATION RESULTS ===")
        for scenario, result in sim_results.items():
            print(f"{scenario}: {result}")'''


        print(f"\nAgent decisions generated: {len(decisions)}")
        print("\nSample Decisions:")
        for d in decisions[:10]:
            print(d)

        return decisions
        
    

def main():

    np.random.seed(RANDOM_SEED)

    pipeline = CAMATISDecisionPipeline()

    decisions = pipeline.run()

    from collections import defaultdict, Counter

    route_actions = defaultdict(list)

    for d in decisions:
        actions = d.get("actions", [d.get("action", "No Action")])
        route_actions[d["route_id"]].extend(actions)

    route_summary = {}

    for route, acts in route_actions.items():
        if len(acts) > 0:
            route_summary[route] = Counter(acts).most_common(1)[0][0]
        else:
            route_summary[route] = "No Action"

    print("\nRoute-Level Decisions:")
    for r, a in list(route_summary.items())[:10]:
        print(f"Route {r} → {a}")

    # ✅ COUNT DECISIONS PER ROUTE
    action_counts = Counter(route_summary.values())

    print("\nDecision Distribution (Routes):")
    for action, count in action_counts.items():
        percent = (count / len(route_summary)) * 100
        print(f"{action}: {count} routes ({percent:.2f}%)")

    return decisions


if __name__ == "__main__":
    main()