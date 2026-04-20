import os
import requests
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("OPENALGO_HOST", "http://127.0.0.1:5001")
api_key = os.getenv("OPENALGO_API_KEY", "")

print(f"Testing connection to: {host}")
print(f"Using API Key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")

try:
    # Test 1: Health Check
    resp = requests.post(f"{host}/api/v1/funds", json={"apikey": api_key}, timeout=10)
    print(f"Health Check Response: {resp.status_code}")
    print(f"Health Check Data: {resp.json()}")

    # Test 2: List available data for DIXON (5 minute)
    payload = {
        "symbol": "DIXON",
        "exchange": "NSE",
        "interval": "5m",
        "start_date": "2024-01-01",
        "end_date": "2026-12-31",
        "apikey": api_key
    }
    resp = requests.post(f"{host}/api/v1/history", json=payload, timeout=10)
    print(f"\nDIXON Data Request Response: {resp.status_code}")
    print(f"DIXON Data Status: {resp.json().get('status')}")
    print(f"DIXON Data Message: {resp.json().get('message')}")
    
    data_count = len(resp.json().get('data', []))
    print(f"DIXON Data Rows Returned: {data_count}")

except Exception as e:
    print(f"Error during test: {e}")
