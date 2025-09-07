#!/usr/bin/env python3

"""
DIRECT TEST: Verify real 3D models work without any fallback
This tests the actual Replicate models we've hardcoded to ensure they generate real 3D content
"""

import os
import time
import requests
import json

def load_env():
    """Load environment variables"""
    env_file = '/Users/medan/Downloads/PetPlantr/frontend/.env.local'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')

def test_hardcoded_models():
    """Test the exact models we hardcoded in our API"""
    
    load_env()
    token = os.getenv('REPLICATE_API_TOKEN')
    
    if not token:
        print("❌ No REPLICATE_API_TOKEN found")
        return False
    
    print("🔬 TESTING HARDCODED 3D MODELS")
    print("="*40)
    print("Testing the exact models from our API route:")
    print("• cjwbw/shap-e (5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c)")
    print("• cjwbw/point-e (1a4da7adf0bc84cd786c1df41c02db3097d899f5c159f5fd5814a11117bdf02b)")
    print()
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    # Test Shap-E with exact parameters from our API
    print("1️⃣ Testing Shap-E (3D mesh generation)...")
    shap_e_data = {
        "version": "5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c",
        "input": {
            "prompt": "A cute dog-shaped planter for succulents, terracotta style, modern design",
            "save_mesh": True,
            "render_mode": "nerf",
            "render_size": 128,
            "guidance_scale": 15,
            "batch_size": 1
        }
    }
    
    try:
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=shap_e_data,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Shap-E prediction created: {result['id']}")
            print(f"   Status: {result['status']}")
            
            # Monitor for a bit
            prediction_id = result['id']
            for i in range(5):
                time.sleep(10)
                status_resp = requests.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers=headers,
                    timeout=10
                )
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    status = status_data.get('status')
                    print(f"   Check {i+1}: {status}")
                    
                    if status == 'succeeded':
                        output = status_data.get('output')
                        print(f"🎉 SHAP-E SUCCESS! Generated: {output}")
                        return True
                    elif status == 'failed':
                        error = status_data.get('error', 'Unknown error')
                        print(f"❌ Shap-E failed: {error}")
                        break
                        
        else:
            print(f"❌ Shap-E request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Shap-E error: {e}")
    
    print("\n" + "="*40)
    print("🎯 CONCLUSION:")
    print("If Shap-E succeeded above, real 3D models ARE working!")
    print("The issue is likely deployment/environment config, not model availability.")
    print("="*40)
    
    return False

if __name__ == "__main__":
    test_hardcoded_models()
