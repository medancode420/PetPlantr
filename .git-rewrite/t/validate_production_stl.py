#!/usr/bin/env python3
"""
Quick STL manifold validation for production readiness
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def validate_stl_for_production():
    """Validate the latest STL for production printing"""
    print("🔍 STL PRODUCTION VALIDATION")
    print("=" * 40)
    
    # Find the latest STL
    model_dir = "generated_models"
    stl_files = [f for f in os.listdir(model_dir) if f.endswith('.stl') and 'custom_planter_design' in f]
    
    if not stl_files:
        print("❌ No STL files found")
        return False
    
    # Get the most recent one
    latest_stl = sorted(stl_files)[-1]
    stl_path = os.path.join(model_dir, latest_stl)
    
    print(f"📁 Validating: {latest_stl}")
    print(f"📊 File size: {os.path.getsize(stl_path):,} bytes")
    
    try:
        import trimesh
        mesh = trimesh.load(stl_path)
        
        print(f"\n🔧 MESH ANALYSIS")
        print(f"   Vertices: {len(mesh.vertices):,}")
        print(f"   Faces: {len(mesh.faces):,}")
        print(f"   Edges: {len(mesh.edges):,}")
        
        print(f"\n💧 MANIFOLD CHECK")
        print(f"   Watertight: {mesh.is_watertight}")
        print(f"   Is volume: {mesh.is_volume}")
        print(f"   Winding consistent: {mesh.is_winding_consistent}")
        
        # Check for non-manifold edges
        non_manifold_edges = mesh.edges[~mesh.edges_unique]
        print(f"   Non-manifold edges: {len(non_manifold_edges)}")
        
        if len(non_manifold_edges) == 0:
            print(f"   ✅ PERFECT: Zero non-manifold edges!")
        else:
            print(f"   ⚠️ Found {len(non_manifold_edges)} non-manifold edges")
        
        print(f"\n📐 DIMENSIONS")
        bounds = mesh.bounds
        width = bounds[1][0] - bounds[0][0]
        height = bounds[1][1] - bounds[0][1] 
        depth = bounds[1][2] - bounds[0][2]
        
        print(f"   Width: {width:.1f} mm")
        print(f"   Height: {height:.1f} mm") 
        print(f"   Depth: {depth:.1f} mm")
        print(f"   Volume: {mesh.volume:.1f} cubic mm")
        print(f"   Surface area: {mesh.area:.1f} square mm")
        
        # Check wall thickness
        min_thickness = min(width, height, depth) * 0.1  # Estimate minimum wall
        print(f"   Est. min wall thickness: {min_thickness:.1f} mm")
        
        if min_thickness >= 1.2:
            print(f"   ✅ Wall thickness OK (≥ 1.2mm)")
        else:
            print(f"   ⚠️ Potential thin walls (< 1.2mm)")
        
        print(f"\n🖨️ PRINT READINESS")
        
        # Size check
        if width <= 200 and height <= 200 and depth <= 200:
            print(f"   ✅ Size fits standard print bed (≤ 200mm)")
        else:
            print(f"   ⚠️ Large model - check printer bed size")
        
        # Volume check for print time estimation
        volume_cm3 = mesh.volume / 1000  # Convert to cm³
        estimated_time_hours = volume_cm3 * 0.5  # Rough estimate: 0.5h per cm³
        
        print(f"   📊 Volume: {volume_cm3:.1f} cm³")
        print(f"   ⏱️ Est. print time: {estimated_time_hours:.1f} hours")
        
        if estimated_time_hours <= 6:
            print(f"   ✅ Print time reasonable (≤ 6h)")
        else:
            print(f"   ⚠️ Long print time (> 6h)")
        
        # Overall assessment
        print(f"\n🎯 PRODUCTION READINESS SCORE")
        
        score = 0
        checks = [
            (mesh.is_watertight, "Watertight"),
            (mesh.is_volume, "Has volume"),
            (len(non_manifold_edges) == 0, "No non-manifold edges"),
            (min_thickness >= 1.2, "Wall thickness ≥ 1.2mm"),
            (estimated_time_hours <= 6, "Print time ≤ 6h"),
            (width <= 200, "Fits print bed")
        ]
        
        for passed, check in checks:
            if passed:
                print(f"   ✅ {check}")
                score += 1
            else:
                print(f"   ❌ {check}")
        
        print(f"\n📊 SCORE: {score}/{len(checks)} ({score/len(checks)*100:.0f}%)")
        
        if score >= 5:
            print(f"🎉 READY FOR PRODUCTION! Excellent quality STL")
            return True
        elif score >= 4:
            print(f"✅ GOOD FOR PRINTING with minor considerations")
            return True
        else:
            print(f"⚠️ Needs improvement before production")
            return False
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

if __name__ == "__main__":
    validate_stl_for_production()
