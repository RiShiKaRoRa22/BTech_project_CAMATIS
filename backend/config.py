import os
import sys

# Add parent directory to path to import camatis
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Paths
CAMATIS_ROOT = BASE_DIR  # This is your camatis folder
OUTPUT_FILE = os.path.join(CAMATIS_ROOT, "final_output.json")

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# Mock users for login (since no database mentioned)
USERS = {
    "admin@camatis.ai": {"password": "admin123", "role": "Admin", "name": "Admin User"},
    "operator@camatis.ai": {"password": "operator123", "role": "Operator", "name": "Operator User"}
}