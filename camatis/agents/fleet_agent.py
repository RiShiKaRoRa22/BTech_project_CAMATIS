class FleetAgent:
    def __init__(self, available_buses):
        self.available_buses = available_buses

    def allocate(self, load, load_uncertainty):
        """
        Decide whether to allocate extra buses
        
        Args:
            load: Current load factor (0-1 range)
            load_uncertainty: Uncertainty in load prediction
        """
        # Only allocate when load > 55% (actual need)
        if load > 0.55:
            return {
                "type": "fleet_action",
                "action": "Allocate Extra Bus",
                "priority": 1
            }
        
        # Allocate if load is moderate but uncertainty is high (might increase)
        if load > 0.45 and load_uncertainty > 0.15:
            return {
                "type": "fleet_action",
                "action": "Allocate Extra Bus",
                "priority": 1
            }
        
        return None