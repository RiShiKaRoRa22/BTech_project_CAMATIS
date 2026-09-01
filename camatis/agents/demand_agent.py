class DemandAgent:
    def evaluate(self, demand, load, prob_high):
        """
        Evaluate demand risk based on current load and forecast probability
        
        Args:
            demand: Current demand (passengers per hour)
            load: Current load factor (0-1 range, 0.34 = 34%)
            prob_high: Probability of high demand from ML model (0-1)
        """
        # Only trigger High Demand Risk for ACTUALLY high load
        # Load > 65% is genuinely high utilization
        if load > 0.65:
            return {
                "type": "demand_risk",
                "action": "High Demand Risk",
                "priority": 3
            }
        
        # For forecast-based risk, require BOTH high demand AND high probability
        # This prevents false positives on low-load routes
        if demand > 350 and prob_high > 0.75:
            return {
                "type": "demand_risk",
                "action": "High Demand Risk",
                "priority": 3
            }
        
        return None