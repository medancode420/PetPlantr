#!/usr/bin/env python3
"""
Test the integrated pipeline with different dog breeds to validate AI integration
"""

import sys
import os
from PIL import Image, ImageDraw
import numpy as np

# Create test images for different breeds
def create_test_dog_image(breed_name, filename):
    """Create a simple test image that might represent different breeds"""
    img = Image.new('RGB', (224, 224), 'white')
    draw = ImageDraw.Draw(img)
    
    # Create different patterns for different "breeds"
    if breed_name == "pug":
        # Pug-like: round face, short snout
        draw.ellipse([50, 50, 174, 174], fill='brown')
        draw.ellipse([80, 90, 144, 134], fill='black')  # Short snout
        draw.ellipse([90, 70, 110, 90], fill='black')   # Eye
        draw.ellipse([114, 70, 134, 90], fill='black')  # Eye
    elif breed_name == "golden":
        # Golden retriever-like: longer snout, fluffy
        draw.ellipse([40, 40, 184, 184], fill='gold')
        draw.ellipse([70, 100, 154, 144], fill='darkgoldenrod')  # Longer snout
        draw.ellipse([80, 70, 100, 90], fill='black')   # Eye
        draw.ellipse([124, 70, 144, 90], fill='black')  # Eye
    elif breed_name == "german":
        # German shepherd-like: pointed ears, angular face
        draw.polygon([(112, 20), (90, 80), (134, 80)], fill='brown')  # Angular face
        draw.ellipse([60, 100, 164, 164], fill='brown')
        draw.ellipse([85, 90, 105, 110], fill='black')  # Eye
        draw.ellipse([119, 90, 139, 110], fill='black') # Eye
    else:
        # Default dog
        draw.ellipse([60, 60, 164, 164], fill='tan')
        draw.ellipse([80, 110, 144, 154], fill='brown')  # Snout
        draw.ellipse([90, 80, 110, 100], fill='black')   # Eye
        draw.ellipse([114, 80, 134, 100], fill='black')  # Eye
    
    img.save(filename)
    print(f"📸 Created test image: {filename} ({breed_name})")

def test_pipeline_with_breed(breed_name, image_file):
    """Test the pipeline with a specific breed image"""
    print(f"\n🧪 TESTING BREED: {breed_name.upper()}")
    print("=" * 50)
    
    # Modify integrated_pipeline to accept custom image
    import subprocess
    result = subprocess.run([
        sys.executable, 'integrated_pipeline.py', image_file
    ], capture_output=True, text=True, cwd='/Users/medan/Downloads/PetPlantr')
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def main():
    """Test multiple breeds with the integrated pipeline"""
    os.chdir('/Users/medan/Downloads/PetPlantr')
    
    print("🎯 BREED DETECTION TEST SUITE")
    print("=" * 60)
    print("Testing AI model integration with different dog breeds...")
    
    # Create test images
    breeds = ["pug", "golden", "german", "mixed"]
    test_images = []
    
    for breed in breeds:
        filename = f"test_{breed}_dog.jpg"
        create_test_dog_image(breed, filename)
        test_images.append((breed, filename))
    
    # Test each breed
    results = {}
    for breed, image_file in test_images:
        success = test_pipeline_with_breed(breed, image_file)
        results[breed] = success
    
    # Summary
    print("\n🏆 TEST RESULTS SUMMARY")
    print("=" * 40)
    successful = sum(results.values())
    total = len(results)
    
    for breed, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{breed:12} : {status}")
    
    print(f"\nOverall: {successful}/{total} tests passed")
    
    if successful == total:
        print("🎉 ALL TESTS PASSED! AI integration is working!")
    else:
        print("⚠️  Some tests failed. Check the outputs above.")

if __name__ == "__main__":
    main()
