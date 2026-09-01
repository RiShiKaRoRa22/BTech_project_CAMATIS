import math

class TransportState:
    def __init__(self):
        self.route_buses = {}
        self.headway = {}
        self.capacity_per_bus = 50


class ExecutionEngine:

    def __init__(self, state):
        self.state = state

    def execute(self, route_id, actions, demand):

        for action in actions:

            # 🚍 Fleet
            if action == "Allocate Extra Bus":

                current = self.state.route_buses.get(route_id, 1)
                required = math.ceil(demand / self.state.capacity_per_bus)

                to_add = max(0, required - current)

                self.state.route_buses[route_id] = current + max(1, to_add)

                print(f"Route {route_id} → +{max(1,to_add)} bus")

            # 🔁 Scheduling
            elif action == "Increase Frequency":

                self.state.headway[route_id] = 10
                print(f"Route {route_id} → Increased frequency")

            # ⚠️ Anomaly
            elif action == "Investigate Anomaly":

                print(f"Route {route_id} → INVESTIGATE")

            # ⚠️ Demand Risk
            elif action == "High Demand Risk":

                print(f"Route {route_id} → Demand Risk Warning")
                
    def execute_optimized(self, route_id, plan):

        freq = plan["frequency_multiplier"]
        buses = plan["buses_to_add"]

        if buses > 0:
            self.state.route_buses[route_id] = \
                self.state.route_buses.get(route_id, 1) + buses

            print(f"Route {route_id} → 🚍 +{buses} buses")

        if freq > 1.0:
            self.state.headway[route_id] = int(15 / freq)
            print(f"Route {route_id} → 🔁 Frequency updated")

        if plan["reroute_to"] is not None:
            print(f"Route {route_id} → 🔀 Rerouted to {plan['reroute_to']}")