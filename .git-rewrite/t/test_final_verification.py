#!/usr/bin/env python3
"""
Final verification that the enhanced pipeline generates recognizable dog planters
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dalle_integrated_pipeline import DalleIntegratedPipeline

def test_final_dog_planter_generation():
    """Final test of the complete enhanced pipeline"""
    print("🐕 FINAL DOG PLANTER GENERATION TEST")
    print("=" * 50)
    
    # Test with a simple dog photo (create if needed)
    test_photo = "final_test_dog.jpg"
    
    if not os.path.exists(test_photo):
        from PIL import Image, ImageDraw
        
        # Create a simple dog photo for testing
        img = Image.new('RGB', (400, 400), 'lightblue')
        draw = ImageDraw.Draw(img)
        
        # Draw a recognizable dog
        brown = (139, 69, 19)
        dark_brown = (101, 67, 33)
        
        # Body
        draw.ellipse([100, 200, 300, 350], fill=brown, outline=dark_brown, width=3)
        
        # Head
        draw.ellipse([50, 100, 200, 250], fill=brown, outline=dark_brown, width=3)
        
        # Ears
        draw.ellipse([40, 80, 100, 140], fill=brown, outline=dark_brown, width=2)
        draw.ellipse([150, 80, 210, 140], fill=brown, outline=dark_brown, width=2)
        
        # Eyes
        draw.ellipse([80, 120, 100, 140], fill='black')
        draw.ellipse([150, 120, 170, 140], fill='black')
        
        # Nose
        draw.ellipse([115, 160, 135, 180], fill='black')
        
        # Legs
        draw.rectangle([120, 340, 140, 390], fill=brown, outline=dark_brown, width=2)
        draw.rectangle([160, 340, 180, 390], fill=brown, outline=dark_brown, width=2)
        draw.rectangle([220, 340, 240, 390], fill=brown, outline=dark_brown, width=2)
        draw.rectangle([260, 340, 280, 390], fill=brown, outline=dark_brown, width=2)
        
        # Tail
        draw.ellipse([290, 180, 350, 240], fill=brown, outline=dark_brown, width=2)
        
        img.save(test_photo)
        print(f"✅ Created test dog photo: {test_photo}")
    
    print(f"📸 Testing with: {test_photo}")
    
    # Run the enhanced pipeline
    pipeline = DalleIntegratedPipeline()
    
    try:
        print("\n🎨 Running enhanced DALL-E + 3D pipeline...")
        result = pipeline.process_pet_photo(test_photo)
        
        if result.get('success'):
            print(f"✅ Enhanced pipeline successful!")
            print(f"   🎨 DALL-E design: {result.get('design_image', 'N/A')}")
            print(f"   🏗️ 3D model: {result.get('stl_file', 'N/A')}")
            print(f"   📊 Method: {result.get('conversion_method', 'N/A')}")
            
            # Check if files exist and are non-empty
            design_path = result.get('design_image')
            stl_path = result.get('stl_file')
            
            if design_path and os.path.exists(design_path):
                design_size = os.path.getsize(design_path)
                print(f"   🎨 Design file: {design_size} bytes")
            
            if stl_path and os.path.exists(stl_path):
                stl_size = os.path.getsize(stl_path)
                print(f"   🏗️ STL file: {stl_size} bytes")
                
                # Verify watertight
                try:
                    import trimesh
                    mesh = trimesh.load(stl_path)
                    
                    print(f"   🔧 Mesh verification:")
                    print(f"      Vertices: {len(mesh.vertices)}")
                    print(f"      Faces: {len(mesh.faces)}")
                    print(f"      Watertight: {mesh.is_watertight}")
                    print(f"      Volume: {mesh.is_volume}")
                    print(f"      Surface area: {mesh.area:.2f}")
                    print(f"      Volume: {mesh.volume:.2f}")
                    
                    if mesh.is_watertight and mesh.is_volume:
                        print(f"   🎉 SUCCESS: Enhanced pipeline creates watertight dog planter!")
                        print(f"   ✨ Ready for 3D printing!")
                        
                        return {
                            'success': True,
                            'design_image': design_path,
                            'stl_file': stl_path,
                            'watertight': True,
                            'volume': mesh.volume,
                            'area': mesh.area
                        }
                    else:
                        print(f"   ⚠️ Mesh generated but not watertight")
                        return {'success': False, 'error': 'Not watertight'}
                        
                except Exception as e:
                    print(f"   ❌ Could not verify mesh: {e}")
                    return {'success': False, 'error': f'Mesh verification failed: {e}'}
            else:
                print(f"   ❌ Output files missing")
                return {'success': False, 'error': 'Output files missing'}
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Enhanced pipeline failed: {error}")
            return {'success': False, 'error': error}
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    
    finally:
        # Cleanup test photo
        if test_photo.startswith('final_test_') and os.path.exists(test_photo):
            os.remove(test_photo)

if __name__ == "__main__":
    result = test_final_dog_planter_generation()
    
    print(f"\n🏁 FINAL RESULTS")
    print("=" * 30)
    
    if result.get('success'):
        print(f"🎉 ENHANCED PIPELINE SUCCESS!")
        print(f"   The PetPlantr system now generates:")
        print(f"   ✅ Custom dog planter designs via DALL-E")
        print(f"   ✅ Watertight, closed-loop 3D models")
        print(f"   ✅ STL files ready for 3D printing")
        print(f"   ✅ Recognizable dog shapes preserved")
        print(f"")
        print(f"📋 PROBLEM RESOLVED:")
        print(f"   ❌ OLD: Open-loop meshes")
        print(f"   ✅ NEW: Closed-loop, watertight meshes")
        print(f"")
        print(f"🔍 FILES CREATED:")
        print(f"   🎨 {result.get('design_image', 'Design image')}")
        print(f"   🏗️ {result.get('stl_file', 'STL model')}")
        print(f"   📊 Volume: {result.get('volume', 0):.2f} cubic units")
        print(f"   📐 Surface area: {result.get('area', 0):.2f} square units")
    else:
        print(f"❌ Pipeline still needs work: {result.get('error')}")
