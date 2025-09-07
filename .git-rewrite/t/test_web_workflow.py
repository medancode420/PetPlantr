#!/usr/bin/env python3
"""
Complete Web Demo Test
Tests the full workflow: Upload Image -> Process -> View 3D Model
"""

import requests
import time
import os
from PIL import Image, ImageDraw

def create_test_dog_image():
    """Create a test dog image for upload"""
    print("🎨 Creating test dog image...")
    
    img = Image.new('RGB', (400, 400), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple golden retriever
    # Body
    draw.ellipse([100, 220, 300, 350], fill='goldenrod', outline='darkgoldenrod', width=2)
    
    # Head
    draw.ellipse([150, 120, 250, 220], fill='goldenrod', outline='darkgoldenrod', width=2)
    
    # Snout
    draw.ellipse([170, 160, 230, 200], fill='wheat', outline='darkgoldenrod', width=1)
    
    # Eyes
    draw.ellipse([165, 140, 185, 160], fill='black')
    draw.ellipse([215, 140, 235, 160], fill='black')
    
    # Nose
    draw.ellipse([190, 170, 210, 185], fill='black')
    
    # Ears (floppy)
    draw.ellipse([135, 120, 165, 170], fill='darkgoldenrod')
    draw.ellipse([235, 120, 265, 170], fill='darkgoldenrod')
    
    # Legs
    draw.rectangle([130, 320, 150, 380], fill='goldenrod')
    draw.rectangle([170, 320, 190, 380], fill='goldenrod')
    draw.rectangle([210, 320, 230, 380], fill='goldenrod')
    draw.rectangle([250, 320, 270, 380], fill='goldenrod')
    
    filename = "test_golden_retriever_web.jpg"
    img.save(filename)
    print(f"✅ Created test image: {filename}")
    return filename

def test_web_workflow():
    """Test the complete web workflow"""
    print("\n🌐 TESTING COMPLETE WEB WORKFLOW")
    print("="*50)
    
    base_url = "http://localhost:5001"
    
    # Step 1: Create test image
    test_image = create_test_dog_image()
    
    try:
        # Step 2: Upload image
        print("\n📤 Step 1: Uploading image...")
        with open(test_image, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{base_url}/api/upload", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            job_id = upload_result['job_id']
            print(f"✅ Upload successful! Job ID: {job_id}")
        else:
            print(f"❌ Upload failed: {response.text}")
            return
        
        # Step 3: Start processing
        print("\n🚀 Step 2: Starting processing...")
        response = requests.post(f"{base_url}/api/process/{job_id}")
        
        if response.status_code == 200:
            print("✅ Processing started!")
        else:
            print(f"❌ Processing failed to start: {response.text}")
            return
        
        # Step 4: Monitor progress
        print("\n⏱️  Step 3: Monitoring progress...")
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            response = requests.get(f"{base_url}/api/status/{job_id}")
            
            if response.status_code == 200:
                status = response.json()
                current_status = status['status']
                progress = status.get('progress', 0)
                current_step = status.get('current_step', 'Unknown')
                
                print(f"   📊 Status: {current_status} | Progress: {progress}% | Step: {current_step}")
                
                if current_status == 'completed':
                    print("✅ Processing completed!")
                    break
                elif current_status == 'failed':
                    print(f"❌ Processing failed: {status.get('error', 'Unknown error')}")
                    return
                
                time.sleep(2)
                attempt += 1
            else:
                print(f"❌ Status check failed: {response.text}")
                return
        
        if attempt >= max_attempts:
            print("⏰ Timeout waiting for processing to complete")
            return
        
        # Step 5: Get results
        print("\n📊 Step 4: Getting results...")
        response = requests.get(f"{base_url}/api/result/{job_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Results retrieved!")
            print(f"   🐕 Breed: {result['breed']}")
            print(f"   🎯 Confidence: {result['confidence']:.1%}")
            print(f"   📐 Vertices: {result['model_stats']['vertices']:,}")
            print(f"   🔺 Faces: {result['model_stats']['faces']:,}")
            print(f"   💾 File Size: {result['model_stats']['file_size']:,} bytes")
            print(f"   ⏱️  Generation Time: {result['generation_time']:.1f}s")
            print(f"   📥 STL Download: {base_url}{result['stl_url']}")
            print(f"   🎯 3D Viewer: {base_url}{result['viewer_url']}")
            
            # Step 6: Open 3D viewer
            print(f"\n🎪 Step 5: Opening 3D viewer...")
            viewer_url = f"{base_url}{result['viewer_url']}"
            print(f"🔗 Viewer URL: {viewer_url}")
            
            # Test download
            print(f"\n📥 Step 6: Testing STL download...")
            download_response = requests.get(f"{base_url}{result['stl_url']}")
            if download_response.status_code == 200:
                download_filename = f"downloaded_{result['breed']}_planter.stl"
                with open(download_filename, 'wb') as f:
                    f.write(download_response.content)
                print(f"✅ STL downloaded: {download_filename} ({len(download_response.content):,} bytes)")
            else:
                print(f"❌ Download failed: {download_response.text}")
            
            print(f"\n🎉 COMPLETE SUCCESS!")
            print(f"✅ Image uploaded and processed")
            print(f"✅ Dog breed detected: {result['breed']}")
            print(f"✅ 3D planter model generated")
            print(f"✅ STL file ready for 3D printing")
            print(f"✅ Interactive 3D viewer available")
            print(f"\n🌐 Open viewer: {viewer_url}")
            
            return viewer_url
            
        else:
            print(f"❌ Results retrieval failed: {response.text}")
            return
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return
    
    finally:
        # Cleanup
        try:
            os.remove(test_image)
            print(f"🧹 Cleaned up test image")
        except:
            pass

if __name__ == "__main__":
    print("🧪 PetPlantr Complete Web Workflow Test")
    print("Testing: Upload → Process → View → Download")
    
    viewer_url = test_web_workflow()
    
    if viewer_url:
        print(f"\n🎯 SUCCESS! Complete workflow working.")
        print(f"📱 Test the web interface: http://localhost:5001")
        print(f"🎪 View your generated planter: {viewer_url}")
    else:
        print(f"\n❌ Workflow test failed. Check server logs.")
