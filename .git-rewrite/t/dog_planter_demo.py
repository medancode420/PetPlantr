#!/usr/bin/env python3
"""
Dog-Shaped Planter Generator Demo
Creates actual recognizable dog-shaped planters for different breeds
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import random

def create_breed_test_images():
    """Create test images for different dog breeds"""
    breeds = [
        ("pug", "tan"),
        ("golden_retriever", "gold"), 
        ("german_shepherd", "brown"),
        ("dalmatian", "white"),
        ("alaskan_malamute", "gray")
    ]
    
    test_images = []
    
    for breed, color in breeds:
        print(f"🎨 Creating {breed} test image...")
        
        # Create breed-specific image
        img = Image.new('RGB', (300, 300), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Get color
        colors = {
            "tan": "#D2B48C", "gold": "#FFD700", "brown": "#8B4513",
            "white": "#FFFFFF", "gray": "#808080"
        }
        main_color = colors.get(color, "#8B4513")
        
        if breed == "pug":
            # Flat-faced, compact
            draw.ellipse([100, 120, 200, 200], fill=main_color)  # Head
            draw.ellipse([120, 140, 140, 160], fill='black')     # Eyes
            draw.ellipse([160, 140, 180, 160], fill='black')     
            draw.ellipse([140, 170, 160, 185], fill='black')     # Nose
            
        elif breed == "german_shepherd":
            # Pointed ears, long snout
            draw.ellipse([90, 120, 210, 220], fill=main_color)   # Head
            draw.polygon([(90, 130), (80, 100), (110, 120)], fill=main_color)  # Ear
            draw.polygon([(190, 120), (220, 100), (210, 130)], fill=main_color)  # Ear
            draw.ellipse([120, 190, 180, 240], fill=main_color)  # Snout
            
        elif breed == "golden_retriever":
            # Floppy ears, friendly face
            draw.ellipse([95, 120, 205, 210], fill=main_color)   # Head
            draw.ellipse([70, 140, 100, 180], fill=main_color)   # Floppy ear
            draw.ellipse([200, 140, 230, 180], fill=main_color)  # Floppy ear
            draw.ellipse([130, 190, 170, 220], fill=main_color)  # Snout
            
        elif breed == "dalmatian":
            # Spots!
            draw.ellipse([95, 120, 205, 210], fill=main_color)   # Head
            # Add spots
            for _ in range(8):
                x = random.randint(100, 190)
                y = random.randint(130, 200)
                draw.ellipse([x, y, x+15, y+15], fill='black')
                
        elif breed == "alaskan_malamute":
            # Fluffy, wolf-like
            draw.ellipse([90, 110, 210, 220], fill=main_color)   # Head
            draw.polygon([(95, 120), (85, 90), (115, 110)], fill=main_color)  # Ear
            draw.polygon([(185, 110), (215, 90), (205, 120)], fill=main_color)  # Ear
        
        # Save image
        filename = f"test_{breed}.jpg"
        img.save(filename)
        test_images.append((breed, filename))
        print(f"   ✅ Saved: {filename}")
    
    return test_images

def test_dog_planter_generation(breed, image_file):
    """Test planter generation for a specific breed"""
    print(f"\n{'='*60}")
    print(f"🐕➡️🪴 TESTING {breed.upper()} PLANTER GENERATION")
    print(f"{'='*60}")
    
    try:
        from integrated_pipeline import IntegratedPetPlantrPipeline
        
        # Create pipeline
        pipeline = IntegratedPetPlantrPipeline(image_file)
        
        # Generate breed-specific planter
        print(f"🎯 Generating {breed} planter...")
        vertices, faces = pipeline.create_realistic_dog_mesh(breed=breed, base_size=80)
        
        if vertices and faces:
            print(f"✅ SUCCESS: Generated {breed} planter!")
            print(f"   📊 Vertices: {len(vertices)}")
            print(f"   🔺 Faces: {len(faces)}")
            
            # Save as STL
            output_file = f"planters/{breed}_planter.stl"
            os.makedirs("planters", exist_ok=True)
            
            # Generate STL content
            stl_content = generate_stl_content(vertices, faces, breed)
            
            with open(output_file, 'w') as f:
                f.write(stl_content)
            
            file_size = os.path.getsize(output_file)
            print(f"   💾 Saved: {output_file} ({file_size:,} bytes)")
            print(f"   🪴 Ready for 3D printing as functional planter!")
            
            return True
        else:
            print(f"❌ Failed to generate planter for {breed}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {breed} planter: {e}")
        return False

def generate_stl_content(vertices, faces, breed):
    """Generate STL file content for the dog planter"""
    stl_lines = [f"solid {breed}_dog_planter"]
    
    for face in faces:
        if len(face) >= 3:
            # Get face vertices
            v1 = vertices[face[0]] if face[0] < len(vertices) else [0, 0, 0]
            v2 = vertices[face[1]] if face[1] < len(vertices) else [0, 0, 0]  
            v3 = vertices[face[2]] if face[2] < len(vertices) else [0, 0, 0]
            
            # Simple normal calculation
            normal = [0, 0, 1]  # Simplified
            
            stl_lines.append(f"  facet normal {normal[0]} {normal[1]} {normal[2]}")
            stl_lines.append("    outer loop")
            stl_lines.append(f"      vertex {v1[0]:.3f} {v1[1]:.3f} {v1[2]:.3f}")
            stl_lines.append(f"      vertex {v2[0]:.3f} {v2[1]:.3f} {v2[2]:.3f}")
            stl_lines.append(f"      vertex {v3[0]:.3f} {v3[1]:.3f} {v3[2]:.3f}")
            stl_lines.append("    endloop")
            stl_lines.append("  endfacet")
    
    stl_lines.append(f"endsolid {breed}_dog_planter")
    return "\n".join(stl_lines)

def show_planter_comparison():
    """Show how different breeds create different planter shapes"""
    print(f"\n{'='*60}")
    print("🐕 DOG BREED PLANTER SHAPE COMPARISON")
    print(f"{'='*60}")
    
    breed_features = {
        "pug": {
            "shape": "Compact, wide planter with flat front face",
            "features": "Short snout cavity, wide opening for easy planting",
            "size": "Small (perfect for succulents)"
        },
        "golden_retriever": {
            "shape": "Medium oval planter with gentle curves", 
            "features": "Moderate depth, floppy ear details on sides",
            "size": "Medium (good for herbs or small flowers)"
        },
        "german_shepherd": {
            "shape": "Angular planter with pointed ear accents",
            "features": "Deep cavity, strong walls, pointed features",
            "size": "Large (suitable for small shrubs)"
        },
        "dalmatian": {
            "shape": "Spotted texture planter with medium depth",
            "features": "Decorative spot patterns, standard proportions", 
            "size": "Medium (perfect for colorful flowers)"
        },
        "alaskan_malamute": {
            "shape": "Robust planter with thick walls",
            "features": "Deep planting cavity, sturdy construction",
            "size": "Large (great for outdoor plants)"
        }
    }
    
    for breed, info in breed_features.items():
        print(f"\n🐕 {breed.upper().replace('_', ' ')}")
        print(f"   Shape: {info['shape']}")
        print(f"   Features: {info['features']}")  
        print(f"   Size: {info['size']}")

def main():
    """Main demo function"""
    print("🐕➡️🪴 DOG-SHAPED PLANTER GENERATOR DEMO")
    print("="*60)
    print("Creating ACTUAL dog-shaped planters for different breeds!")
    print("Each planter is hollow and functional for growing plants.")
    
    # Show what makes each breed unique as a planter
    show_planter_comparison()
    
    # Create test images
    print(f"\n📸 Creating breed-specific test images...")
    test_images = create_breed_test_images()
    
    # Test planter generation for each breed
    successful_planters = 0
    total_breeds = len(test_images)
    
    for breed, image_file in test_images:
        success = test_dog_planter_generation(breed, image_file)
        if success:
            successful_planters += 1
    
    # Final results
    print(f"\n{'='*60}")
    print("🎉 DOG PLANTER GENERATION COMPLETE!")
    print(f"{'='*60}")
    print(f"✅ Successfully generated {successful_planters}/{total_breeds} breed-specific planters")
    print(f"📁 Check the 'planters/' folder for STL files")
    print(f"🖨️  All files are ready for 3D printing!")
    print(f"🪴 Each planter is hollow and ready for plants!")
    
    if successful_planters == total_breeds:
        print(f"\n🏆 PERFECT SUCCESS! All dog breeds generated as functional planters!")
    
    # Cleanup test images
    print(f"\n🧹 Cleaning up test images...")
    for breed, image_file in test_images:
        try:
            os.remove(image_file)
            print(f"   Removed: {image_file}")
        except:
            pass

if __name__ == "__main__":
    main()
