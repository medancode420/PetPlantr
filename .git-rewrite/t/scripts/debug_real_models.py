#!/usr/bin/env python3

"""
Test script to verify real 3D model generation (no demo fallback)
This will test the actual Replicate API calls to ensure we get real 3D models
"""

import os
import time
import requests
import json

def load_env_vars():
    """Load environment variables from .env.local file"""
    env_file = '/Users/medan/Downloads/PetPlantr/frontend/.env.local'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')

# Load environment variables
load_env_vars()

def test_real_3d_generation():
    """Test the actual 3D model generation pipeline"""
    
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN not found")
        return False
    
    print("🧪 Testing Real 3D Model Generation Pipeline")
    print("=" * 50)
    
    # Test the verified models directly
    models_to_test = [
        {
            "name": "cjwbw/shap-e",
            "version": "5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c",
            "input": {
                "prompt": "A cute dog-shaped planter for succulents, terracotta style, modern design"
            }
        },
        {
            "name": "cjwbw/point-e", 
            "version": "1a4da7adf0bc84cd786c1df41c02db3097d899f5c159f5fd5814a11117bdf02b",
            "input": {
                "prompt": "A dog-shaped planter, 3D printable design",
                "output_format": "animation"
            }
        }
    ]
    
    headers = {
        "Authorization": f"Token {replicate_token}",
        "Content-Type": "application/json"
    }
    
    for model in models_to_test:
        print(f"\n🔬 Testing {model['name']}...")
        
        # Create prediction
        prediction_data = {
            "version": model["version"],
            "input": model["input"]
        }
        
        try:
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json=prediction_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                prediction_id = result.get('id')
                print(f"✅ {model['name']} prediction created: {prediction_id}")
                print(f"   Status: {result.get('status')}")
                
                # Check status a few times
                for i in range(3):
                    time.sleep(5)
                    status_response = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        status = status_result.get('status')
                        print(f"   Status check {i+1}: {status}")
                        
                        if status == 'succeeded':
                            output = status_result.get('output')
                            print(f"✅ {model['name']} SUCCESS! Output: {output}")
                            return True
                        elif status == 'failed':
                            error = status_result.get('error')
                            print(f"❌ {model['name']} FAILED: {error}")
                            break
                    else:
                        print(f"⚠️ Status check failed: {status_response.status_code}")
                        
            else:
                print(f"❌ {model['name']} creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"💥 {model['name']} error: {str(e)}")
    
    return False

def test_production_api():
    """Test our production API to ensure it uses real models"""
    
    print("\n🌐 Testing Production API Integration")
    print("=" * 40)
    
    # Test concept generation (should work)
    try:
        response = requests.post(
            "https://petplantr.vercel.app/api/replicate",
            json={"prompt": "A cute dog planter design"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            prediction_id = result.get('predictionId')
            pipeline = result.get('pipeline')
            
            print(f"✅ Production API Response:")
            print(f"   Prediction ID: {prediction_id}")
            print(f"   Pipeline: {pipeline}")
            print(f"   Note: {result.get('note')}")
            
            if pipeline == "real":
                print("🎉 SUCCESS: Using real AI pipeline!")
                return True
            else:
                print("⚠️ WARNING: Still using demo/fallback mode")
                
        else:
            print(f"❌ Production API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Production API error: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("🔍 DEBUGGING: Real 3D Model Connection")
    print("=====================================")
    
    # Test 1: Direct Replicate API
    real_models_work = test_real_3d_generation()
    
    # Test 2: Production API
    production_works = test_production_api()
    
    print("\n📊 SUMMARY")
    print("=" * 20)
    print(f"Real Models Available: {'✅ YES' if real_models_work else '❌ NO'}")
    print(f"Production API Working: {'✅ YES' if production_works else '❌ NO'}")
    
    if real_models_work and production_works:
        print("\n🎉 SUCCESS: Real 3D models are connected and working!")
    elif real_models_work:
        print("\n⚠️ PARTIAL: Models work but production API needs debugging")
    else:
        print("\n❌ FAILED: Real 3D models not working - using demo fallback")
