# CAMATIS Backend API

FastAPI backend service for the CAMATIS (Causal-Adaptive Multi-Agent Transport Intelligence System) that serves real-time transit optimization data to the frontend dashboard.

## 📋 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Backend](#running-the-backend)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This backend service provides a REST API that:
- Serves data from your existing CAMATIS pipeline (`final_output.json`)
- Triggers the ML inference pipeline on demand
- Handles authentication for the frontend
- Provides real-time transit optimization results

## 📦 Prerequisites

Before running the backend, ensure you have:

- **Python 3.10+** installed
- **Git** (optional, for version control)
- **CAMATIS pipeline** already set up and working
- `final_output.json` generated from your pipeline

## 🚀 Installation

### 1. Clone/Navigate to Project Root

cd C:\Users\rishi\OneDrive\Desktop\PROJECTS\PBL2
### 2. Create Virtual Environment
bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate


### 3. Install Backend Dependencies
bash
# Install FastAPI and server
pip install fastapi uvicorn

# Install data processing libraries
pip install numpy pandas

# Install CAMATIS dependencies (if not already installed)
pip install torch lightgbm catboost xgboost scikit-learn simpy
### 4. Verify CAMATIS Installation
bash
# Test that CAMATIS imports work
python -c "from camatis.run_agents_pipeline import CAMATISDecisionPipeline; print('✅ CAMATIS imported successfully')"

## 📁 Project Structure
Ensure your project structure looks like this:

text
C:\Users\rishi\OneDrive\Desktop\PROJECTS\PBL2\
├── venv/                      # Virtual environment
├── camatis/                   # Your existing ML pipeline
│   ├── agents/
│   ├── optimization/
│   ├── simulation/
│   ├── execution/
│   ├── run_agents_pipeline.py
│   └── ... (all your existing files)
├── backend/                   # Backend API (NEW)
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Configuration settings
│   ├── models.py             # Pydantic data models
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py         # API endpoints
│   └── services/
│       ├── __init__.py
│       ├── data_service.py   # Data reading service
│       └── pipeline_service.py # Pipeline execution service
└── final_output.json          # Your pipeline output
⚙️ Configuration
Backend Configuration (backend/config.py)
python
# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Mock users for login (can be replaced with database)
USERS = {
    "admin@camatis.ai": {"password": "admin123", "role": "Admin", "name": "Admin User"},
    "operator@camatis.ai": {"password": "operator123", "role": "Operator", "name": "Operator User"}
}
## 🏃 Running the Backend
Method 1: Direct Run (Development)
bash
# Make sure you're in the project root
cd C:\Users\rishi\OneDrive\Desktop\PROJECTS\PBL2

# Activate virtual environment
venv\Scripts\activate

# Run the server with auto-reload
uvicorn backend.main:app --reload --port 8001

Method 2: Run with Python
bash
# Navigate to project root
cd C:\Users\rishi\OneDrive\Desktop\PROJECTS\PBL2

# Activate venv
venv\Scripts\activate

# Run directly
python -m uvicorn backend.main:app --reload --port 8000
Method 3: Production Run
bash
# Without auto-reload
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
🔧 API Endpoints
Base URL
text
http://localhost:8000
Authentication
Endpoint	Method	Description
/api/login	POST	User login
Login Request Body:

json
{
  "email": "admin@camatis.ai",
  "password": "admin123",
  "role": "Admin"
}
Dashboard & Data
Endpoint	Method	Description
- /api/dashboard	GET	Get dashboard overview stats and charts
- /api/routes	GET	Get all routes with current status
- /api/route/{id}	GET	Get detailed analysis for specific route
- /api/alerts	GET	Get all anomaly alerts
- /api/results	GET	Get latest optimization results
Optimization
Endpoint	Method	Description
- /api/optimize	POST	Trigger CAMATIS pipeline inference
Health Check
Endpoint	Method	Description
- /	GET	Root endpoint with API info
- /api/health	GET	Health check status

## 🧪 Testing the API
Using Browser
Start the backend server

Open http://localhost:8000/docs - Swagger UI with interactive documentation

Open http://localhost:8000/redoc - ReDoc documentation

Using curl
bash
# Health check
curl http://localhost:8000/api/health

# Get dashboard data
curl http://localhost:8000/api/dashboard

# Get all routes
curl http://localhost:8000/api/routes

# Get specific route
curl http://localhost:8000/api/route/R-101

# Get alerts
curl http://localhost:8000/api/alerts

# Get results
curl http://localhost:8000/api/results

# Trigger optimization
curl -X POST http://localhost:8000/api/optimize

# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@camatis.ai","password":"admin123","role":"Admin"}'
Using Python
python
import requests

BASE_URL = "http://localhost:8000"

# Get dashboard data
response = requests.get(f"{BASE_URL}/api/dashboard")
print(response.json())

# Trigger optimization
response = requests.post(f"{BASE_URL}/api/optimize")
print(response.json())
🔄 Running Complete System
Terminal 1 - Backend
bash
cd C:\Users\rishi\OneDrive\Desktop\PROJECTS\PBL2
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
Terminal 2 - Frontend
bash
cd C:\Users\rishi\OneDrive\Desktop\PROJECTS\PBL2\camatis-frontend
npm run dev
Then access:

Frontend: http://localhost:3000

Backend API: http://localhost:8000

API Docs: http://localhost:8000/docs

## 📝 Development Notes
Auto-reload
The --reload flag automatically restarts the server when code changes. Remove for production.

Adding New Endpoints
Add new route in backend/api/routes.py

Add model in backend/models.py

Add service method in appropriate service file


## 📄 License
CAMATIS - Causal-Adaptive Multi-Agent Transport Intelligence System