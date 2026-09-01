class SchedulingAgent:
    def adjust(self, demand, uncertainty, util_class):
        # util_class mapping:
        # 0 = Underutilized (load < 0.33)
        # 1 = Normal (load 0.33-0.66)
        # 2 = Overutilized (load > 0.66)
        
        # Only increase frequency for overutilized routes OR high demand
        if util_class == 2 and uncertainty > 0.1:
            return {
                "type": "schedule_action",
                "action": "Increase Frequency",
                "priority": 2
            }
        
        # Also increase frequency if demand is very high (>350) even if not overutilized
        if demand > 350 and uncertainty > 0.1:
            return {
                "type": "schedule_action",
                "action": "Increase Frequency",
                "priority": 2
            }
        
        return None