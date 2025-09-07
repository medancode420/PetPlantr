#!/usr/bin/env python3
"""
Advanced Planter Shape Optimizer
Enhanced optimization techniques specifically for improving planter characteristics
"""
import os
import sys
import numpy as np
import trimesh
from pathlib import Path
from enhanced_stl_analyzer import analyze_planter_characteristics

class AdvancedPlanterOptimizer:
    def __init__(self):
        """Initialize advanced optimizer with specialized techniques"""
        self.optimization_techniques = {
            'opening_ratio': 'Improve top opening size relative to base',
            'shape_stability': 'Smooth shape transitions between cross-sections',
            'taper_improvement': 'Create gradual tapering from bottom to top',
            'volume_hollowing': 'Create internal cavity for planting',
            'base_stabilization': 'Widen and flatten base for stability',
            'wall_thickening': 'Ensure adequate wall thickness for printing'
        }
        
        print("🔧 Advanced Planter Optimizer initialized")

    def optimize_for_planter_characteristics(self, mesh, target_confidence=0.8, max_attempts=3):
        """
        Systematically optimize a mesh to improve planter characteristics
        
        Args:
            mesh: Input trimesh object
            target_confidence: Target planter confidence score (0-1)
            max_attempts: Maximum optimization attempts
        
        Returns:
            optimized_mesh: Improved mesh
            improvements: List of improvements made
        """
        print(f"🎯 Optimizing mesh for planter characteristics (target: {target_confidence:.1%})")
        
        current_mesh = mesh.copy()
        improvements_made = []
        
        for attempt in range(max_attempts):
            print(f"\n🔄 Optimization attempt {attempt + 1}/{max_attempts}")
            
            # Save temporary mesh for analysis
            temp_path = f"/tmp/temp_optimization_{attempt}.stl"
            current_mesh.export(temp_path)
            
            # Analyze current characteristics
            current_analysis = analyze_planter_characteristics(temp_path)
            current_confidence = current_analysis.get('planter_confidence', 0) / 100.0
            
            print(f"   Current confidence: {current_confidence:.3f}")
            
            if current_confidence >= target_confidence:
                print(f"✅ Target confidence achieved!")
                break
            
            # Identify primary issues and apply targeted optimizations
            optimization_applied = False
            
            # 1. Fix opening ratio (most critical for planters)
            opening_ratio = current_analysis.get('opening_ratio', 0)
            if opening_ratio < 1.0:
                print(f"   🔧 Improving opening ratio: {opening_ratio:.3f} -> target: 1.2+")
                current_mesh = self._improve_opening_ratio(current_mesh, target_ratio=1.3)
                improvements_made.append(f"Improved opening ratio from {opening_ratio:.3f}")
                optimization_applied = True
            
            # 2. Fix shape stability
            stability = current_analysis.get('shape_stability', 0)
            if stability < 0.5:
                print(f"   🔧 Improving shape stability: {stability:.3f} -> target: 0.7+")
                current_mesh = self._improve_shape_stability(current_mesh)
                improvements_made.append(f"Improved shape stability from {stability:.3f}")
                optimization_applied = True
            
            # 3. Fix taper ratio
            taper_ratio = current_analysis.get('taper_ratio', 0)
            if taper_ratio < 0.3:
                print(f"   🔧 Improving taper ratio: {taper_ratio:.3f} -> target: 0.5+")
                current_mesh = self._improve_taper_ratio(current_mesh, target_taper=0.6)
                improvements_made.append(f"Improved taper ratio from {taper_ratio:.3f}")
                optimization_applied = True
            
            # 4. Add planter cavity if missing
            if not self._has_adequate_cavity(current_mesh):
                print(f"   🔧 Adding planter cavity")
                current_mesh = self._add_planter_cavity(current_mesh)
                improvements_made.append("Added planter cavity")
                optimization_applied = True
            
            # 5. Improve base stability
            if attempt == max_attempts - 1:  # Last attempt, ensure base is stable
                print(f"   🔧 Final base stabilization")
                current_mesh = self._stabilize_base(current_mesh)
                improvements_made.append("Stabilized base")
                optimization_applied = True
            
            if not optimization_applied:
                print(f"   ⚠️ No optimizations needed for attempt {attempt + 1}")
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        return current_mesh, improvements_made

    def _improve_opening_ratio(self, mesh, target_ratio=1.3):
        """Improve the opening ratio by widening the top and/or narrowing the bottom"""
        try:
            vertices = mesh.vertices.copy()
            bounds = mesh.bounds
            height = bounds[1][2] - bounds[0][2]
            
            # Define top and bottom regions
            bottom_height = bounds[0][2] + height * 0.2  # Bottom 20%
            top_height = bounds[1][2] - height * 0.2      # Top 20%
            
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            center_y = (bounds[0][1] + bounds[1][1]) / 2
            
            # Widen top region
            top_mask = vertices[:, 2] >= top_height
            for i in np.where(top_mask)[0]:
                # Distance from center
                dx = vertices[i][0] - center_x
                dy = vertices[i][1] - center_y
                
                # Scale outward by target ratio
                scale_factor = target_ratio
                vertices[i][0] = center_x + dx * scale_factor
                vertices[i][1] = center_y + dy * scale_factor
            
            # Slightly narrow bottom region (but not too much)
            bottom_mask = vertices[:, 2] <= bottom_height
            for i in np.where(bottom_mask)[0]:
                dx = vertices[i][0] - center_x
                dy = vertices[i][1] - center_y
                
                # Slight inward scaling
                scale_factor = 0.95
                vertices[i][0] = center_x + dx * scale_factor
                vertices[i][1] = center_y + dy * scale_factor
            
            return trimesh.Trimesh(vertices=vertices, faces=mesh.faces, validate=False)
            
        except Exception as e:
            print(f"   ❌ Opening ratio improvement failed: {e}")
            return mesh

    def _improve_shape_stability(self, mesh):
        """Smooth the shape transitions to improve stability"""
        try:
            # Apply Laplacian smoothing to reduce erratic transitions
            vertices = mesh.vertices.copy()
            
            # Simple smoothing: average each vertex with its neighbors
            # This is a simplified approach - in practice, proper Laplacian smoothing
            # would use the mesh connectivity
            
            # Apply Gaussian smoothing to each coordinate
            from scipy.ndimage import gaussian_filter1d
            
            # Sort vertices by height for consistent smoothing
            height_order = np.argsort(vertices[:, 2])
            sorted_vertices = vertices[height_order]
            
            # Smooth x and y coordinates based on height progression
            sorted_vertices[:, 0] = gaussian_filter1d(sorted_vertices[:, 0], sigma=2)
            sorted_vertices[:, 1] = gaussian_filter1d(sorted_vertices[:, 1], sigma=2)
            
            # Restore original order
            vertices[height_order] = sorted_vertices
            
            smoothed_mesh = trimesh.Trimesh(vertices=vertices, faces=mesh.faces, validate=False)
            
            # Apply trimesh's built-in smoothing as well
            try:
                smoothed_mesh = smoothed_mesh.smoothed()
            except:
                pass  # Fallback to our manual smoothing
            
            return smoothed_mesh
            
        except Exception as e:
            print(f"   ❌ Shape stability improvement failed: {e}")
            return mesh

    def _improve_taper_ratio(self, mesh, target_taper=0.6):
        """Improve taper by creating gradual narrowing from bottom to top"""
        try:
            vertices = mesh.vertices.copy()
            bounds = mesh.bounds
            height = bounds[1][2] - bounds[0][2]
            
            center_x = (bounds[0][0] + bounds[1][0]) / 2
            center_y = (bounds[0][1] + bounds[1][1]) / 2
            
            # Apply graduated scaling based on height
            for i, vertex in enumerate(vertices):
                # Height ratio (0 = bottom, 1 = top)
                height_ratio = (vertex[2] - bounds[0][2]) / height
                
                # Taper factor: 1.0 at bottom, target_taper at top
                taper_factor = 1.0 - (1.0 - target_taper) * height_ratio
                
                # Apply scaling
                dx = vertex[0] - center_x
                dy = vertex[1] - center_y
                
                vertices[i][0] = center_x + dx * taper_factor
                vertices[i][1] = center_y + dy * taper_factor
            
            return trimesh.Trimesh(vertices=vertices, faces=mesh.faces, validate=False)
            
        except Exception as e:
            print(f"   ❌ Taper ratio improvement failed: {e}")
            return mesh

    def _has_adequate_cavity(self, mesh):
        """Check if mesh has an adequate internal cavity"""
        try:
            # Simple check: if mesh is watertight and has reasonable volume distribution
            if not mesh.is_watertight:
                return False
            
            # Check volume to surface area ratio
            volume = mesh.volume
            surface_area = mesh.area
            
            # A hollow object should have a lower volume/surface ratio
            ratio = volume / surface_area if surface_area > 0 else 0
            
            # If ratio is too high, likely solid
            return ratio < 5.0  # This is a rough heuristic
            
        except:
            return False

    def _add_planter_cavity(self, mesh):
        """Add a planting cavity to the mesh"""
        try:
            if not mesh.is_watertight:
                mesh.fill_holes()
            
            bounds = mesh.bounds
            width = bounds[1][0] - bounds[0][0]
            depth = bounds[1][1] - bounds[0][1]
            height = bounds[1][2] - bounds[0][2]
            
            # Cavity parameters
            cavity_radius = min(width, depth) * 0.35  # 35% of smallest horizontal dimension
            cavity_height = height * 0.7  # 70% of total height
            
            # Position cavity at the top-center
            cavity_center = [
                (bounds[0][0] + bounds[1][0]) / 2,
                (bounds[0][1] + bounds[1][1]) / 2,
                bounds[1][2] - cavity_height / 2
            ]
            
            # Create cylindrical cavity
            cavity = trimesh.creation.cylinder(
                radius=cavity_radius,
                height=cavity_height,
                transform=trimesh.transformations.translation_matrix(cavity_center)
            )
            
            # Subtract cavity from mesh
            result = mesh.difference(cavity)
            
            # If difference operation fails, return original
            if result and result.volume > 0:
                return result
            else:
                return mesh
                
        except Exception as e:
            print(f"   ❌ Cavity addition failed: {e}")
            return mesh

    def _stabilize_base(self, mesh):
        """Stabilize the base by flattening and slightly widening it"""
        try:
            vertices = mesh.vertices.copy()
            bounds = mesh.bounds
            
            # Define base region (bottom 15%)
            base_height = bounds[0][2] + (bounds[1][2] - bounds[0][2]) * 0.15
            base_mask = vertices[:, 2] <= base_height
            
            if np.any(base_mask):
                # Flatten base vertices to the same level
                base_z = bounds[0][2]
                vertices[base_mask, 2] = base_z
                
                # Slightly widen base for stability
                center_x = (bounds[0][0] + bounds[1][0]) / 2
                center_y = (bounds[0][1] + bounds[1][1]) / 2
                
                for i in np.where(base_mask)[0]:
                    dx = vertices[i][0] - center_x
                    dy = vertices[i][1] - center_y
                    
                    # Widen by 5%
                    vertices[i][0] = center_x + dx * 1.05
                    vertices[i][1] = center_y + dy * 1.05
            
            return trimesh.Trimesh(vertices=vertices, faces=mesh.faces, validate=False)
            
        except Exception as e:
            print(f"   ❌ Base stabilization failed: {e}")
            return mesh

def test_advanced_optimizer():
    """Test the advanced optimizer on an existing model"""
    print("🧪 Testing Advanced Planter Optimizer")
    
    # Find a generated model to test
    test_files = list(Path("demo_single_planter").glob("*_FINAL.stl"))
    if not test_files:
        print("❌ No test files found")
        return
    
    test_file = test_files[0]
    print(f"📁 Testing with: {test_file}")
    
    # Load mesh
    mesh = trimesh.load(str(test_file))
    
    # Initialize optimizer
    optimizer = AdvancedPlanterOptimizer()
    
    # Optimize mesh
    optimized_mesh, improvements = optimizer.optimize_for_planter_characteristics(
        mesh, target_confidence=0.8, max_attempts=3
    )
    
    # Save optimized result
    output_path = test_file.parent / f"{test_file.stem}_OPTIMIZED.stl"
    optimized_mesh.export(str(output_path))
    
    print(f"💾 Optimized model saved: {output_path}")
    print(f"🔧 Improvements made:")
    for improvement in improvements:
        print(f"   • {improvement}")
    
    return str(output_path)

if __name__ == "__main__":
    # Test the optimizer
    result_path = test_advanced_optimizer()
    
    if result_path:
        print(f"\n📊 Analyzing optimized result...")
        from enhanced_stl_analyzer import analyze_stl_quality
        quality_report, _ = analyze_stl_quality(result_path)
        
        planter_analysis = quality_report["planter_analysis"]
        confidence = planter_analysis["planter_confidence"]
        is_planter = planter_analysis["is_planter_like"]
        
        print(f"✅ Final Results:")
        print(f"   Planter confidence: {confidence:.1f}%")
        print(f"   Planter-like: {is_planter}")
        print(f"   Opening ratio: {planter_analysis['opening_ratio']:.3f}")
        print(f"   Shape stability: {planter_analysis['shape_stability']:.3f}")
        print(f"   Taper ratio: {planter_analysis['taper_ratio']:.3f}")
        
        if confidence >= 80:
            print("🎉 Optimization successful!")
        else:
            print("⚠️ Further optimization needed")
