"""
CAMATIS Backend API
Thin wrapper that reads your existing final_output.json
"""

import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from backend
from backend.api.routes import router
from backend.config import API_HOST, API_PORT

# Create FastAPI app
app = FastAPI(
    title="CAMATIS API",
    description="Causal-Adaptive Multi-Agent Transport Intelligence System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router, prefix="/api", tags=["CAMATIS"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CAMATIS API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "routes": "/api/routes",
            "results": "/api/results",
            "alerts": "/api/alerts",
            "optimize": "/api/optimize (POST)",
            "login": "/api/login (POST)"
        }
    }

# Run with: uvicorn backend.main:app --reload --port 8000