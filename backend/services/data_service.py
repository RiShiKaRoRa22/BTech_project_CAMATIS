import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from backend.config import OUTPUT_FILE

class DataService:
    """Service to read data from your existing CAMATIS outputs"""
    
    def __init__(self):
        self._cached_results = None
        self._cached_timestamp = None
    
    def load_results(self) -> Optional[List[Dict[str, Any]]]:
        """Load results from final_output.json"""
        if os.path.exists(OUTPUT_FILE):
            # Check if file was modified since last read
            file_mtime = os.path.getmtime(OUTPUT_FILE)
            if self._cached_timestamp != file_mtime:
                with open(OUTPUT_FILE, 'r') as f:
                    self._cached_results = json.load(f)
                    self._cached_timestamp = file_mtime
            return self._cached_results
        return None
    
    def get_all_routes(self) -> List[Dict[str, Any]]:
        """Get all routes from results"""
        results = self.load_results()
        if not results:
            return []
        
        routes = []
        for r in results[:100]:  # Limit to 100 routes
            load = r.get("waiting_passengers", 50)
            
            # Determine status based on your data
            if r.get("anomaly", False):
                status = "Anomaly"
            elif load > 85:
                status = "Risk"
            elif r.get("high_uncertainty", False):
                status = "Risk"
            else:
                status = "Normal"
            
            routes.append({
                "id": f"R-{r.get('route_id')}",
                "demand": round(r.get("demand_after", 0), 0),
                "load_factor": round(load, 1),
                "status": status
            })
        
        return routes
    
    def get_route_detail(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed data for a specific route"""
        route_num = route_id.replace("R-", "")
        results = self.load_results()
        
        if not results:
            return None
        
        # Find the route
        route_data = None
        for r in results:
            if str(r.get("route_id", "")) == route_num:
                route_data = r
                break
        
        if not route_data:
            return None
        
        # Generate hourly trends based on actual data
        hours = ["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
        demand_patterns = [0.5, 1.5, 1.2, 1.3, 1.1, 1.4, 1.6, 1.0, 0.6]
        load_patterns = [0.4, 0.9, 0.8, 0.85, 0.75, 0.9, 1.0, 0.7, 0.5]
        
        demand_base = route_data.get("demand_after", 500)
        load_base = route_data.get("waiting_passengers", 65)
        
        demand_trend = [
            {"time": hour, "demand": round(demand_base * pattern, 0)}
            for hour, pattern in zip(hours, demand_patterns)
        ]
        
        load_trend = [
            {"time": hour, "load": round(load_base * pattern, 1)}
            for hour, pattern in zip(hours, load_patterns)
        ]
        
        # Confidence based on uncertainty
        confidence = 95 if not route_data.get("high_uncertainty", False) else 70
        
        # Build recommendations from actual actions
        actions = route_data.get("actions", [])
        
        recommendations = {
            "frequency_multiplier": f"{route_data.get('frequency_multiplier', 1.0)}x",
            "buses_to_add": f"+{route_data.get('buses_added', 0)} Buses" if route_data.get('buses_added', 0) > 0 else "0 Buses",
            "reroute_suggestion": f"Route {route_data.get('rerouted_to')}" if route_data.get('rerouted_to') else "No change needed"
        }
        
        # Map actions to badges
        action_badges = []
        for action in actions:
            if action == "Increase Frequency":
                action_badges.append({"label": action, "color": "blue"})
            elif action == "Allocate Extra Bus":
                action_badges.append({"label": action, "color": "green"})
            elif action == "High Demand Risk":
                action_badges.append({"label": action, "color": "orange"})
            elif action == "Investigate Anomaly":
                action_badges.append({"label": action, "color": "red"})
            else:
                action_badges.append({"label": action, "color": "yellow"})
        
        if not action_badges:
            action_badges.append({"label": "Monitor Load", "color": "yellow"})
        
        return {
            "demand_trend": demand_trend,
            "load_trend": load_trend,
            "confidence": confidence,
            "recommendations": recommendations,
            "action_badges": action_badges
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard overview data with anomaly detection"""
        results = self.load_results()
        
        if not results:
            return {
                "stats": {
                    "total_routes": 0,
                    "active_buses": 0,
                    "high_demand_routes": 0,
                    "anomalies": 0,
                    "avg_load_factor": 0,
                    "avg_demand": 0
                },
                "demand": [],
                "load": [],
                "alerts": []
            }
        
        # Calculate stats
        total_routes = len(results)
        
        # Calculate high demand routes (demand > 300)
        high_demand_routes = sum(1 for r in results if r.get("demand_after", 0) > 300)
        
        # CALCULATE ANOMALIES BASED ON MULTIPLE FACTORS
        anomalies = 0
        anomaly_routes = []
        
        for r in results:
            is_anomaly = False
            reason = []
            
            demand = r.get("demand_after", 0)
            waiting = r.get("waiting_passengers", 0)
            actions = r.get("actions", [])
            
            # 1. Check if already flagged by ML model
            if r.get("anomaly", False):
                is_anomaly = True
                reason.append("ML anomaly flag")
            
            # 2. Check for unusually high waiting passengers (>100)
            if waiting > 100:
                is_anomaly = True
                reason.append(f"High waiting ({waiting:.0f})")
            
            # 3. Check for demand spike (>500)
            if demand > 500:
                is_anomaly = True
                reason.append(f"Demand spike ({demand:.0f})")
            
            # 4. Check for Investigate Anomaly action from agents
            if "Investigate Anomaly" in actions:
                is_anomaly = True
                reason.append("Agent flagged for investigation")
            
            # 5. Check for High Demand Risk with relatively low demand (potential false positive)
            if "High Demand Risk" in actions and demand < 200:
                is_anomaly = True
                reason.append("False positive risk flag")
            
            # 6. Check for extreme load factor (>80%)
            load_factor = r.get("load_factor", 0)
            if load_factor > 80:
                is_anomaly = True
                reason.append(f"Overload ({load_factor:.0f}%)")
            
            if is_anomaly:
                anomalies += 1
                anomaly_routes.append({
                    "route": r.get("route_id"),
                    "demand": demand,
                    "waiting": waiting,
                    "reason": ", ".join(reason)
                })
        
        # Print debug info
        print(f"[DEBUG] Anomalies detected: {anomalies}")
        for a in anomaly_routes[:5]:
            print(f"  Route {a['route']}: {a['reason']}")
        
        # Calculate active buses
        total_buses = sum(r.get("buses_added", 0) for r in results) + total_routes
        
        # Calculate averages
        avg_demand = sum(r.get("demand_after", 0) for r in results) / total_routes if total_routes > 0 else 0
        avg_waiting = sum(r.get("waiting_passengers", 0) for r in results) / total_routes if total_routes > 0 else 0
        avg_load_factor = min(100, (avg_waiting / max(avg_demand, 1)) * 10) if avg_demand > 0 else 0
        
        # Generate hourly demand pattern
        hours = ["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
        patterns = [0.3, 1.4, 1.3, 1.2, 1.0, 1.3, 1.5, 0.9, 0.5]
        
        demand_data = [
            {"time": hour, "demand": round(avg_demand * pattern, 0)}
            for hour, pattern in zip(hours, patterns)
        ]
        
        # Get top routes for load chart
        load_data = [
            {"route": f"R-{r.get('route_id')}", "load": round(r.get("waiting_passengers", 50), 1)}
            for r in results[:6]
        ]
        
        # Generate alerts (prioritize anomalies)
        alerts = []
        alert_id = 1
        
        # First add anomaly alerts
        for r in anomaly_routes[:10]:
            severity = "High" if "spike" in r["reason"] or "Overload" in r["reason"] else "Medium"
            alerts.append({
                "id": alert_id,
                "route": f"R-{r['route']}",
                "message": f"Anomaly: {r['reason']}",
                "severity": severity,
                "time": datetime.now().strftime("%I:%M %p")
            })
            alert_id += 1
        
        # Then add high waiting alerts if not already covered
        for r in results[:15]:
            waiting = r.get("waiting_passengers", 0)
            route_id = r.get("route_id")
            
            # Skip if already in anomalies
            if any(a["route"] == route_id for a in anomaly_routes):
                continue
            
            if waiting > 50:
                severity = "High" if waiting > 100 else "Medium"
                alerts.append({
                    "id": alert_id,
                    "route": f"R-{route_id}",
                    "message": f"High waiting: {waiting:.0f} passengers",
                    "severity": severity,
                    "time": datetime.now().strftime("%I:%M %p")
                })
                alert_id += 1
        
        return {
            "stats": {
                "total_routes": total_routes,
                "active_buses": total_buses,
                "high_demand_routes": high_demand_routes,
                "anomalies": anomalies,
                "avg_load_factor": round(avg_load_factor, 1),
                "avg_demand": round(avg_demand, 0)
            },
            "demand": demand_data,
            "load": load_data,
            "alerts": alerts[:10]  # Limit to 10 alerts
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get alerts from anomalies and high uncertainty"""
        results = self.load_results()
        
        if not results:
            return []
        
        alerts = []
        for i, r in enumerate(results):
            should_alert = False
            message = ""
            
            # 1. Check for Investigate Anomaly action
            actions = r.get("actions", [])
            if "Investigate Anomaly" in actions:
                should_alert = True
                message = "System flagged for investigation"
            
            # 2. Check for high uncertainty (model confidence)
            # high_uncertainty is already set by MC Dropout
            elif r.get("high_uncertainty", False):
                should_alert = True
                # Uncertainty message about model confidence, NOT about demand
                message = "High prediction uncertainty – model confidence is low, manual review advised"
            
            if should_alert:
                alerts.append({
                    "id": i + 1,
                    "route": f"R-{r.get('route_id')}",
                    "message": message,
                    "severity": "Medium",  # Both are medium severity
                    "time": datetime.now().strftime("%I:%M %p")
                })
        
        return alerts[:20]
# Singleton instance
data_service = DataService()