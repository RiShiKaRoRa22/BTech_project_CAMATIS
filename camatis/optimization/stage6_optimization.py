"""
Stage 6: Multi-Objective Optimization
Causal-Aware NSGA-III for transport optimization
"""

import numpy as np
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions
from camatis.config import *

class TransportOptimizationProblem(Problem):
    """
    Multi-objective optimization problem:
    1. Minimize waiting time
    2. Minimize fuel cost
    3. Maximize fleet utilization
    4. Maximize service fairness
    """
    
    def __init__(self, predictions, causal_constraints=None):
        self.predictions = predictions
        self.causal_constraints = causal_constraints
        
        # Decision variables: bus frequency adjustments per route
        n_routes = len(self.predictions['passenger_demand'])  # Simplified
        
        super().__init__(
            n_var=n_routes,
            n_obj=4,
            n_constr=0,  # No constraints
            xl=0.5,  # Min frequency multiplier
            xu = 1.6   # Max frequency multiplier
        )
    
    def _evaluate(self, X, out, *args, **kwargs):
        """Evaluate objectives"""
        n_solutions = X.shape[0]
        
        # Objective 1: Waiting time (minimize)
        waiting_time = self._compute_waiting_time(X)
        
        # Objective 2: Fuel cost (minimize)
        fuel_cost = self._compute_fuel_cost(X)
        
        # Objective 3: Utilization (maximize -> minimize negative)
        utilization = -self._compute_utilization(X)
        
        # Objective 4: Fairness (maximize -> minimize negative)
        fairness = -self._compute_fairness(X)
        
        out["F"] = np.column_stack([waiting_time, fuel_cost, utilization, fairness])
    
    def _compute_waiting_time(self, X):

        demand = self.predictions['passenger_demand']

        # ✅ ADD THIS LINE (uncertainty)
        uncertainty = self.predictions.get(
            'demand_std',
            np.zeros_like(demand)
        )

        # ✅ UPDATED FORMULA
        return np.mean(
            (demand / (X + 0.1)) * (1 + uncertainty),
            axis=1
        )
        

    def _compute_fuel_cost(self, X):

        demand = self.predictions['passenger_demand']

        return np.sum((X ** 2) * demand * 0.1, axis=1)
        
    def _compute_utilization(self, X):

        load = self.predictions['load_factor']

        return np.mean(load * X, axis=1)
    
    def _compute_fairness(self, X):
        """Compute service fairness (minimize variance)"""
        return -np.var(X, axis=1)

class MultiObjectiveOptimizer:
    def __init__(self):
        self.algorithm = None
        self.results = None
        
    def optimize(self, predictions, causal_constraints=None):
        """
        Run Causal-Aware NSGA-III optimization
        """
        print("Running multi-objective optimization...")
        
        # Define problem
        problem = TransportOptimizationProblem(predictions, causal_constraints)
        
        # Reference directions for NSGA-III
        ref_dirs = get_reference_directions("das-dennis", 4, n_partitions=12)
        
        # Initialize algorithm
        self.algorithm = NSGA3(
            pop_size=POPULATION_SIZE,
            ref_dirs=ref_dirs
        )
        
        # Run optimization
        self.results = minimize(
            problem,
            self.algorithm,
            ('n_gen', N_GENERATIONS),
            seed=RANDOM_SEED,
            verbose=True
        )
        
        print(f"Optimization completed!")
        print(f"Found {len(self.results.F)} Pareto-optimal solutions")
        
        return self.results
    
    def get_best_solution(self, preference_weights=None):
        """
        Get best solution based on preference weights
        Default: equal weights
        """
        if preference_weights is None:
            preference_weights = np.array([0.25, 0.25, 0.25, 0.25])
        
        # Normalize objectives
        F_norm = (self.results.F - self.results.F.min(axis=0)) / (
            self.results.F.max(axis=0) - self.results.F.min(axis=0) + 1e-8
        )
        
        # Weighted sum
        scores = F_norm @ preference_weights
        best_idx = np.argmin(scores)
        
        return {
            'solution': self.results.X[best_idx],
            'objectives': self.results.F[best_idx],
            'index': best_idx
        }
    
    def get_pareto_front(self):
        """Get all Pareto-optimal solutions"""
        return {
            'solutions': self.results.X,
            'objectives': self.results.F
        }
