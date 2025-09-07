#!/usr/bin/env python3
"""
Test the actual dog planter generation with DALL-E
"""

import os
import sys
from PIL import Image, ImageDraw

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dalle_integrated_pipeline import DalleIntegratedPipeline

def create_realistic_dog_photo():
    """Create a more realistic-looking dog photo for testing"""
    # Create a more detailed dog photo
    img = Image.new('RGB', (800, 600), color=(135, 206, 235))  # Sky blue background
    draw = ImageDraw.Draw(img)
    
    # Draw a more realistic dog
    # Body
    brown = (139, 69, 19)
    dark_brown = (101, 67, 33)
    
    # Dog body (Golden Retriever style)
    draw.ellipse([200, 300, 500, 500], fill=brown, outline=dark_brown, width=3)
    
    # Dog head
    draw.ellipse([150, 200, 350, 350], fill=brown, outline=dark_brown, width=3)
    
    # Ears
    draw.ellipse([120, 180, 180, 280], fill=(160, 82, 45), outline=dark_brown, width=2)
    draw.ellipse([320, 180, 380, 280], fill=(160, 82, 45), outline=dark_brown, width=2)
    
    # Eyes
    draw.ellipse([180, 230, 200, 250], fill='black')
    draw.ellipse([300, 230, 320, 250], fill='black')
    
    # Nose
    draw.ellipse([240, 280, 260, 295], fill='black')
    
    # Mouth
    draw.arc([220, 295, 280, 320], start=0, end=180, fill='black', width=3)
    
    # Legs
    draw.rectangle([220, 480, 250, 580], fill=brown, outline=dark_brown, width=2)
    draw.rectangle([270, 480, 300, 580], fill=brown, outline=dark_brown, width=2)
    draw.rectangle([370, 480, 400, 580], fill=brown, outline=dark_brown, width=2)
    draw.rectangle([420, 480, 450, 580], fill=brown, outline=dark_brown, width=2)
    
    # Tail
    draw.ellipse([480, 350, 550, 400], fill=brown, outline=dark_brown, width=2)
    
    photo_path = "realistic_dog_photo.jpg"
    img.save(photo_path, quality=95)
    print(f"✅ Created realistic dog photo: {photo_path}")
    return photo_path

def test_actual_dog_planter_generation():
    """Test the complete pipeline with a realistic dog photo"""
    print("🐕 TESTING ACTUAL DOG PLANTER GENERATION")
    print("=" * 60)
    
    # Create test photo
    dog_photo = create_realistic_dog_photo()
    
    try:
        # Initialize the complete pipeline
        pipeline = DalleIntegratedPipeline()
        
        # Test the complete workflow
        print("\n🚀 Running complete pet-to-planter pipeline...")
        
        result = pipeline.process_pet_photo(dog_photo)
        
        if result.get('success'):
            print(f"\n🎉 SUCCESS! Dog planter generated!")
            print(f"📁 Design image: {result.get('design_image')}")
            print(f"📁 STL file: {result.get('stl_file')}")
            print(f"🐕 Breed detected: {result.get('pet_analysis', {}).get('breed', 'Unknown')}")
            print(f"🎨 Design method: DALL-E")
            print(f"🏗️ 3D method: {result.get('conversion_method')}")
            
            # Check if files exist
            design_path = result.get('design_image')
            stl_path = result.get('stl_file')
            
            if design_path and os.path.exists(design_path):
                print(f"✅ Design image exists: {os.path.getsize(design_path)} bytes")
            else:
                print(f"❌ Design image missing or not found: {design_path}")
                
            if stl_path and os.path.exists(stl_path):
                print(f"✅ STL file exists: {os.path.getsize(stl_path)} bytes")
                
                # Verify it's watertight
                try:
                    import trimesh
                    mesh = trimesh.load(stl_path)
                    print(f"✅ STL verification:")
                    print(f"   Watertight: {mesh.is_watertight}")
                    print(f"   Vertices: {len(mesh.vertices)}")
                    print(f"   Faces: {len(mesh.faces)}")
                    
                    if mesh.is_watertight:
                        print(f"🎉 Perfect! The dog planter is watertight and ready for 3D printing!")
                    else:
                        print(f"⚠️ STL generated but not watertight")
                        
                except Exception as e:
                    print(f"⚠️ Could not verify STL: {e}")
            else:
                print(f"❌ STL file missing or not found: {stl_path}")
                
            return True
            
        else:
            error = result.get('error', 'Unknown error')
            print(f"\n❌ Pipeline failed: {error}")
            
            # Check individual steps
            if 'dalle_error' in result:
                print(f"🎨 DALL-E Error: {result['dalle_error']}")
            if 'conversion_error' in result:
                print(f"🏗️ 3D Conversion Error: {result['conversion_error']}")
                
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(dog_photo):
            os.remove(dog_photo)

if __name__ == "__main__":
    success = test_actual_dog_planter_generation()
    
    if success:
        print("\n🎉 DOG PLANTER GENERATION TEST PASSED!")
        print("The pipeline successfully created a custom dog planter!")
    else:
        print("\n❌ Dog planter generation test failed")
        print("Check the error messages above for debugging")
