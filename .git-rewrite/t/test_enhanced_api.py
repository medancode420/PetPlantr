#!/usr/bin/env python3
"""
Test script for the enhanced PetPlantr API
Demonstrates the new comprehensive 3D model generation features
"""

import requests
import json
import time
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_IMAGE_URL = "https://images.unsplash.com/photo-1551717952-65b0c9c8aa60"  # Sample dog image

def test_enhanced_api():
    """Test the enhanced API endpoint with comprehensive options"""
    
    print("🧪 Testing Enhanced PetPlantr API")
    print("=" * 50)
    
    # Test 1: Basic enhanced generation
    print("\n1️⃣ Testing basic enhanced generation...")
    
    basic_data = {
        "image_url": TEST_IMAGE_URL,
        "quality_level": "ultra-high",
        "breed": "Golden Retriever",
        "options": json.dumps({
            "include_detailed": True,
            "analyze_colors": True,
            "photo_style": "studio",
            "include_profile": True
        })
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/generate-enhanced-3d-simple",
        data=basic_data,
        headers={"Authorization": "Bearer pk_demo_token"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! Generated model: {result['model_url']}")
        print(f"📊 Quality: {result['quality_metrics']['quality_level']}")
        print(f"🐕 Breed: {result['breed_analysis']['breed']} ({result['breed_analysis']['confidence']:.1%} confidence)")
        print(f"⏱️ Processing time: {result['processing_time']}")
        print(f"💰 Estimated cost: {result['estimated_cost']}")
        
        if result.get('additional_features'):
            features = result['additional_features']
            print(f"🪴 Features: Drainage={features['drainage_holes']}, Reservoir={features['water_reservoir']}")
            print(f"📝 Care instructions: {len(features['care_instructions'])} tips provided")
        
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 2: Advanced options
    print("\n2️⃣ Testing advanced options...")
    
    advanced_data = {
        "image_url": TEST_IMAGE_URL,
        "quality_level": "production",
        "breed": "Border Collie",
        "options": json.dumps({
            "include_detailed": True,
            "analyze_colors": True,
            "analyze_dimensions": True,
            "photo_style": "natural",
            "include_profile": True,
            "image_width": 1024,
            "image_height": 1024,
            "quality": "high",
            "texture_size": 2048,
            "mesh_simplify": 0.9,
            "optimization_level": "high",
            "target_poly_count": 20000,
            "minimize_supports": True,
            "planter_size": "large",
            "include_drainage": True,
            "include_reservoir": True,
            "custom_text": "Smart Pup Planter",
            "plant_type": "herbs",
            "preferred_material": "PETG",
            "infill_percentage": "25%",
            "print_speed": "40mm/s"
        })
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/generate-enhanced-3d-simple",
        data=advanced_data,
        headers={"Authorization": "Bearer pk_demo_token"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Advanced generation successful!")
        print(f"🎯 Target polygons: {result['quality_metrics']['polygon_count']:,}")
        print(f"🏗️ Mesh quality: {result['quality_metrics']['mesh_quality']:.1f}%")
        print(f"📐 Geometry score: {result['quality_metrics']['geometry_score']:.1f}%")
        print(f"🧱 Material: {result['metadata']['recommended_material']}")
        print(f"⏱️ Print time: {result['metadata']['estimated_print_time']}")
        print(f"🗂️ Available formats: GLB, STL, OBJ")
        
        if result['metadata'].get('filament_usage'):
            print(f"🧵 Filament usage: {result['metadata']['filament_usage']}")
    else:
        print(f"❌ Error: {response.text}")
    
    # Test 3: Rate limiting
    print("\n3️⃣ Testing rate limiting...")
    
    rate_limit_data = {
        "image_url": TEST_IMAGE_URL,
        "quality_level": "standard",
        "breed": "Pug"
    }
    
    # Make rapid requests to test rate limiting
    for i in range(3):
        response = requests.post(
            f"{API_BASE_URL}/api/v1/generate-enhanced-3d-simple",
            data=rate_limit_data,
            headers={"Authorization": "Bearer pk_demo_token"}
        )
        print(f"Request {i+1}: {response.status_code}")
        if response.status_code == 429:
            print("✅ Rate limiting working correctly!")
            break
        time.sleep(0.1)
    
    # Test 4: Error handling
    print("\n4️⃣ Testing error handling...")
    
    # Invalid image URL
    invalid_data = {
        "image_url": "not-a-valid-url",
        "quality_level": "high"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/generate-enhanced-3d-simple",
        data=invalid_data,
        headers={"Authorization": "Bearer pk_demo_token"}
    )
    
    print(f"Invalid URL test: {response.status_code}")
    if response.status_code == 400:
        print("✅ Error validation working correctly!")
    
    print("\n" + "=" * 50)
    print("🎉 Enhanced API testing complete!")

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{API_BASE_URL}/api/v1/health")
    if response.status_code == 200:
        health = response.json()
        print(f"🏥 Health Check: {health['status']}")
        print(f"🧠 Neural Pipeline: {'✅' if health['neural_pipeline'] else '❌'}")
        print(f"📊 Active Jobs: {health['active_jobs']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")

def demonstrate_features():
    """Demonstrate the key enhanced features"""
    print("\n🚀 Enhanced PetPlantr API Features:")
    print("=" * 50)
    
    features = [
        "✨ Comprehensive breed analysis with confidence scoring",
        "🎨 Enhanced image generation with multiple styles",
        "🏗️ Advanced 3D model generation using TRELLIS AI",
        "⚙️ Configurable optimization levels and mesh quality",
        "🪴 Smart planter integration with drainage options", 
        "📐 Customizable dimensions and print settings",
        "🧱 Material recommendations and print parameters",
        "🔄 Multiple output formats (GLB, STL, OBJ)",
        "📊 Detailed quality metrics and performance data",
        "🛡️ Rate limiting and enhanced error handling",
        "💰 Cost estimation for different quality levels",
        "📝 Plant care instructions based on breed personality",
        "🎯 Polygon count optimization for 3D printing",
        "🔧 Advanced mesh simplification options",
        "🌈 Color analysis and texture generation",
        "📱 Development and production mode support"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n📋 API Endpoints:")
    endpoints = [
        "POST /api/v1/generate-enhanced-3d-simple - Enhanced 3D generation",
        "GET  /api/v1/health - System health check", 
        "POST /api/v1/generate-planter - Legacy planter generation",
        "GET  /api/v1/status/{job_id} - Job status tracking",
        "GET  /api/v1/download/{job_id}/stl - File downloads"
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint}")

if __name__ == "__main__":
    print("🐕 PetPlantr Enhanced API Test Suite")
    print("🔧 Make sure the API server is running: python api_server.py")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running!")
            test_health_check()
            demonstrate_features()
            
            # Run tests
            user_input = input("\n🧪 Run full test suite? (y/n): ").lower()
            if user_input in ['y', 'yes']:
                test_enhanced_api()
            else:
                print("📋 Test suite skipped. Use 'python test_enhanced_api.py' to run tests.")
        else:
            print(f"❌ API server returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("💡 Start the server with: python api_server.py")
