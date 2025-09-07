#!/usr/bin/env python3
"""
Aggressive STL repair using voxel reconstruction
This should fix the non-manifold issues completely
"""

import os
import trimesh
import numpy as np

def aggressive_voxel_repair():
    """Aggressive voxel-based repair for production STL"""
    print("🔧 AGGRESSIVE VOXEL REPAIR")
    print("=" * 40)
    
    # Find latest STL
    model_dir = "generated_models"
    stl_files = [f for f in os.listdir(model_dir) 
                 if f.endswith('.stl') and 'custom_planter_design' in f and 'PRODUCTION' not in f]
    
    if not stl_files:
        print("❌ No source STL files found")
        return False
    
    latest_stl = sorted(stl_files)[-1]
    input_path = os.path.join(model_dir, latest_stl)
    
    try:
        # Load original mesh
        mesh = trimesh.load(input_path)
        print(f"📁 Source: {os.path.basename(input_path)}")
        print(f"📊 Original: {len(mesh.vertices):,} vertices, {len(mesh.faces):,} faces")
        print(f"🌊 Volume: {mesh.volume:.1f} cubic mm")
        
        # Get dimensions for voxel sizing
        bounds = mesh.bounds
        max_dim = np.max(bounds[1] - bounds[0])
        
        # Use smaller voxel size for better detail preservation
        voxel_pitch = max_dim / 100  # 100 voxels across the largest dimension
        print(f"🧊 Using voxel pitch: {voxel_pitch:.2f} mm")
        
        # Create voxel grid
        print("🔄 Creating voxel grid...")
        voxel_grid = mesh.voxelized(pitch=voxel_pitch)
        
        # Generate mesh from voxels using marching cubes
        print("🔄 Generating mesh from voxels...")
        repaired_mesh = voxel_grid.marching_cubes
        
        # Check results
        print(f"\n📊 VOXEL REPAIR RESULTS")
        print(f"   Vertices: {len(repaired_mesh.vertices):,}")
        print(f"   Faces: {len(repaired_mesh.faces):,}")
        print(f"   Watertight: {repaired_mesh.is_watertight}")
        print(f"   Is volume: {repaired_mesh.is_volume}")
        print(f"   Volume: {repaired_mesh.volume:.1f} cubic mm")
        
        # Check non-manifold edges
        edges = repaired_mesh.edges
        unique_edges = repaired_mesh.edges_unique
        non_manifold_count = len(edges) - len(edges[unique_edges])
        print(f"   Non-manifold edges: {non_manifold_count}")
        
        # Dimensions
        bounds = repaired_mesh.bounds
        width = bounds[1][0] - bounds[0][0]
        height = bounds[1][1] - bounds[0][1]
        depth = bounds[1][2] - bounds[0][2]
        print(f"   Dimensions: {width:.1f} x {height:.1f} x {depth:.1f} mm")
        
        if repaired_mesh.is_watertight and repaired_mesh.is_volume:
            print("✅ Voxel repair successful!")
            
            # Save the repaired mesh
            output_path = os.path.join(model_dir, "dog_planter_VOXEL_REPAIRED.stl")
            repaired_mesh.export(output_path)
            
            print(f"\n💾 SAVED REPAIRED MESH")
            print(f"   File: {output_path}")
            print(f"   Size: {os.path.getsize(output_path):,} bytes")
            
            if non_manifold_count == 0:
                print("🎉 PERFECT: Zero non-manifold edges!")
                return True
            else:
                print("✅ GOOD: Watertight but with some non-manifold edges")
                return True
        else:
            print("❌ Voxel repair failed to create watertight mesh")
            return False
            
    except Exception as e:
        print(f"❌ Aggressive repair failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = aggressive_voxel_repair()
    
    if success:
        print(f"\n🎉 AGGRESSIVE REPAIR COMPLETE!")
        print(f"✅ Dog planter is now ready for slicer testing!")
        print(f"📋 Next: Load in PrusaSlicer/Bambu Studio and check repair results")
    else:
        print(f"\n❌ Still need to address mesh topology issues")
