"""
CAMATIS Main Pipeline
Causal-Adaptive Multi-Agent Transport Intelligence System
Complete ML/DL Pipeline Orchestrator
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')

from camatis.config import *
from camatis.stage1_data_loader import DataLoader
from camatis.stage2_causal_features import CausalFeatureEngine
from camatis.stage3_deep_learning import DeepLearningTrainer
from camatis.stage4_meta_ensemble import MetaEnsemble
from camatis.stage5_uncertainty_anomaly import UncertaintyAnomalyPipeline
from camatis.optimization.stage6_optimization import MultiObjectiveOptimizer
from camatis.simulation.stage7_simulation import ScenarioSimulator
from camatis.evaluation import ModelEvaluator

class CAMATISPipeline:
    """Complete CAMATIS Pipeline"""
    
    def __init__(self):
        print("\n" + "="*70)
        print(" CAMATIS - Causal-Adaptive Multi-Agent Transport Intelligence System")
        print("="*70)
        
        self.data_loader = DataLoader()
        self.causal_engine = CausalFeatureEngine()
        self.dl_trainer = None
        self.meta_ensemble = MetaEnsemble()
        self.uncertainty_pipeline = UncertaintyAnomalyPipeline()
        self.optimizer = MultiObjectiveOptimizer()
        self.simulator = ScenarioSimulator()
        self.evaluator = ModelEvaluator()
        
        self.train_df = None
        self.test_df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = None
        
    def run_stage1_data_foundation(self):
        """Stage 1: Load and prepare data"""
        print("\n" + "="*70)
        print("STAGE 1: DATA FOUNDATION")
        print("="*70)
        
        # Load data
        self.train_df, self.test_df = self.data_loader.load_data()
        
        # Prepare features
        self.X_train, self.X_test, self.y_train, self.y_test, self.feature_names = \
            self.data_loader.prepare_features(self.train_df, self.test_df)
        
        # Save preprocessor
        self.data_loader.save_preprocessor()
        
        print("✓ Stage 1 completed!")
        
    def run_stage2_causal_features(self):
        """Stage 2: Causal feature engineering"""
        print("\n" + "="*70)
        print("STAGE 2: CAUSAL FEATURE INTELLIGENCE")
        print("="*70)
        
        # Build causal graph
        self.causal_engine.build_causal_graph()
        
        # Learn causal weights
        self.causal_engine.learn_causal_weights(self.train_df, self.feature_names)
        
        # Generate counterfactual features (optional enhancement)
        # train_df_cf = self.causal_engine.generate_counterfactual_features(self.train_df)
        
        print("✓ Stage 2 completed!")
        
    def run_stage3_deep_learning(self):
        """Stage 3: Train deep learning model"""
        print("\n" + "="*70)
        print("STAGE 3: CAUSAL DUAL-ATTENTION GRAPH TRANSFORMER (CDAGT)")
        print("="*70)
        
        # Initialize trainer
        self.dl_trainer = DeepLearningTrainer(input_dim=self.X_train.shape[1])
        
        # Train model
        self.dl_trainer.train(self.X_train, self.y_train)
        
        # Get predictions
        self.dl_predictions_train = self.dl_trainer.predict(self.X_train)
        self.dl_predictions_test = self.dl_trainer.predict(self.X_test)
        
        print("✓ Stage 3 completed!")
        
    def run_stage4_meta_ensemble(self):
        """Stage 4: Train meta-ensemble"""
        print("\n" + "="*70)
        print("STAGE 4: META-ENSEMBLE STABILIZATION")
        print("="*70)
        
        # Train base models
        self.meta_ensemble.train_base_models(self.X_train, self.y_train)
        
        # Train meta-learner
        self.meta_ensemble.train_meta_learner(
            self.X_train, self.y_train, self.dl_predictions_train
        )
        
        # Get final predictions
        self.final_predictions_test = self.meta_ensemble.predict_meta(
            self.X_test, self.dl_predictions_test
        )
        
        # Save models
        self.meta_ensemble.save_models()
        
        print("✓ Stage 4 completed!")
        
    def run_stage5_uncertainty_anomaly(self):
        """Stage 5: Uncertainty and anomaly detection"""
        print("\n" + "="*70)
        print("STAGE 5: UNCERTAINTY & ANOMALY INTELLIGENCE")
        print("="*70)
        
        # Run uncertainty and anomaly pipeline
        self.uncertainty_results = self.uncertainty_pipeline.process(
            self.X_train, self.X_test, self.dl_trainer
        )
        
        # Save anomaly detector
        self.uncertainty_pipeline.anomaly_detector.save_detector()
        
        print("✓ Stage 5 completed!")
        
    def run_stage6_optimization(self):
        """Stage 6: Multi-objective optimization"""
        print("\n" + "="*70)
        print("STAGE 6: MULTI-OBJECTIVE OPTIMIZATION")
        print("="*70)
        
        # Run optimization
        opt_results = self.optimizer.optimize(self.final_predictions_test)
        
        # Get best solution
        best_solution = self.optimizer.get_best_solution()
        print(f"\nBest solution objectives: {best_solution['objectives']}")
        
        print("✓ Stage 6 completed!")
        
    def run_stage7_simulation(self):
        """Stage 7: Scenario simulation"""
        print("\n" + "="*70)
        print("STAGE 7: SCENARIO SIMULATION ENGINE")
        print("="*70)
        
        # Run all scenarios
        simulation_results = self.simulator.run_all_scenarios(
            self.final_predictions_test,
            self.uncertainty_results
        )
        
        # Compare scenarios
        self.simulator.compare_scenarios()
        
        print("✓ Stage 7 completed!")
        
        return simulation_results
        
    def evaluate_pipeline(self):
        """Evaluate complete pipeline"""
        print("\n" + "="*70)
        print("PIPELINE EVALUATION")
        print("="*70)
        
        # Evaluate predictions
        eval_results = self.evaluator.evaluate_all(self.y_test, self.final_predictions_test)
        
        # Plot results
        self.evaluator.plot_predictions(self.y_test, self.final_predictions_test)
        
        # Plot uncertainty
        self.evaluator.plot_uncertainty(
            self.uncertainty_results['uncertainty_predictions']['demand_mean'],
            self.uncertainty_results['confidence_intervals']
        )
        
        # Save results
        self.evaluator.save_results()
        
        print("✓ Evaluation completed!")
        
        return eval_results
    
    def run_complete_pipeline(self):
        """Run all stages sequentially"""
        print("\n🚀 Starting CAMATIS Complete Pipeline...\n")
        
        try:
            # Stage 1: Data Foundation
            self.run_stage1_data_foundation()
            
            # Stage 2: Causal Features
            self.run_stage2_causal_features()
            
            # Stage 3: Deep Learning
            self.run_stage3_deep_learning()
            
            # Stage 4: Meta-Ensemble
            self.run_stage4_meta_ensemble()
            
            # Stage 5: Uncertainty & Anomaly
            self.run_stage5_uncertainty_anomaly()
            
            # Stage 6: Optimization
            self.run_stage6_optimization()
            
            # Stage 7: Simulation
            simulation_results = self.run_stage7_simulation()
            
            # Final Evaluation
            eval_results = self.evaluate_pipeline()
            
            print("\n" + "="*70)
            print("✅ CAMATIS PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"\nResults saved in: {RESULTS_DIR}/")
            print(f"Models saved in: {MODELS_DIR}/")
            
            return {
                'evaluation': eval_results,
                'simulation': simulation_results,
                'uncertainty': self.uncertainty_results
            }
            
        except Exception as e:
            print(f"\n❌ Pipeline failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

def main():
    """Main entry point"""
    # Set random seeds
    np.random.seed(RANDOM_SEED)
    
    # Initialize and run pipeline
    pipeline = CAMATISPipeline()
    results = pipeline.run_complete_pipeline()
    
    return pipeline, results

if __name__ == "__main__":
    pipeline, results = main()


