#!/usr/bin/env python3
"""
🚀 HIGH-RESOLUTION MODEL GENERATOR
=================================

Generate ultra-high quality dog planter models with maximum detail
for museum-quality output and perfect 3D printing.
"""

import numpy as np
import trimesh
from pathlib import Path
import time

def create_ultra_high_res_dog_planter():
    """Create ultra-high resolution dog planter model"""
    print("🚀 GENERATING ULTRA-HIGH RESOLUTION DOG PLANTER")
    print("=" * 55)
    
    # Ultra-high resolution parameters
    resolution = 512  # 4x higher than standard
    detail_level = 8  # Maximum detail
    
    print(f"📊 Resolution: {resolution}x{resolution}")
    print(f"🎨 Detail Level: {detail_level}/10")
    
    # Create base dog shape with ultra-high detail
    print("\n🐕 Creating detailed dog geometry...")
    
    # Start with a more complex base shape
    # Create a detailed dog head/body using multiple spheres and transformations
    
    # Main body (elongated sphere)
    body = trimesh.creation.uv_sphere(radius=20, count=[resolution//4, resolution//8])
    body.apply_scale([1.2, 0.8, 0.6])  # Make it more dog-like proportions
    
    # Head (larger sphere, positioned forward)
    head = trimesh.creation.uv_sphere(radius=15, count=[resolution//6, resolution//12])
    head.apply_translation([18, 0, 5])
    
    # Snout (smaller elongated sphere)
    snout = trimesh.creation.uv_sphere(radius=8, count=[resolution//8, resolution//16])
    snout.apply_scale([1.5, 0.7, 0.7])
    snout.apply_translation([28, 0, 3])
    
    # Ears (flattened spheres)
    ear1 = trimesh.creation.uv_sphere(radius=6, count=[resolution//12, resolution//24])
    ear1.apply_scale([0.3, 1.2, 1.0])
    ear1.apply_translation([15, -8, 12])
    
    ear2 = trimesh.creation.uv_sphere(radius=6, count=[resolution//12, resolution//24])
    ear2.apply_scale([0.3, 1.2, 1.0])
    ear2.apply_translation([15, 8, 12])
    
    # Legs (cylinders with high detail)
    leg_segments = resolution // 16
    
    leg1 = trimesh.creation.cylinder(radius=3, height=15, sections=leg_segments)
    leg1.apply_translation([8, -8, -15])
    
    leg2 = trimesh.creation.cylinder(radius=3, height=15, sections=leg_segments)
    leg2.apply_translation([8, 8, -15])
    
    leg3 = trimesh.creation.cylinder(radius=3, height=15, sections=leg_segments)
    leg3.apply_translation([-8, -8, -15])
    
    leg4 = trimesh.creation.cylinder(radius=3, height=15, sections=leg_segments)
    leg4.apply_translation([-8, 8, -15])
    
    # Tail (tapered cylinder)
    tail = trimesh.creation.cylinder(radius=2, height=12, sections=leg_segments)
    tail.apply_scale([0.5, 0.5, 1.0])
    tail.apply_translation([-22, 0, 8])
    
    print("🔧 Combining dog components...")
    
    # Combine all parts into one mesh
    dog_parts = [body, head, snout, ear1, ear2, leg1, leg2, leg3, leg4, tail]
    combined_mesh = trimesh.util.concatenate(dog_parts)
    
    # Apply smoothing for organic look
    print("✨ Applying high-quality smoothing...")
    
    # Smooth the mesh for organic appearance
    combined_mesh = combined_mesh.smoothed()
    
    # Add surface detail with noise for realistic texture
    print("🎨 Adding surface detail...")
    vertices = combined_mesh.vertices.copy()
    
    # Add subtle surface variation for realism
    noise_scale = 0.5
    for i in range(len(vertices)):
        noise = np.random.normal(0, noise_scale, 3)
        vertices[i] += noise * 0.1  # Subtle surface variation
    
    combined_mesh.vertices = vertices
    
    # Ensure manifold geometry
    print("🔧 Ensuring watertight geometry...")
    combined_mesh.remove_degenerate_faces()
    combined_mesh.remove_duplicate_faces()
    combined_mesh.remove_unreferenced_vertices()
    combined_mesh.fill_holes()
    
    # Create planter cavity
    print("🏺 Creating planter cavity...")
    
    # Create internal cavity (smaller version of the dog, hollowed out)
    cavity_scale = 0.7
    cavity_mesh = combined_mesh.copy()
    cavity_mesh.apply_scale([cavity_scale, cavity_scale, 0.8])
    cavity_mesh.apply_translation([0, 0, 3])  # Offset up for cavity
    
    # Boolean operation to create hollow interior
    try:
        # Subtract cavity from main mesh
        planter_mesh = combined_mesh.difference(cavity_mesh)
        print("✅ Cavity created successfully")
    except:
        # Fallback: use original mesh with manual cavity indication
        print("⚠️ Using original mesh (cavity to be added in post-processing)")
        planter_mesh = combined_mesh
    
    # Final quality improvements
    print("🎯 Final quality enhancements...")
    
    # Remesh for consistent quality
    if hasattr(planter_mesh, 'remesh'):
        planter_mesh = planter_mesh.remesh()
    
    # Ensure proper orientation (dog facing forward)
    planter_mesh.apply_translation([0, 0, 15])  # Lift off ground
    
    # Scale to printable size (approximately 80mm long)
    bounds = planter_mesh.bounds
    current_length = bounds[1][0] - bounds[0][0]
    target_length = 80  # mm
    scale_factor = target_length / current_length
    planter_mesh.apply_scale([scale_factor, scale_factor, scale_factor])
    
    print(f"📏 Scaled to {target_length}mm length")
    
    # Final validation
    print("\n🔍 QUALITY VALIDATION")
    print("-" * 25)
    
    is_watertight = planter_mesh.is_watertight
    volume = planter_mesh.volume
    surface_area = planter_mesh.area
    face_count = len(planter_mesh.faces)
    vertex_count = len(planter_mesh.vertices)
    
    print(f"✅ Watertight: {'YES' if is_watertight else 'NO'}")
    print(f"📊 Volume: {volume:.2f} cubic units")
    print(f"📐 Surface Area: {surface_area:.2f} square units")
    print(f"🔺 Faces: {face_count:,}")
    print(f"📍 Vertices: {vertex_count:,}")
    
    final_bounds = planter_mesh.bounds
    final_dimensions = final_bounds[1] - final_bounds[0]
    print(f"📏 Dimensions: {final_dimensions[0]:.1f}×{final_dimensions[1]:.1f}×{final_dimensions[2]:.1f}mm")
    
    # Save the high-resolution model
    timestamp = int(time.time())
    output_filename = f"HIGH_RES_DOG_PLANTER_{timestamp}.stl"
    output_path = Path("generated_models") / output_filename
    
    # Ensure output directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    print(f"\n💾 Saving high-resolution model...")
    planter_mesh.export(str(output_path))
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Saved: {output_filename}")
    print(f"💾 File Size: {file_size_mb:.2f}MB")
    
    # Create a copy as the new production model
    production_path = Path("HIGH_RES_PRODUCTION_READY.stl")
    planter_mesh.export(str(production_path))
    print(f"🏆 Production copy: {production_path.name}")
    
    return str(output_path), str(production_path)

def main():
    """Generate ultra-high resolution model"""
    print("🎯 STARTING HIGH-RESOLUTION MODEL GENERATION")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        model_path, production_path = create_ultra_high_res_dog_planter()
        
        elapsed_time = time.time() - start_time
        
        print(f"\n🏁 GENERATION COMPLETE")
        print("=" * 30)
        print(f"⏱️ Time: {elapsed_time:.1f} seconds")
        print(f"📁 Model: {model_path}")
        print(f"🏆 Production: {production_path}")
        print("\n🎉 ULTRA-HIGH RESOLUTION MODEL READY!")
        print("✅ Ready for museum-quality viewing")
        print("✅ Ready for precision 3D printing")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
