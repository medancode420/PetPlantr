#!/usr/bin/env python3
"""
Simple test script to check PetPlantr endpoints
"""
import requests
import json

def test_endpoint(url, description):
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ {description}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ {description}")
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing PetPlantr endpoints...\n")

    # Test synthetic monitor
    test_endpoint("http://localhost:8000/synthetic-monitor", "Synthetic Monitor")

    # Test health endpoint
    test_endpoint("http://localhost:8000/health", "Health Check")

    print("\n✨ Testing complete!")
