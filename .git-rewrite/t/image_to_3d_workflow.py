#!/usr/bin/env python3
"""
Dog Image to Planter to 3D Model Complete Workflow
=================================================
Converts a dog photo into a planter visualization and then into a 3D model
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import time

def create_planter_visualization(input_image_path: str, output_path: str = "planter_visualization.jpg"):
    """
    Create a planter visualization from a dog image
    """
    print("🎨 Creating Planter Visualization")
    print("=" * 40)
    
    try:
        # Load the original image
        img = Image.open(input_image_path)
        print(f"📸 Loaded image: {os.path.basename(input_image_path)}")
        print(f"   Size: {img.size[0]}x{img.size[1]} pixels")
        
        # Resize for consistent processing
        img = img.resize((512, 512), Image.Resampling.LANCZOS)
        
        # Create planter mockup
        planter_img = create_planter_mockup(img)
        
        # Save the result
        planter_img.save(output_path, quality=95)
        print(f"✅ Planter visualization saved: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error creating planter visualization: {e}")
        return None

def create_planter_mockup(dog_img):
    """
    Create a realistic planter mockup with the dog head
    """
    # Create a new canvas
    canvas_width = 800
    canvas_height = 600
    canvas = Image.new('RGB', (canvas_width, canvas_height), (245, 245, 245))
    
    # Create planter base (cylinder shape)
    planter_base = Image.new('RGBA', (400, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(planter_base)
    
    # Draw planter body (terracotta color)
    planter_color = (210, 140, 110)  # Terracotta
    rim_color = (180, 110, 80)       # Darker rim
    
    # Main cylinder
    draw.ellipse([50, 250, 350, 300], fill=planter_color, outline=rim_color, width=3)
    draw.rectangle([50, 150, 350, 275], fill=planter_color)
    draw.ellipse([50, 100, 350, 150], fill=planter_color, outline=rim_color, width=3)
    
    # Add drainage hole
    draw.ellipse([180, 270, 220, 285], fill=(80, 50, 30))
    
    # Resize dog image to fit as planter "face"
    dog_resized = dog_img.resize((250, 200), Image.Resampling.LANCZOS)
    
    # Create mask for rounded effect
    mask = Image.new('L', (250, 200), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([10, 10, 240, 190], fill=255)
    
    # Paste dog onto planter base
    planter_base.paste(dog_resized, (75, 120), mask)
    
    # Paste planter onto canvas
    canvas.paste(planter_base, (200, 150), planter_base)
    
    # Add title
    try:
        draw_canvas = ImageDraw.Draw(canvas)
        draw_canvas.text((canvas_width//2 - 100, 50), "🐕 Custom Pet Planter", 
                        fill=(100, 100, 100), anchor="mm")
        draw_canvas.text((canvas_width//2 - 80, 500), "Ready for 3D Printing!", 
                        fill=(100, 100, 100), anchor="mm")
    except:
        pass  # Skip text if font issues
    
    return canvas

def run_enhanced_pipeline_for_image(image_path: str):
    """
    Run the enhanced pipeline on a specific image
    """
    print(f"\n🚀 Running Enhanced Pipeline on: {os.path.basename(image_path)}")
    print("=" * 60)
    
    # Create unique output directory
    timestamp = str(int(time.time()))
    output_dir = f"demo_conversion_{timestamp}"
    
    cmd = [
        sys.executable, "enhanced_petplantr_pipeline.py",
        "--input", image_path,
        "--output", output_dir,
        "--validation"
    ]
    
    try:
        print("⏳ Processing... (this may take 10-30 seconds)")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Enhanced pipeline completed successfully!")
            
            # Find generated STL file
            output_path = Path(f"enhanced-production-models")
            stl_files = list(output_path.glob(f"*{timestamp}*.stl"))
            
            if stl_files:
                stl_file = stl_files[0]
                print(f"📁 Generated STL: {stl_file}")
                return str(stl_file)
            else:
                print("⚠️  STL file not found in expected location")
                return None
        else:
            print("❌ Pipeline failed:")
            print(result.stderr)
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ Pipeline processing took longer than expected")
        # Check if file was still generated
        output_path = Path(f"enhanced-production-models")
        stl_files = list(output_path.glob(f"*{timestamp}*.stl"))
        if stl_files:
            return str(stl_files[0])
        return None
        
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return None

def main():
    """
    Complete workflow: Dog image → Planter visualization → 3D model
    """
    print("🎬 Dog Image to 3D Planter Complete Workflow")
    print("=" * 70)
    
    # Available test images
    test_images = [
        "data/oxford_local/train/train_031_wheaten_terrier_wheaten_terrier_75.jpg",
        "data/oxford_local/train/train_075_japanese_chin_japanese_chin_183.jpg", 
        "data/oxford_local/train/train_103_chihuahua_chihuahua_19.jpg"
    ]
    
    # Select first available image
    selected_image = None
    for img_path in test_images:
        if os.path.exists(img_path):
            selected_image = img_path
            break
    
    if not selected_image:
        print("❌ No test images found!")
        return
    
    print(f"📸 Selected image: {os.path.basename(selected_image)}")
    breed = os.path.basename(selected_image).split('_')[2]
    print(f"🐕 Detected breed: {breed.replace('_', ' ').title()}")
    
    # Step 1: Create planter visualization
    planter_viz = create_planter_visualization(selected_image, f"{breed}_planter_concept.jpg")
    
    if planter_viz:
        print(f"✅ Planter concept created: {planter_viz}")
    
    # Step 2: Generate 3D model using enhanced pipeline
    stl_path = run_enhanced_pipeline_for_image(selected_image)
    
    if stl_path:
        print(f"✅ 3D model generated: {os.path.basename(stl_path)}")
        
        # Final summary
        print(f"\n🎯 Workflow Results:")
        print(f"   Original Image: ✅ {os.path.basename(selected_image)}")
        print(f"   Planter Concept: {'✅ Created' if planter_viz else '❌ Failed'}")
        print(f"   3D Model: ✅ {os.path.basename(stl_path)}")
        
        print(f"\n🎉 COMPLETE SUCCESS!")
        print(f"🚀 Your {breed.replace('_', ' ')} planter is ready for 3D printing!")
        print(f"📁 Files created:")
        print(f"   • {planter_viz} (concept visualization)")
        print(f"   • {stl_path} (3D printable model)")
    
    else:
        print("❌ 3D model generation failed")

if __name__ == "__main__":
    main()
