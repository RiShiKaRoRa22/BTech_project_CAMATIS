from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import secrets

# Use relative imports within backend
from backend.api.models import *
from backend.services.data_service import data_service
from backend.services.pipeline_service import pipeline_service
from backend.config import USERS

router = APIRouter()

# ============== Auth Routes ==============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    user = USERS.get(request.email)
    
    if not user or user["password"] != request.password:
        return LoginResponse(
            success=False,
            message="Invalid credentials",
            token=None,
            user=None
        )
    
    # Generate simple token
    token = secrets.token_urlsafe(32)
    
    return LoginResponse(
        success=True,
        token=token,
        user={
            "email": request.email,
            "name": user["name"],
            "role": user["role"]
        },
        message="Login successful"
    )

# ============== Dashboard Routes ==============

@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    """Get dashboard data"""
    return data_service.get_dashboard_data()

# ============== Routes Routes ==============

@router.get("/routes", response_model=List[RouteSummary])
async def get_routes():
    """Get all routes"""
    return data_service.get_all_routes()

@router.get("/route/{route_id}", response_model=RouteDetail)
async def get_route_detail(route_id: str):
    """Get detailed route information"""
    detail = data_service.get_route_detail(route_id)
    
    if not detail:
        # Return empty detail for unknown route
        return RouteDetail(
            demand_trend=[],
            load_trend=[],
            confidence=0,
            recommendations=Recommendation(
                frequency_multiplier="1.0x",
                buses_to_add="0 Buses",
                reroute_suggestion="No data"
            ),
            action_badges=[]
        )
    
    return detail

# ============== Optimization Routes ==============

@router.post("/optimize", response_model=OptimizeResponse)
async def run_optimization():
    """
    Run your existing CAMATIS pipeline inference
    """
    import traceback
    print("\n" + "="*70)
    print("[API] /optimize endpoint called")
    print("="*70)
    
    try:
        print("[API] Calling pipeline_service.run_inference()...")
        result = pipeline_service.run_inference()
        print(f"[API] Pipeline result: {result}")
        
        # Get summary from fresh results
        dashboard = data_service.get_dashboard_data()
        stats = dashboard.get("stats", {})
        
        return OptimizeResponse(
            success=True,
            message="Pipeline executed successfully. Results updated.",
            summary={
                "total_routes": stats.get("total_routes", 0),
                "routes_with_actions": sum(1 for r in data_service.load_results() or [] if r.get("actions") and "No action" not in r.get("actions", [])),
                "total_buses_added": sum(r.get("buses_added", 0) for r in data_service.load_results() or []),
                "anomalies_detected": stats.get("anomalies", 0),
                "high_uncertainty_routes": sum(1 for r in data_service.load_results() or [] if r.get("high_uncertainty", False))
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"[API ERROR] {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {str(e)}\n{error_details}"
        )

@router.get("/results", response_model=List[OptimizationResult])
async def get_results():
    """Get latest optimization results"""
    results = data_service.load_results()
    
    if not results:
        return []
    
    return results

# ============== Alerts Routes ==============

@router.get("/alerts", response_model=List[Alert])
async def get_alerts():
    """Get all alerts"""
    return data_service.get_alerts()

# ============== Health Check ==============

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    from backend.config import OUTPUT_FILE
    import os
    
    return {
        "status": "healthy",
        "output_file_exists": os.path.exists(OUTPUT_FILE),
        "timestamp": datetime.now().isoformat()
    }

from backend.services.config_service import config_service
from pydantic import BaseModel

class SettingsUpdate(BaseModel):
    max_buses: int = None
    frequency_limit: int = None
    optimization_preference: str = None

@router.get("/settings")
async def get_settings():
    config = config_service.get_config()
    return {
        "maxBuses": config.max_buses,
        "frequencyLimit": config.frequency_limit,
        "optimizationPreference": config.optimization_preference
    }

@router.post("/settings")
async def update_settings(settings: SettingsUpdate):
    updates = {}
    if settings.max_buses is not None:
        updates["max_buses"] = settings.max_buses
    if settings.frequency_limit is not None:
        updates["frequency_limit"] = settings.frequency_limit
    if settings.optimization_preference is not None:
        updates["optimization_preference"] = settings.optimization_preference
    
    new_config = config_service.update_config(updates)
    return {
        "success": True,
        "settings": {
            "maxBuses": new_config.max_buses,
            "frequencyLimit": new_config.frequency_limit,
            "optimizationPreference": new_config.optimization_preference
        }
    }