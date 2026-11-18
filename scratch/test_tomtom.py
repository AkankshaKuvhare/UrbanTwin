import sys, os
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import requests
from config.settings import settings

api_key = settings.TOMTOM_API_KEY
print(f"Testing TomTom API with key: {api_key[:6] if api_key else 'None'}... (length: {len(api_key) if api_key else 0})")

url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
params = {
    "key": api_key,
    "point": "18.5204,73.8567",
    "unit": "kmph"
}

try:
    print("Sending request to TomTom...")
    res = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
