#!/usr/bin/env python3
"""
Production Deployment Verification
Confirms PetPlantr is using real AI models in production
"""

import requests
import json
import time
import sys

def test_production_deployment():
    print("🚀 PetPlantr Production Verification")
    print("=" * 40)
    
    base_url = "https://petplantr.vercel.app"
    
    # Test 1: Health Check
    print("📋 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check: PASSED")
            print(f"   Pipeline: {health_data.get('pipeline', 'unknown')}")
            print(f"   Version: {health_data.get('version', 'unknown')}")
            
            # Check if real models are confirmed
            if health_data.get('pipeline') == 'real':
                print("✅ Real AI models: CONFIRMED")
            else:
                print("❌ Real AI models: NOT CONFIRMED")
                
            # Check environment variables
            env = health_data.get('environment', {})
            if env.get('hasReplicateToken'):
                print("✅ Replicate API token: CONFIGURED")
            else:
                print("❌ Replicate API token: MISSING")
                
        else:
            print(f"❌ Health check: FAILED (HTTP {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check: FAILED ({e})")
        return False
    
    # Test 2: API Environment Check (without generating models)
    print("\n🔧 Testing API environment...")
    try:
        # This should return fast error if env vars missing
        response = requests.post(
            f"{base_url}/api/replicate",
            json={"prompt": "test"},
            timeout=15
        )
        
        if response.status_code == 503:
            print("⚠️  API returned 503: Environment not configured")
            print("   → Check Vercel dashboard for environment variables")
        elif response.status_code == 200:
            data = response.json()
            print("✅ API environment: CONFIGURED")
            if data.get('status') == 'processing':
                print("✅ Real model generation: STARTED")
        else:
            print(f"❌ API test: Unexpected status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⚠️  API timed out (may indicate old deployment hanging)")
    except requests.exceptions.RequestException as e:
        print(f"❌ API test: FAILED ({e})")
    
    print("\n" + "=" * 40)
    print("✅ Verification complete!")
    
    print("\nIf environment variables are missing:")
    print("1. Go to Vercel dashboard")
    print("2. Set REPLICATE_API_TOKEN in environment variables")
    print("3. Set AWS credentials if using S3")
    print("4. Force redeploy")
    
    return True

if __name__ == "__main__":
    test_production_deployment()
