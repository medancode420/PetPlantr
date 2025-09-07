#!/usr/bin/env python3
"""
Test script to verify watertight mesh generation
Tests the improved image-to-3D converter with enhanced closed-loop mesh creation
"""

import os
import sys
import numpy as np
from PIL import Image
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from image_to_3d_converter import ImageTo3DConverter

def create_test_design_image():
    """Create a simple test design image for testing"""
    # Create a simple dog-like silhouette on white background
    width, height = 400, 400
    image = Image.new('RGB', (width, height), 'white')
    
    # Create a simple shape array (ellipse representing a dog)
    import numpy as np
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(image)
    
    # Draw a simple dog-like shape using RGB colors
    brown = (139, 69, 19)  # Brown color
    dark_brown = (101, 67, 33)  # Dark brown color
    
    # Body (ellipse)
    draw.ellipse([100, 200, 300, 320], fill=brown, outline=dark_brown, width=2)
    
    # Head (circle)
    draw.ellipse([80, 120, 180, 220], fill=brown, outline=dark_brown, width=2)
    
    # Ears
    draw.ellipse([70, 110, 110, 150], fill=brown, outline=dark_brown, width=1)
    draw.ellipse([140, 110, 180, 150], fill=brown, outline=dark_brown, width=1)
    
    # Legs
    draw.rectangle([130, 310, 150, 380], fill=brown, outline=dark_brown, width=1)
    draw.rectangle([180, 310, 200, 380], fill=brown, outline=dark_brown, width=1)
    draw.rectangle([230, 310, 250, 380], fill=brown, outline=dark_brown, width=1)
    draw.rectangle([260, 310, 280, 380], fill=brown, outline=dark_brown, width=1)
    
    # Tail
    draw.ellipse([290, 180, 350, 220], fill=brown, outline=dark_brown, width=1)
    
    test_path = "test_dog_design.png"
    image.save(test_path)
    print(f"✅ Created test design image: {test_path}")
    return test_path

def test_watertight_generation():
    """Test watertight mesh generation with different methods"""
    print("🧪 Testing Watertight Mesh Generation")
    print("=" * 50)
    
    # Create test image
    test_image = create_test_design_image()
    
    converter = ImageTo3DConverter()
    
    # Test all conversion methods
    methods = [
        ('Depth Estimation', converter.convert_with_depth_estimation),
        ('Procedural Extrusion', converter.convert_with_procedural_extrusion),
    ]
    
    results = {}
    
    for method_name, method_func in methods:
        print(f"\n🔬 Testing {method_name}...")
        print("-" * 30)
        
        timestamp = int(time.time())
        output_path = f"test_watertight_{method_name.lower().replace(' ', '_')}_{timestamp}.stl"
        
        # Test the method
        success = method_func(test_image, output_path)
        
        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            
            # Try to load with trimesh to verify
            try:
                import trimesh
                mesh = trimesh.load(output_path)
                
                results[method_name] = {
                    'success': True,
                    'file_path': output_path,
                    'file_size': file_size,
                    'vertices': len(mesh.vertices),
                    'faces': len(mesh.faces),
                    'is_watertight': mesh.is_watertight,
                    'is_volume': mesh.is_volume,
                    'volume': mesh.volume if mesh.is_volume else 0,
                    'is_winding_consistent': mesh.is_winding_consistent
                }
                
                print(f"✅ {method_name} - Success!")
                print(f"   📁 File: {output_path} ({file_size} bytes)")
                print(f"   🔧 Mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
                print(f"   💧 Watertight: {mesh.is_watertight}")
                print(f"   📦 Volume: {mesh.is_volume}")
                print(f"   🌊 Volume value: {mesh.volume:.2f}")
                print(f"   🔄 Winding consistent: {mesh.is_winding_consistent}")
                
                if mesh.is_watertight:
                    print(f"   🎉 SUCCESS: Mesh is WATERTIGHT (closed-loop)!")
                else:
                    print(f"   ❌ FAIL: Mesh is NOT watertight (open-loop)")
                    
            except Exception as e:
                results[method_name] = {
                    'success': False,
                    'error': f"Mesh loading failed: {e}"
                }
                print(f"❌ {method_name} - Mesh loading failed: {e}")
        else:
            results[method_name] = {
                'success': False,
                'error': "Method failed or no output file"
            }
            print(f"❌ {method_name} - Method failed")
    
    # Summary
    print("\n📊 WATERTIGHT TEST SUMMARY")
    print("=" * 50)
    
    watertight_methods = []
    for method, result in results.items():
        if result.get('success') and result.get('is_watertight'):
            watertight_methods.append(method)
            print(f"✅ {method}: WATERTIGHT ✨")
        elif result.get('success'):
            print(f"⚠️  {method}: Generated mesh but NOT watertight")
        else:
            print(f"❌ {method}: Failed")
    
    if watertight_methods:
        print(f"\n🎉 SUCCESS: {len(watertight_methods)} method(s) produced watertight meshes!")
        print("   Your 3D models should now be closed-loop and printable!")
    else:
        print(f"\n❌ CONCERN: No methods produced watertight meshes.")
        print("   This means the models may still be open-loop.")
    
    # Cleanup test image
    if os.path.exists(test_image):
        os.remove(test_image)
    
    return results

def test_full_pipeline():
    """Test the complete pipeline including cavity and drainage"""
    print("\n🔬 Testing Full Pipeline with Cavity and Drainage")
    print("=" * 50)
    
    test_image = create_test_design_image()
    converter = ImageTo3DConverter()
    
    # Test full conversion
    result = converter.convert_image_to_3d(test_image)
    
    if result.get('success'):
        output_path = result['output_stl']
        print(f"✅ Full pipeline successful!")
        print(f"   📁 Output: {output_path}")
        print(f"   📊 Method: {result['method']}")
        
        # Verify the final result
        try:
            import trimesh
            mesh = trimesh.load(output_path)
            
            print(f"   🔧 Final mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
            print(f"   💧 Watertight: {mesh.is_watertight}")
            print(f"   📦 Volume: {mesh.is_volume}")
            print(f"   🌊 Volume value: {mesh.volume:.2f}")
            
            if mesh.is_watertight:
                print(f"   🎉 FINAL SUCCESS: Complete pipeline produces WATERTIGHT mesh!")
            else:
                print(f"   ⚠️  FINAL RESULT: Pipeline produces non-watertight mesh")
                
        except Exception as e:
            print(f"   ❌ Could not verify final mesh: {e}")
    else:
        print(f"❌ Full pipeline failed: {result.get('error', 'Unknown error')}")
    
    # Cleanup
    if os.path.exists(test_image):
        os.remove(test_image)
    
    return result

if __name__ == "__main__":
    print("🧪 WATERTIGHT MESH TESTING SUITE")
    print("Testing enhanced image-to-3D converter for closed-loop mesh generation")
    print("=" * 70)
    
    try:
        # Test individual methods
        method_results = test_watertight_generation()
        
        # Test full pipeline
        pipeline_result = test_full_pipeline()
        
        print("\n🏁 FINAL RESULTS")
        print("=" * 50)
        
        # Check if we have any watertight results
        watertight_count = sum(1 for r in method_results.values() 
                              if r.get('success') and r.get('is_watertight'))
        
        if watertight_count > 0:
            print(f"🎉 SUCCESS! {watertight_count} method(s) produce watertight meshes")
            print("   Your PetPlantr pipeline should now generate closed-loop models!")
            print("   The 3D models will be properly manifold for 3D printing.")
        else:
            print("❌ No watertight meshes generated.")
            print("   Additional debugging may be needed.")
        
        print(f"\n📁 Generated test files can be found in the current directory")
        print(f"   Look for files matching: test_watertight_*.stl")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
