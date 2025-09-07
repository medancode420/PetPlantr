#!/usr/bin/env python3
import requests
import time

def test_synthetic_monitor():
    """Test the synthetic monitor endpoint"""
    try:
        print("🧪 Testing synthetic monitor endpoint...")
        response = requests.get("http://localhost:8000/api/v1/ops/synthetic/live", timeout=5)
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    # Wait for server to be ready
    time.sleep(2)
    test_synthetic_monitor()
