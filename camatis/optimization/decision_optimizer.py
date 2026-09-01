import numpy as np
import sys
import os
from camatis.optimization.stage6_optimization import MultiObjectiveOptimizer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.services.config_service import config_service

class DecisionOptimizer:

    def __init__(self):
        self.optimizer = MultiObjectiveOptimizer()

    
    def optimize_actions(self, route_ids, predictions, agent_outputs):
        print("\n" + "="*70)
        print(" OPTIMIZATION LAYER - RESOURCE ALLOCATION")
        print("="*70)
        
        # Load current settings
        try:
            config = config_service.get_config()
            max_buses = config.max_buses
            freq_limit = config.frequency_limit
            opt_pref = config.optimization_preference
        except:
            max_buses = 30
            freq_limit = 12
            opt_pref = "balanced"
        
        print(f"[SETTINGS] Max buses per route: {max_buses}")
        print(f"[SETTINGS] Frequency limit: {freq_limit} buses/hour (base 4)")
        print(f"[SETTINGS] Optimization preference: {opt_pref}")
        
        unique_routes = list(set(route_ids))
        
        # Build reduced predictions
        reduced_predictions = {
            "passenger_demand": [],
            "load_factor": [],
            "demand_std": []  
        }

        for route in unique_routes:
            indices = np.where(route_ids == route)[0]
            reduced_predictions["passenger_demand"].append(
                np.mean(predictions['passenger_demand'][indices])
            )
            reduced_predictions["load_factor"].append(
                np.mean(predictions['load_factor'][indices])
            )
            reduced_predictions["demand_std"].append(
                np.mean(predictions['demand_std'][indices])
            )

        reduced_predictions["passenger_demand"] = np.array(reduced_predictions["passenger_demand"])
        reduced_predictions["load_factor"] = np.array(reduced_predictions["load_factor"])
        reduced_predictions["demand_std"] = np.array(reduced_predictions["demand_std"])

        # Set NSGA-III weights based on preference
        if opt_pref == "cost":
            preference_weights = np.array([0.5, 0.3, 0.1, 0.1])
            print("[OPT] Cost minimization mode - prioritizing fuel efficiency")
        elif opt_pref == "demand":
            preference_weights = np.array([0.1, 0.1, 0.6, 0.2])
            print("[OPT] Demand coverage mode - prioritizing passenger service")
        elif opt_pref == "efficiency":
            preference_weights = np.array([0.2, 0.2, 0.5, 0.1])
            print("[OPT] Efficiency mode - prioritizing utilization")
        else:  # balanced
            preference_weights = np.array([0.25, 0.25, 0.25, 0.25])
            print("[OPT] Balanced mode - equal weights")
        
        # Pass weights to optimizer
        self.optimizer.preference_weights = preference_weights
        results = self.optimizer.optimize(reduced_predictions)
        best = self.optimizer.get_best_solution()
        freq_solution = best['solution']

        optimized_actions = {}
        
        print("\n📊 Calculating Route Optimizations:")
        total_buses_added = 0
        
        for i, route in enumerate(unique_routes):
            indices = np.where(route_ids == route)[0]
            actions = agent_outputs.get(route, [])
            
            hourly_demand = reduced_predictions['passenger_demand'][i]
            load_factor = reduced_predictions['load_factor'][i] 
            current_buses = 1  # Base is 1 bus per route
            
            # Dynamic bus allocation based on demand (capped by max_buses)
            if hourly_demand > 400:
                buses_to_add = min(3, max_buses - current_buses)
            elif hourly_demand > 250:
                buses_to_add = min(2, max_buses - current_buses)
            elif hourly_demand > 120:
                buses_to_add = min(1, max_buses - current_buses)
            else:
                buses_to_add = 0
            
            # Override if agent flagged for allocation
            if "Allocate Extra Bus" in actions:
                buses_to_add = min(max(buses_to_add, 2), max_buses - current_buses)
            
            # Apply frequency limit (base frequency is 4)
            base_freq = 4
            freq_multiplier = min(freq_solution[i], freq_limit / base_freq)
            
            route_plan = {
                "frequency_multiplier": freq_multiplier,
                "buses_to_add": buses_to_add,
                "reroute_to": None,
                "reroute_buses_count": 0,
                "reroute_reason": None
            }
            
            
            # REROUTING LOGIC: Move buses from overloaded routes to underloaded ones
            # Condition 1: Route has High Demand Risk AND load factor > 0.8
            # Condition 2: Route has low demand (< 100) - candidate to receive buses from
            if "High Demand Risk" in actions and load_factor > 0.8:
                # Find a route with low demand to take buses FROM
                # Or find a route that can handle overflow
                candidate_routes = []
                for j, candidate in enumerate(unique_routes):
                    if candidate != route:
                        candidate_demand = reduced_predictions['passenger_demand'][j]
                        candidate_load = reduced_predictions['load_factor'][j]
                        
                        # Candidate should have low demand OR low load factor
                        if candidate_demand < 100 or candidate_load < 0.4:
                            candidate_routes.append({
                                "route": candidate,
                                "demand": candidate_demand,
                                "load": candidate_load,
                                "distance": abs(route - candidate) if isinstance(route, (int, float)) else 0
                            })
                
                if candidate_routes:
                    # Sort by load factor (lowest first - best to take from)
                    candidate_routes.sort(key=lambda x: x["load"])
                    best_candidate = candidate_routes[0]
                    
                    # Decide how many buses to reroute
                    # More buses if demand is very high
                    if hourly_demand > 500:
                        buses_to_reroute = 2
                    elif hourly_demand > 300:
                        buses_to_reroute = 1
                    else:
                        buses_to_reroute = 1
                    
                    route_plan["reroute_to"] = best_candidate["route"]
                    route_plan["reroute_buses_count"] = buses_to_reroute
                    route_plan["reroute_reason"] = f"High demand ({hourly_demand:.0f}/hr) - taking {buses_to_reroute} bus(es) from Route {best_candidate['route']}"
                    
                    # Reduce buses on the source route (the one we're taking from)
                    # This will be handled in simulation
                    
            optimized_actions[route] = route_plan
            
            # Print optimization summary (first 30 routes)
            if i < 30:
                status = "🔴 HIGH" if hourly_demand > 300 else "🟡 MEDIUM" if hourly_demand > 150 else "🟢 LOW"
                reroute_info = f" → Reroute to {route_plan['reroute_to']}" if route_plan['reroute_to'] else ""
                print(f"  Route {route}: {status} demand={hourly_demand:.0f} | "
                    f"+{buses_to_add} buses | {route_plan['frequency_multiplier']:.2f}x freq{reroute_info}")
        
        total_buses_added = sum(p["buses_to_add"] for p in optimized_actions.values())
        total_routes_rerouted = sum(1 for p in optimized_actions.values() if p["reroute_to"] is not None)
        total_buses_rerouted = sum(p["reroute_buses_count"] for p in optimized_actions.values() if p["reroute_to"] is not None)
        
        print(f"\n✓ Total additional buses allocated: {total_buses_added}")
        print(f"✓ Routes with rerouting: {total_routes_rerouted}")
        print(f"✓ Buses being rerouted: {total_buses_rerouted}")
        print("="*70)
    
        return optimized_actions

    def find_alternate_route(self, route, reduced_predictions, unique_routes):
        loads = reduced_predictions['load_factor']
        best_score = float("inf")
        best_route = None

        for i, candidate in enumerate(unique_routes):
            if candidate == route:
                continue
            
            distance = abs(route - candidate) if isinstance(route, (int, float)) else 1
            load = loads[i]
            score = 0.6 * distance + 0.4 * load

            if score < best_score:
                best_score = score
                best_route = candidate

        return best_route