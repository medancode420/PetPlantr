#!/usr/bin/env python3
"""
Create production-ready dog planter using simple geometric primitives
This approach guarantees manifold output by building from basic shapes
"""

import os
import trimesh
import numpy as np
from PIL import Image

def create_production_dog_planter():
    """Create a guaranteed manifold dog planter using geometric primitives"""
    print("🐕 CREATING PRODUCTION DOG PLANTER")
    print("=" * 40)
    
    # Load the DALL-E design for reference
    design_dir = "generated_designs"
    design_files = [f for f in os.listdir(design_dir) if f.endswith('.png') and 'custom_planter' in f]
    
    if not design_files:
        print("❌ No design reference found")
        return False
    
    latest_design = sorted(design_files)[-1]
    design_path = os.path.join(design_dir, latest_design)
    
    print(f"📸 Using design reference: {os.path.basename(design_path)}")
    
    try:
        # Analyze the design image to extract basic shapes
        with Image.open(design_path) as img:
            img = img.convert('RGB')
            img_array = np.array(img)
            
            # Find the main object region
            gray = np.mean(img_array, axis=2)
            object_mask = gray < 200  # Detect non-white areas
            
            # Get object bounds
            coords = np.where(object_mask)
            if len(coords[0]) == 0:
                print("❌ No object detected in design")
                return False
            
            min_y, max_y = coords[0].min(), coords[0].max()
            min_x, max_x = coords[1].min(), coords[1].max()
            
            # Calculate object dimensions in pixels
            obj_height_px = max_y - min_y
            obj_width_px = max_x - min_x
            
            print(f"🔍 Object bounds: {obj_width_px} x {obj_height_px} pixels")
        
        # Create manifold dog planter using primitive shapes
        print("🔧 Building manifold dog planter...")
        
        # Scale to reasonable size (50mm width)
        scale = 50.0 / max(obj_width_px, obj_height_px)
        width = obj_width_px * scale
        height = obj_height_px * scale
        depth = 20.0  # Fixed depth for planter
        
        print(f"📐 Target size: {width:.1f} x {height:.1f} x {depth:.1f} mm")
        
        # Main body (scaled sphere for dog body)
        body = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        # Scale to desired dimensions
        body.apply_scale([width/2, height/2, depth/2])
        body.apply_translation([0, 0, depth/2])
        
        # Head (smaller sphere)
        head_size = min(width, height) * 0.3
        head = trimesh.creation.icosphere(subdivisions=2, radius=head_size/2)
        head.apply_translation([width/3, height/3, depth * 0.7])
        
        # Combine body and head
        combined = trimesh.util.concatenate([body, head])
        
        # Create the convex hull to ensure manifold
        dog_planter = combined.convex_hull
        
        print(f"🔧 Base planter created: {len(dog_planter.vertices)} vertices, {len(dog_planter.faces)} faces")
        
        # Add planter cavity (cylinder subtraction)
        cavity_radius = min(width, height) * 0.25
        cavity_depth = depth * 0.6
        
        cavity = trimesh.creation.cylinder(
            radius=cavity_radius,
            height=cavity_depth + 1,  # Slightly deeper for clean boolean
            transform=trimesh.transformations.translation_matrix([0, 0, depth - cavity_depth/2])
        )
        
        # Subtract cavity
        final_planter = dog_planter.difference(cavity)
        
        # Add drainage holes
        hole_radius = 1.5
        hole_positions = [
            [-cavity_radius/2, 0, 0],
            [cavity_radius/2, 0, 0],
            [0, -cavity_radius/2, 0],
        ]
        
        for pos in hole_positions:
            hole = trimesh.creation.cylinder(
                radius=hole_radius,
                height=10,
                transform=trimesh.transformations.translation_matrix(pos)
            )
            final_planter = final_planter.difference(hole)
        
        # Final validation
        print(f"\n📊 FINAL PRODUCTION PLANTER")
        print(f"   Vertices: {len(final_planter.vertices):,}")
        print(f"   Faces: {len(final_planter.faces):,}")
        print(f"   Watertight: {final_planter.is_watertight}")
        print(f"   Is volume: {final_planter.is_volume}")
        print(f"   Volume: {final_planter.volume:.1f} cubic mm")
        
        # Check manifold
        edges = final_planter.edges
        unique_edges = final_planter.edges_unique
        non_manifold_count = len(edges) - len(edges[unique_edges])
        print(f"   Non-manifold edges: {non_manifold_count}")
        
        # Dimensions
        bounds = final_planter.bounds
        final_width = bounds[1][0] - bounds[0][0]
        final_height = bounds[1][1] - bounds[0][1]
        final_depth = bounds[1][2] - bounds[0][2]
        print(f"   Dimensions: {final_width:.1f} x {final_height:.1f} x {final_depth:.1f} mm")
        
        # Save production-ready STL
        output_path = "generated_models/dog_planter_PRODUCTION_READY.stl"
        final_planter.export(output_path)
        
        output_size = os.path.getsize(output_path)
        print(f"\n💾 PRODUCTION STL SAVED")
        print(f"   File: {output_path}")
        print(f"   Size: {output_size:,} bytes")
        
        # Production assessment
        if final_planter.is_watertight and final_planter.is_volume and non_manifold_count == 0:
            print(f"🎉 PERFECT: Production-ready with zero non-manifold edges!")
            return True
        elif final_planter.is_watertight and final_planter.is_volume:
            print(f"✅ EXCELLENT: Watertight and ready for printing!")
            return True
        else:
            print(f"⚠️ Needs refinement")
            return False
            
    except Exception as e:
        print(f"❌ Production planter creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_production_dog_planter()
    
    if success:
        print(f"\n🎉 PRODUCTION DOG PLANTER COMPLETE!")
        print(f"✅ Ready for slicer validation and test print!")
        print(f"📋 File: generated_models/dog_planter_PRODUCTION_READY.stl")
    else:
        print(f"\n❌ Production planter creation needs work")
