import numpy as np
from camatis.agents.demand_agent import DemandAgent
from camatis.agents.fleet_agent import FleetAgent
from camatis.agents.scheduling_agent import SchedulingAgent
from camatis.agents.supervisor_agent import SupervisorAgent


class AgentManager:

    def __init__(self, available_buses=5):
        self.demand_agent = DemandAgent()
        self.fleet_agent = FleetAgent(available_buses)
        self.schedule_agent = SchedulingAgent()
        self.supervisor = SupervisorAgent()

    def process(self,
                route_ids,
                demand_mean,
                load_mean,
                utilization,
                demand_std,
                load_std,
                cls_probs,
                high_uncertainty_mask,
                anomaly_mask):

        decisions = []
        
        for i in range(len(route_ids)):

            demand = float(demand_mean[i])
            load = float(load_mean[i])
           
            util_class = int(utilization[i])
            demand_unc = float(demand_std[i])
            load_unc = float(load_std[i])
            prob_high = float(cls_probs[i][2])
            if i < 50:  # Check first 50 routes
                print(f"[DEBUG] Route {route_ids[i]}: demand={demand:.1f}, load={load:.3f}, prob_high={prob_high:.3f}, util={util_class}")

            is_anomaly = anomaly_mask[i]

            actions = []

            if is_anomaly:
                decisions.append({
                    "route_id": route_ids[i],
                    "actions": ["Investigate Anomaly"],  # 🔥 FIX
                    "demand": demand,
                    "load": load
                })
                continue
                

            actions.append(self.demand_agent.evaluate(demand, load, prob_high))
            actions.append(self.fleet_agent.allocate(load, load_unc))
            actions.append(self.schedule_agent.adjust(demand, demand_unc, util_class))

            final_action = self.supervisor.resolve(actions)

            if final_action and len(final_action) > 0:
                decisions.append({
                    "route_id": route_ids[i],
                    "actions": [a["action"] for a in final_action],  # 🔥 FIX
                    "demand": demand,
                    "load": load,
                    "demand_uncertainty": demand_unc,
                    "load_uncertainty": load_unc
                })
            else:
                decisions.append({
                    "route_id": route_ids[i],
                    "actions": ["No action"],
                    "demand": demand,
                    "load": load
                })

        return decisions