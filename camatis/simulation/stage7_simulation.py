"""
Stage 7: Scenario Simulation Engine - DYNAMIC VERSION with Settings
"""

import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass, field
import sys
import os

# Add parent directory to path to import backend config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.services.config_service import config_service

@dataclass
class RouteState:
    """Tracks state changes for each route"""
    route_id: int
    original_demand: float
    current_demand: float
    original_frequency: float
    current_frequency: float
    original_buses: int
    current_buses: int
    rerouted_from: List[int] = field(default_factory=list)
    rerouted_to: List[int] = field(default_factory=list)
    waiting_passengers: int = 0
    load_factor: float = 0.0
    hourly_demand: float = 0.0


class TransportSimulation:
    """Simulation that shows impact of decisions on system state"""

    def __init__(self, predictions, uncertainty_info, optimized_actions, test_df=None):
        self.predictions = predictions
        self.optimized_actions = optimized_actions
        self.test_df = test_df
        
        self.route_states: Dict[int, RouteState] = {}
        self.demand_shifts: List[Dict] = []
        self.BUS_CAPACITY = 50
        
        # Load settings from config service
        try:
            config = config_service.get_config()
            self.frequency_limit = config.frequency_limit
            self.max_buses = config.max_buses
            # Also set freq_limit for compatibility with existing code
            self.freq_limit = self.frequency_limit
            print(f"[SIMULATION] Settings loaded: freq_limit={self.frequency_limit}, max_buses={self.max_buses}")
        except Exception as e:
            self.frequency_limit = 12
            self.freq_limit = 12
            self.max_buses = 30
            print(f"[SIMULATION] Using defaults: freq_limit={self.frequency_limit}, max_buses={self.max_buses}")
        
    def setup_initial_state(self):
        """Initialize state before any decisions"""
        print("\n" + "="*70)
        print(" INITIAL SYSTEM STATE (Before Decisions)")
        print("="*70)
        
        # Check if optimized_actions is a dict or array
        if isinstance(self.optimized_actions, np.ndarray):
            # If it's a numpy array, create dummy route states
            num_routes = min(len(self.optimized_actions), 20)  # Limit to 20 routes
            route_list = list(range(num_routes))
            print(f"⚠️  Optimized actions is array with {len(self.optimized_actions)} entries. Using {num_routes} routes.")
        else:
            route_list = list(self.optimized_actions.keys())
        
        for idx, route_id in enumerate(route_list):
            if idx < len(self.predictions.get('passenger_demand', [])):
                demand = float(self.predictions['passenger_demand'][idx])
            else:
                demand = 200.0
            
            demand = max(30, min(800, demand))
            original_freq = 4.0
            original_buses = 1
            
            self.route_states[route_id] = RouteState(
                route_id=route_id,
                original_demand=demand,
                current_demand=demand,
                original_frequency=original_freq,
                current_frequency=original_freq,
                original_buses=original_buses,
                current_buses=original_buses,
                hourly_demand=demand
            )
        
        print(f"\n{'Route':<8} {'Original Demand':<15} {'Original Freq':<12} {'Original Buses':<12}")
        print("-" * 55)
        for i, (rid, state) in enumerate(list(self.route_states.items())[:20]):
            print(f"{rid:<8} {state.original_demand:<15.0f} {state.original_frequency:<12.1f} {state.original_buses:<12}")
        if len(self.route_states) > 20:
            print(f"... and {len(self.route_states) - 20} more routes")
    
    def apply_frequency_decisions(self):
        """Apply frequency multiplier decisions WITH LIMIT"""
        print("\n" + "="*70)
        print(" APPLYING FREQUENCY DECISIONS")
        print("="*70)
        
        freq_changes = []
        base_freq = 4.0
        
        # Handle both dict and array cases
        if isinstance(self.optimized_actions, np.ndarray):
            # If it's a numpy array, create dummy actions
            num_routes = len(self.route_states)
            dummy_actions = {i: {"frequency_multiplier": 1.0, "buses_to_add": 0} 
                             for i in range(num_routes)}
            # Use dummy actions
            actions_to_use = dummy_actions
        else:
            actions_to_use = self.optimized_actions
        
        for route_id, plan in actions_to_use.items():
            if route_id not in self.route_states:
                continue
            
            # Handle both dict and array cases
            if isinstance(plan, dict):
                multiplier = plan.get("frequency_multiplier", 1.0)
            else:
                multiplier = 1.0
            
            if multiplier != 1.0:
                old_freq = self.route_states[route_id].current_frequency
                new_freq = min(old_freq * multiplier, self.freq_limit)
                self.route_states[route_id].current_frequency = new_freq
                freq_changes.append({
                    "route": route_id,
                    "old_freq": old_freq,
                    "new_freq": new_freq,
                    "multiplier": multiplier,
                    "capped": new_freq < old_freq * multiplier
                })
        
        if freq_changes:
            print(f"\n{'Route':<8} {'Old Freq':<10} {'New Freq':<10} {'Multiplier':<10} {'Capped':<8}")
            print("-" * 55)
            for change in freq_changes[:15]:
                capped_flag = "✓" if change['capped'] else ""
                print(f"{change['route']:<8} {change['old_freq']:<10.1f} {change['new_freq']:<10.1f} "
                      f"{change['multiplier']:<10.2f}x {capped_flag:<8}")
            if len(freq_changes) > 15:
                print(f"... and {len(freq_changes) - 15} more routes")
            print(f"\n[LIMIT] Frequency capped at {self.frequency_limit} buses/hour")
        else:
            print("  No frequency changes applied")
    
    def apply_bus_allocation_decisions(self):
        """Apply bus allocation decisions WITH MAX BUSES LIMIT"""
        print("\n" + "="*70)
        print(" APPLYING BUS ALLOCATION DECISIONS")
        print("="*70)
        
        bus_changes = []
        capped_count = 0
        
        # Handle both dict and array cases
        if isinstance(self.optimized_actions, np.ndarray):
            num_routes = len(self.route_states)
            dummy_actions = {i: {"buses_to_add": 0} for i in range(num_routes)}
            actions_to_use = dummy_actions
        else:
            actions_to_use = self.optimized_actions
        
        for route_id, plan in actions_to_use.items():
            if route_id not in self.route_states:
                continue
            
            if isinstance(plan, dict):
                buses_to_add = plan.get("buses_to_add", 0)
            else:
                buses_to_add = 0
            
            if buses_to_add > 0:
                old_buses = self.route_states[route_id].current_buses
                new_buses = min(old_buses + buses_to_add, self.max_buses)
                actual_added = new_buses - old_buses
                
                if actual_added < buses_to_add:
                    capped_count += 1
                
                self.route_states[route_id].current_buses = new_buses
                bus_changes.append({
                    "route": route_id,
                    "old_buses": old_buses,
                    "new_buses": new_buses,
                    "requested": buses_to_add,
                    "added": actual_added
                })
        
        if bus_changes:
            print(f"\n{'Route':<8} {'Old Buses':<10} {'New Buses':<10} {'Requested':<10} {'Added':<8}")
            print("-" * 55)
            for change in bus_changes[:15]:
                print(f"{change['route']:<8} {change['old_buses']:<10} {change['new_buses']:<10} "
                      f"+{change['requested']:<9} +{change['added']:<7}")
            if len(bus_changes) > 15:
                print(f"... and {len(bus_changes) - 15} more routes")
            
            if capped_count > 0:
                print(f"\n[LIMIT] {capped_count} routes hit max_buses limit of {self.max_buses}")
        else:
            print("  No bus allocation changes")
    
    def apply_rerouting_decisions(self):
        """DYNAMIC REROUTING - Each reroute affects the system state"""
        print("\n" + "="*70)
        print(" DYNAMIC REROUTING - One at a time")
        print("="*70)
        
        # Get routes that want to reroute
        reroute_requests = []
        
        if isinstance(self.optimized_actions, np.ndarray):
            # If array, no rerouting
            print("  No rerouting requests (optimized_actions is an array)")
            return []
        
        for route_id, plan in self.optimized_actions.items():
            if route_id not in self.route_states:
                continue
            
            if isinstance(plan, dict):
                reroute_to = plan.get("reroute_to")
                if reroute_to is not None and reroute_to in self.route_states:
                    reroute_requests.append({
                        "from": route_id,
                        "to": reroute_to,
                        "priority": self.route_states[route_id].hourly_demand
                    })
        
        if not reroute_requests:
            print("  No rerouting requests")
            return []
        
        # Sort by priority (highest demand first)
        reroute_requests.sort(key=lambda x: x["priority"], reverse=True)
        
        print(f"Processing {len(reroute_requests)} reroute requests in priority order...\n")
        
        applied_reroutes = []
        target_counts = {}
        
        for request in reroute_requests:
            from_route = request["from"]
            original_target = request["to"]
            
            source_state = self.route_states[from_route]
            
            # Find best target based on current state
            best_target = self.find_best_target(from_route, target_counts, original_target)
            
            if best_target is None:
                print(f"  ⚠️ No suitable target for Route {from_route}, skipping")
                continue
            
            target_state = self.route_states[best_target]
            
            # Calculate current load
            target_capacity = target_state.current_buses * self.BUS_CAPACITY * target_state.current_frequency
            target_load = target_state.current_demand / target_capacity if target_capacity > 0 else 1
            
            if target_load > 0.75:
                print(f"  ⚠️ Target {best_target} at {target_load:.1%} load, skipping")
                continue
            
            # Check if source has enough buses
            if source_state.current_buses <= 1:
                print(f"  ⚠️ Route {from_route} only has {source_state.current_buses} bus, cannot reroute")
                continue
            
            # Move 1 bus
            from_capacity_before = source_state.current_buses * self.BUS_CAPACITY * source_state.current_frequency
            to_capacity_before = target_capacity
            
            source_state.current_buses -= 1
            target_state.current_buses += 1
            
            # Demand shift (15%)
            demand_shift = source_state.current_demand * 0.15
            source_state.current_demand -= demand_shift
            target_state.current_demand += demand_shift
            
            from_capacity_after = source_state.current_buses * self.BUS_CAPACITY * source_state.current_frequency
            to_capacity_after = target_state.current_buses * self.BUS_CAPACITY * target_state.current_frequency
            
            target_counts[best_target] = target_counts.get(best_target, 0) + 1
            
            applied_reroutes.append({
                "from": from_route,
                "to": best_target,
                "demand_shift": demand_shift,
                "from_capacity_change": from_capacity_after - from_capacity_before,
                "to_capacity_change": to_capacity_after - to_capacity_before
            })
            
            # Update the plan
            if isinstance(self.optimized_actions, dict):
                self.optimized_actions[from_route]["reroute_to"] = best_target
            
            print(f"  ✓ Route {from_route} → {best_target} | "
                  f"Target load: {target_load:.1%} → {target_state.current_demand / to_capacity_after:.1%}")
        
        if applied_reroutes:
            print(f"\n{'From':<8} {'To':<8} {'Demand Shift':<12} {'From Cap Δ':<12} {'To Cap Δ':<12}")
            print("-" * 55)
            for r in applied_reroutes:
                print(f"{r['from']:<8} {r['to']:<8} {r['demand_shift']:<12.0f} "
                      f"{r['from_capacity_change']:<+12.0f} {r['to_capacity_change']:<+12.0f}")
        
        return applied_reroutes

    def find_best_target(self, from_route, target_counts, skip_route=None):
        """Find best target based on current system state"""
        best_score = float("inf")
        best_target = None
        
        for route_id, state in self.route_states.items():
            if route_id == from_route or route_id == skip_route:
                continue
            
            capacity = state.current_buses * self.BUS_CAPACITY * state.current_frequency
            current_load = state.current_demand / capacity if capacity > 0 else 1
            
            # Penalty for routes that already received reroutes
            reroute_penalty = target_counts.get(route_id, 0) * 0.2
            
            score = current_load + reroute_penalty
            
            if score < best_score and current_load < 0.6:
                best_score = score
                best_target = route_id
        
        return best_target

    def calculate_impact(self):
        """Calculate the impact of all decisions"""
        print("\n" + "="*70)
        print(" IMPACT OF DECISIONS - BEFORE vs AFTER")
        print("="*70)
        
        impacts = []
        
        for route_id, state in self.route_states.items():
            demand_change = state.current_demand - state.original_demand
            demand_change_percent = (demand_change / state.original_demand * 100) if state.original_demand > 0 else 0
            
            freq_change = state.current_frequency - state.original_frequency
            bus_change = state.current_buses - state.original_buses
            
            new_capacity = state.current_buses * self.BUS_CAPACITY * state.current_frequency
            
            if new_capacity > 0:
                if state.current_demand > new_capacity:
                    excess_per_hour = state.current_demand - new_capacity
                    waiting = int(excess_per_hour * 0.3 * 8)
                else:
                    waiting = int(state.current_demand * 0.05)
            else:
                waiting = int(state.current_demand * 0.5)
            
            load_factor = min(100, (state.current_demand / new_capacity * 100)) if new_capacity > 0 else 100
            
            state.waiting_passengers = waiting
            state.load_factor = load_factor
            
            if abs(demand_change) > 5 or abs(freq_change) > 0.1 or bus_change != 0:
                impacts.append({
                    "route": route_id,
                    "demand_change": demand_change,
                    "demand_change_percent": demand_change_percent,
                    "freq_change": freq_change,
                    "bus_change": bus_change,
                    "waiting": waiting,
                    "load_factor": load_factor,
                    "new_capacity": new_capacity
                })
        
        print(f"\n{'Route':<8} {'Demand Δ':<12} {'Demand %':<10} {'Freq Δ':<10} {'Buses Δ':<10} {'Waiting':<10} {'Load %':<8}")
        print("-" * 85)
        
        impacts.sort(key=lambda x: abs(x["demand_change"]), reverse=True)
        
        for impact in impacts[:25]:
            demand_symbol = "↑" if impact["demand_change"] > 0 else "↓"
            freq_symbol = "↑" if impact["freq_change"] > 0 else "↓"
            bus_symbol = "+" if impact["bus_change"] > 0 else "-"
            
            print(f"{impact['route']:<8} "
                  f"{demand_symbol}{abs(impact['demand_change']):<11.0f} "
                  f"{impact['demand_change_percent']:<+10.1f}% "
                  f"{freq_symbol}{abs(impact['freq_change']):<9.1f} "
                  f"{bus_symbol}{abs(impact['bus_change']):<9} "
                  f"{impact['waiting']:<10} "
                  f"{impact['load_factor']:<8.0f}%")
        
        return impacts
    
    def update_optimized_actions(self):
        """Update the optimized_actions with simulation results"""
        for route_id, state in self.route_states.items():
            if isinstance(self.optimized_actions, dict) and route_id in self.optimized_actions:
                self.optimized_actions[route_id]["demand_after"] = state.current_demand
                self.optimized_actions[route_id]["waiting_passengers"] = state.waiting_passengers
                self.optimized_actions[route_id]["load_factor"] = state.load_factor
        
        self.dynamic_demand = {rid: s.current_demand for rid, s in self.route_states.items()}
        self.route_queues = {rid: s.waiting_passengers for rid, s in self.route_states.items()}
    
    def run_simulation(self, duration=480):
        """Run dynamic simulation"""
        print("\n" + "🚀"*35)
        print(" DYNAMIC DECISION SIMULATION")
        print("🚀"*35)
        
        self.setup_initial_state()
        self.apply_frequency_decisions()
        self.apply_bus_allocation_decisions()
        
        print("\n" + "="*70)
        print(" DYNAMIC REROUTING")
        print("="*70)
        reroutes = self.apply_rerouting_decisions()
        
        impacts = self.calculate_impact()
        self.update_optimized_actions()
        
        return impacts

    def get_results(self):
        return {"routes_served": len(self.route_states)}


class ScenarioSimulator:
    def run(self, predictions, uncertainty_info, optimized_actions, test_df=None, duration=480):
        print("\n" + "="*70)
        print(" RUNNING DECISION IMPACT SIMULATION")
        print("="*70)
        
        sim = TransportSimulation(predictions, uncertainty_info, optimized_actions, test_df)
        sim.run_simulation(duration=duration)
        results = sim.get_results()
        
        return sim, results

    def run_all_scenarios(self, optimized_solutions, scenarios=None):
        """
        Run all scenarios for simulation - Called by main_pipeline.py
        
        Args:
            optimized_solutions: Solutions from NSGA-III optimization
            scenarios: List of scenarios to simulate (optional)
        """
        print("\n" + "="*70)
        print(" STAGE 7: SCENARIO SIMULATION ENGINE")
        print("="*70)
        
        if scenarios is None:
            scenarios = ['normal', 'congestion_spike', 'festival_surge']
        
        results = {}
        
        for scenario in scenarios:
            print(f"\n📊 Simulating scenario: {scenario.upper()}")
            print("-" * 50)
            
            # Create simulation instance with the optimized solutions
            sim = TransportSimulation(
                predictions={},  # Empty predictions as we're using optimized solutions
                uncertainty_info={},
                optimized_actions=optimized_solutions,
                test_df=None
            )
            
            # Adjust simulation parameters based on scenario
            if scenario == 'congestion_spike':
                sim.freq_limit = 8
                sim.max_buses = 25
                print("   🚗 Congestion mode: Reduced frequency to 8 buses/hour")
            elif scenario == 'festival_surge':
                sim.freq_limit = 15
                sim.max_buses = 35
                print("   🎉 Festival mode: Increased frequency to 15 buses/hour")
            elif scenario == 'fleet_breakdown':
                sim.freq_limit = 10
                sim.max_buses = 20
                print("   🔧 Breakdown mode: Limited to 20 buses")
            else:
                sim.freq_limit = 12
                sim.max_buses = 30
                print("   📊 Normal mode: Standard operations")
            
            # Run the simulation
            sim.run_simulation(duration=480)
            impacts = sim.calculate_impact()
            
            # Calculate summary statistics
            total_waiting = sum(s.waiting_passengers for s in sim.route_states.values())
            avg_load_factor = sum(s.load_factor for s in sim.route_states.values()) / len(sim.route_states) if sim.route_states else 0
            total_demand_change = sum(abs(s.current_demand - s.original_demand) for s in sim.route_states.values())
            
            results[scenario] = {
                'status': 'completed',
                'num_solutions': len(optimized_solutions) if hasattr(optimized_solutions, '__len__') else 0,
                'routes_served': len(sim.route_states),
                'total_waiting': total_waiting,
                'avg_load_factor': avg_load_factor,
                'total_demand_change': total_demand_change,
                'scenario': scenario,
                'top_impacts': impacts[:10]
            }
            
            print(f"\n   ✅ {scenario} scenario completed")
            print(f"      Routes simulated: {len(sim.route_states)}")
            print(f"      Total waiting passengers: {total_waiting}")
            print(f"      Average load factor: {avg_load_factor:.1f}%")
        
        print("\n" + "="*70)
        print(" SCENARIO SIMULATION COMPLETE")
        print("="*70)
        
        return results