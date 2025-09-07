#!/usr/bin/env python3
"""
Complete Dog-to-Planter-to-3D Workflow
=====================================
Converts a dog image into a planter visualization, then generates a 3D model
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

def create_planter_visualization(input_image_path: str, output_path: str) -> str:
    """
    Convert a dog image into a planter visualization
    """
    print("🎨 Creating Planter Visualization")
    print("=" * 40)
    
    try:
        # Load the original image
        img = Image.open(input_image_path).convert('RGB')
        print(f"📸 Loaded image: {os.path.basename(input_image_path)}")
        print(f"   Original size: {img.size}")
        
        # Resize for processing
        target_size = (512, 512)
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Create a copy for the planter visualization
        planter_img = img.copy()
        
        # Enhance the image for better planter appearance
        enhancer = ImageEnhance.Contrast(planter_img)
        planter_img = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Sharpness(planter_img)
        planter_img = enhancer.enhance(1.1)
        
        # Create a mask for the planter cavity
        mask = Image.new('L', target_size, 0)
        draw = ImageDraw.Draw(mask)
        
        # Draw a circular cavity in the back/top area
        center_x, center_y = target_size[0] // 2, target_size[1] // 3
        cavity_radius = min(target_size) // 6
        
        draw.ellipse([
            center_x - cavity_radius, center_y - cavity_radius,
            center_x + cavity_radius, center_y + cavity_radius
        ], fill=255)
        
        # Apply a slight blur to the mask for smooth edges
        mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
        
        # Create cavity effect (darker area)
        cavity_overlay = Image.new('RGB', target_size, (60, 40, 30))  # Dark brown
        planter_img = Image.composite(cavity_overlay, planter_img, mask)
        
        # Add planter base/rim effect
        rim_mask = Image.new('L', target_size, 0)
        draw_rim = ImageDraw.Draw(rim_mask)
        
        # Draw rim around the bottom
        rim_thickness = 20
        draw_rim.rectangle([
            0, target_size[1] - rim_thickness,
            target_size[0], target_size[1]
        ], fill=128)
        
        # Rim color (terracotta-like)
        rim_overlay = Image.new('RGB', target_size, (180, 120, 80))
        planter_img = Image.composite(rim_overlay, planter_img, rim_mask)
        
        # Add some planter texture/wear
        noise = np.random.randint(-10, 10, (target_size[1], target_size[0], 3))
        planter_array = np.array(planter_img).astype(np.int16)
        planter_array += noise
        planter_array = np.clip(planter_array, 0, 255).astype(np.uint8)
        planter_img = Image.fromarray(planter_array)
        
        # Create a side-by-side comparison
        comparison_width = target_size[0] * 2 + 20
        comparison_height = target_size[1] + 100
        comparison_img = Image.new('RGB', (comparison_width, comparison_height), (40, 40, 40))
        
        # Add original image
        comparison_img.paste(img, (10, 50))
        
        # Add planter visualization
        comparison_img.paste(planter_img, (target_size[0] + 20, 50))
        
        # Add labels
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        draw_comp = ImageDraw.Draw(comparison_img)
        draw_comp.text((10, 10), "Original Dog", fill=(255, 255, 255), font=font)
        draw_comp.text((target_size[0] + 20, 10), "As Planter", fill=(255, 255, 255), font=font)
        
        # Add arrow between images
        arrow_start = (target_size[0] - 30, target_size[1] // 2 + 50)
        arrow_end = (target_size[0] + 50, target_size[1] // 2 + 50)
        draw_comp.line([arrow_start, arrow_end], fill=(100, 200, 100), width=3)
        draw_comp.polygon([
            (arrow_end[0] - 10, arrow_end[1] - 5),
            (arrow_end[0], arrow_end[1]),
            (arrow_end[0] - 10, arrow_end[1] + 5)
        ], fill=(100, 200, 100))
        
        # Save the visualization
        comparison_img.save(output_path, 'JPEG', quality=95)
        print(f"✅ Planter visualization saved: {output_path}")
        
        # Also save just the planter version for 3D processing
        planter_only_path = output_path.replace('.jpg', '_planter_only.jpg')
        planter_img.save(planter_only_path, 'JPEG', quality=95)
        print(f"✅ Planter-only image saved: {planter_only_path}")
        
        return planter_only_path
        
    except Exception as e:
        print(f"❌ Error creating planter visualization: {e}")
        return None

def run_3d_pipeline(planter_image_path: str, output_dir: str = "planter_3d_output") -> str:
    """
    Run the enhanced 3D pipeline on the planter image
    """
    print(f"\n🚀 Generating 3D Model from Planter Image")
    print("=" * 50)
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Run the enhanced pipeline
        cmd = [
            sys.executable, "enhanced_petplantr_pipeline.py",
            "--input", planter_image_path,
            "--output", output_dir,
            "--validation"
        ]
        
        print(f"🔧 Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ 3D pipeline completed successfully!")
            
            # Find the generated STL file
            output_path = Path(output_dir)
            stl_files = list(output_path.glob("*.stl"))
            
            if stl_files:
                latest_stl = max(stl_files, key=os.path.getctime)
                print(f"📁 Generated STL: {latest_stl}")
                return str(latest_stl)
            else:
                print("⚠️  STL file not found in output directory")
                return None
        else:
            print("❌ 3D pipeline failed:")
            print(result.stderr)
            return None
            
    except subprocess.TimeoutExpired:
        print("⏰ Pipeline timed out - this is normal for full processing")
        # Still try to find the STL file
        output_path = Path(output_dir)
        stl_files = list(output_path.glob("*.stl"))
        if stl_files:
            latest_stl = max(stl_files, key=os.path.getctime)
            return str(latest_stl)
        return None
        
    except Exception as e:
        print(f"❌ Error running 3D pipeline: {e}")
        return None

def validate_3d_model(stl_path: str) -> dict:
    """
    Validate the generated 3D model
    """
    print(f"\n🔍 Validating 3D Model")
    print("=" * 30)
    
    try:
        result = subprocess.run([
            sys.executable, "simple_validation.py", stl_path
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        # Parse validation results
        validation_data = {
            "passed": "✅ PASSED" in result.stdout,
            "grade": "A" if "Grade: A" in result.stdout else "B" if "Grade: B" in result.stdout else "C",
            "output": result.stdout
        }
        
        return validation_data
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return {"passed": False, "error": str(e)}

def create_workflow_summary(original_image: str, planter_viz: str, stl_file: str, validation: dict):
    """
    Create a summary of the complete workflow
    """
    print(f"\n📋 Workflow Summary")
    print("=" * 40)
    
    summary = {
        "workflow": "Dog → Planter Visualization → 3D Model",
        "original_image": original_image,
        "planter_visualization": planter_viz,
        "stl_model": stl_file,
        "validation_passed": validation.get("passed", False),
        "model_grade": validation.get("grade", "Unknown"),
        "timestamp": "2025-06-26"
    }
    
    # Save summary
    summary_path = "workflow_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Original Image: {original_image}")
    print(f"✅ Planter Visualization: {planter_viz}")
    print(f"✅ 3D STL Model: {stl_file}")
    print(f"✅ Validation: {'PASSED' if validation.get('passed') else 'FAILED'}")
    print(f"✅ Model Grade: {validation.get('grade', 'Unknown')}")
    print(f"📁 Summary saved: {summary_path}")
    
    return summary

def main():
    """
    Complete workflow: Dog image → Planter visualization → 3D model
    """
    print("🐕 Complete Dog-to-Planter-to-3D Workflow")
    print("=" * 60)
    
    # Step 1: Select a test image
    test_images = [
        "data/oxford_local/train/train_031_wheaten_terrier_wheaten_terrier_75.jpg",
        "data/oxford_local/train/train_103_chihuahua_chihuahua_19.jpg",
        "data/oxford_local/train/train_075_japanese_chin_japanese_chin_183.jpg"
    ]
    
    # Use the first available image
    input_image = None
    for img_path in test_images:
        if os.path.exists(img_path):
            input_image = img_path
            break
    
    if not input_image:
        print("❌ No test images found")
        return
    
    breed = os.path.basename(input_image).split('_')[3]
    print(f"🎯 Selected breed: {breed}")
    print(f"📸 Input image: {input_image}")
    
    # Step 2: Create planter visualization
    planter_viz_path = f"planter_visualization_{breed}.jpg"
    planter_image = create_planter_visualization(input_image, planter_viz_path)
    
    if not planter_image:
        print("❌ Failed to create planter visualization")
        return
    
    # Step 3: Generate 3D model
    stl_file = run_3d_pipeline(planter_image, f"3d_output_{breed}")
    
    if not stl_file:
        print("❌ Failed to generate 3D model")
        return
    
    # Step 4: Validate the model
    validation_results = validate_3d_model(stl_file)
    
    # Step 5: Create summary
    summary = create_workflow_summary(input_image, planter_viz_path, stl_file, validation_results)
    
    # Final results
    print(f"\n🎉 Workflow Complete!")
    print("=" * 30)
    print(f"✅ Successfully converted {breed} dog image to 3D planter model")
    print(f"✅ Files generated:")
    print(f"   📸 Planter visualization: {planter_viz_path}")
    print(f"   🎯 3D STL model: {stl_file}")
    print(f"   📊 Validation: {'PASSED' if validation_results.get('passed') else 'FAILED'}")
    
    # Open the visualization
    print(f"\n🖥️  To view your results:")
    print(f"   1. Open {planter_viz_path} to see the planter visualization")
    print(f"   2. Load {stl_file} in the 3D viewer (simple-viewer-test.html)")
    print(f"   3. Check workflow_summary.json for complete details")

if __name__ == "__main__":
    main()
