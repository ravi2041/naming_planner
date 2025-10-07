# app/utils/config_loader.py
import json
from pathlib import Path

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "poiuPOIU@098",
    "database": "naming_planner"
}


def load_rules(file_name: str):
    """Load JSON rule configuration from app/config folder."""
    config_path = Path(__file__).resolve().parents[1] / "config" / file_name
    with open(config_path, "r") as f:
        return json.load(f)

