#!/usr/bin/env python3
"""
Quick health check for PetPlantr local environment
Tests if the API works with the configured Replicate token
"""

import os
import requests
import time
import subprocess
import signal
import sys
import json

def test_environment():
    """Test the environment configuration"""
    print("🔍 Testing Environment Configuration")
    print("=" * 40)
    
    # Check .env.local
    env_file = "/Users/medan/Downloads/PetPlantr/frontend/.env.local"
    if os.path.exists(env_file):
        print("✅ .env.local file found")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'REPLICATE_API_TOKEN=r8_' in content:
                print("✅ Replicate API token configured")
                return True
            else:
                print("❌ Replicate API token not found or invalid")
                return False
    else:
        print("❌ .env.local file not found")
        return False

def start_dev_server():
    """Start the Next.js development server"""
    print("\n🚀 Starting development server...")
    os.chdir("/Users/medan/Downloads/PetPlantr/frontend")
    
    # Start the server
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(10)
    
    return process

def test_api_endpoints(max_retries=5):
    """Test the API endpoints"""
    print("\n🧪 Testing API Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:3000"
    
    for attempt in range(max_retries):
        try:
            # Test health endpoint
            print(f"📋 Testing health endpoint (attempt {attempt + 1})...")
            response = requests.get(f"{base_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Health endpoint: WORKING")
                print(f"   Pipeline: {data.get('pipeline', 'undefined')}")
                print(f"   Has Replicate Token: {data.get('environment', {}).get('hasReplicateToken', False)}")
                
                # Check if real models are configured
                if data.get('pipeline') == 'real':
                    print("✅ Real AI models: CONFIRMED")
                else:
                    print("⚠️  Real AI models: NOT CONFIRMED")
                
                return True
            else:
                print(f"❌ Health endpoint failed: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"⏳ Server not ready yet (attempt {attempt + 1})...")
            time.sleep(3)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_quick_generation():
    """Test a quick AI generation"""
    print("\n⚡ Testing Quick AI Generation")
    print("=" * 40)
    
    try:
        response = requests.post(
            "http://localhost:3000/api/replicate",
            json={"prompt": "simple geometric pet planter test"},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ AI Generation: STARTED")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Model: {data.get('usedModel', 'unknown')}")
            print("🎯 SUCCESS: Real AI models are working!")
            return True
        else:
            print(f"❌ AI Generation failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ AI Generation error: {e}")
        return False

def main():
    print("🎯 PetPlantr Local Environment Validator")
    print("=" * 50)
    
    # Step 1: Test environment
    if not test_environment():
        print("\n❌ Environment configuration failed!")
        print("Please check your .env.local file")
        return False
    
    # Step 2: Start development server
    server_process = None
    try:
        server_process = start_dev_server()
        
        # Step 3: Test API endpoints
        if test_api_endpoints():
            print("\n✅ API endpoints working!")
            
            # Step 4: Test AI generation
            if test_quick_generation():
                print("\n🎉 SUCCESS: PetPlantr is fully functional!")
                print("=" * 50)
                print("🌐 Open in browser: http://localhost:3000")
                print("🔧 API health check: http://localhost:3000/api/health")
                print("\nPress Enter to stop the server...")
                input()
                return True
            else:
                print("\n⚠️  API working but AI generation needs attention")
        else:
            print("\n❌ API endpoints failed!")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        # Clean up server process
        if server_process:
            print("\n🛑 Stopping development server...")
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
