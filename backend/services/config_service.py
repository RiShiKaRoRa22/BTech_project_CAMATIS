"""
Dynamic configuration service for CAMATIS
"""

import threading
import json
import os
from typing import Dict, Any
from dataclasses import dataclass, asdict

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "system_config.json")

@dataclass
class SystemConfig:
    """System configuration based on actual data"""
    max_buses: int = 30           # Max buses per route (Route 91 had 17, so 30 is safe)
    frequency_limit: int = 12     # Max buses per hour (base is 4, so 12 = 3x multiplier)
    optimization_preference: str = "balanced"

class ConfigService:
    def __init__(self):
        self._config = SystemConfig()
        self._lock = threading.Lock()
        self._load_from_file()
    
    def _load_from_file(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self._config = SystemConfig(**data)
                print(f"[CONFIG] Loaded: max_buses={self._config.max_buses}, "
                      f"freq_limit={self._config.frequency_limit}, "
                      f"pref={self._config.optimization_preference}")
            except Exception as e:
                print(f"[CONFIG] Load failed: {e}")
    
    def _save_to_file(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(asdict(self._config), f, indent=2)
        except Exception as e:
            print(f"[CONFIG] Save failed: {e}")
    
    def get_config(self) -> SystemConfig:
        with self._lock:
            return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> SystemConfig:
        with self._lock:
            for key, value in updates.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
            self._save_to_file()
            print(f"[CONFIG] Updated: {updates}")
            return self._config

config_service = ConfigService()