#!/usr/bin/env python3
"""
Custom API Test Script
Modify this to test specific scenarios
"""

import requests
import json
import time

API_URL = "http://localhost:3004/api/generate-enhanced-3d-simple"

def test_api():
    print("🧪 Testing PetPlantr API...")
    
    # Test payload
    payload = {
        "imageUrl": "https://images.unsplash.com/photo-1587300003388-59208cc962cb/ixlib=rb-4.0.3&w=400&auto=format&fit=crop&q=60",
        "quality": "draft",  # Use draft for fastest testing
        "breed": "Golden Retriever",
        "options": {
            "fastMode": True,
            "includeReservoir": False
        }
    }
    
    try:
        print("📤 Sending request...")
        start_time = time.time()
        
        response = requests.post(API_URL, json=payload, timeout=30)
        
        duration = time.time() - start_time
        print(f"⏱️ Response time: {duration:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"   Request ID: {data.get('requestId', 'N/A')}")
            print(f"   Quality Score: {data.get('qualityAssurance', {}).get('score', 'N/A')}%")
            print(f"   From Cache: {data.get('fromCache', False)}")
            print(f"   Breed: {data.get('breedAnalysis', {}).get('breed', 'N/A')}")
            return True
            
        elif response.status_code == 429:
            error_data = response.json()
            print(f"⏰ Rate limited. Retry after: {error_data.get('retryAfter', 'N/A')} seconds")
            return False
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Request failed: {e}")
        return False

if __name__ == "__main__":
    test_api()
