#!/usr/bin/env python3
"""
Terrain Guard-Rail Validator
============================
Automatically detects and rejects terrain-style depth maps
that would produce flat/blocky meshes instead of dog planters.
"""

import numpy as np
from PIL import Image
import cv2

class TerrainGuardRail:
    """Validates depth maps and concept images to prevent terrain artifacts"""
    
    @staticmethod
    def validate_depth_map(depth_path: str, threshold: float = 0.6) -> dict:
        """
        Validate depth map to detect terrain-style flat patterns
        
        Args:
            depth_path: Path to depth map image
            threshold: Ratio of flat pixels that triggers rejection
            
        Returns:
            dict with validation results
        """
        try:
            # Load depth image
            depth_img = np.array(Image.open(depth_path).convert('L'))
            
            # Calculate flat ratio (pixels in first 3 gray levels)
            flat_pixels = (depth_img < 20).sum()
            total_pixels = depth_img.size
            flat_ratio = flat_pixels / total_pixels
            
            # Calculate depth variation
            depth_std = np.std(depth_img)
            depth_range = np.max(depth_img) - np.min(depth_img)
            
            # Calculate gradient magnitude (edges)
            grad_x = cv2.Sobel(depth_img, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(depth_img, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            avg_gradient = np.mean(gradient_magnitude)
            
            # Terrain detection criteria
            is_terrain = (
                flat_ratio > threshold or           # Too many flat pixels
                depth_std < 10 or                  # Too little depth variation
                depth_range < 30 or                # Too small depth range
                avg_gradient < 5                   # Too few edges
            )
            
            results = {
                'is_valid': not is_terrain,
                'is_terrain': is_terrain,
                'flat_ratio': flat_ratio,
                'depth_std': depth_std,
                'depth_range': depth_range,
                'avg_gradient': avg_gradient,
                'threshold_used': threshold,
                'analysis': 'PASS' if not is_terrain else 'FAIL - TERRAIN DETECTED'
            }
            
            return results
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e),
                'analysis': 'ERROR - Could not analyze depth map'
            }
    
    @staticmethod
    def validate_concept_image(image_path: str) -> dict:
        """
        Analyze concept image to detect terrain-style patterns
        """
        try:
            # Load image
            img = np.array(Image.open(image_path))
            
            # Convert to grayscale for analysis
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            else:
                gray = img
            
            # Calculate image statistics
            brightness_mean = np.mean(gray)
            brightness_std = np.std(gray)
            
            # Edge detection to find structure
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Look for regular patterns (terrain tiles)
            # Calculate horizontal and vertical gradients
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # Check for dominant horizontal/vertical patterns (terrain grid)
            horizontal_energy = np.mean(np.abs(grad_x))
            vertical_energy = np.mean(np.abs(grad_y))
            
            # Terrain typically has grid-like patterns
            pattern_regularity = abs(horizontal_energy - vertical_energy) / max(horizontal_energy, vertical_energy, 1)
            
            # Simple heuristics for terrain detection
            is_terrain_like = (
                brightness_std < 30 or              # Too uniform
                edge_density < 0.01 or              # Too few edges
                pattern_regularity > 0.8            # Too regular/grid-like
            )
            
            results = {
                'is_valid': not is_terrain_like,
                'is_terrain_like': is_terrain_like,
                'brightness_mean': brightness_mean,
                'brightness_std': brightness_std,
                'edge_density': edge_density,
                'pattern_regularity': pattern_regularity,
                'analysis': 'PASS' if not is_terrain_like else 'FAIL - TERRAIN-LIKE PATTERN'
            }
            
            return results
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e),
                'analysis': 'ERROR - Could not analyze concept image'
            }
    
    @staticmethod
    def print_validation_report(depth_results: dict, concept_results: dict = None):
        """Print comprehensive validation report"""
        print("\n🔍 TERRAIN GUARD-RAIL VALIDATION REPORT")
        print("=" * 50)
        
        print(f"📊 DEPTH MAP ANALYSIS:")
        print(f"   Status: {depth_results['analysis']}")
        print(f"   Flat Ratio: {depth_results.get('flat_ratio', 0):.3f}")
        print(f"   Depth Std: {depth_results.get('depth_std', 0):.1f}")
        print(f"   Depth Range: {depth_results.get('depth_range', 0):.1f}")
        print(f"   Avg Gradient: {depth_results.get('avg_gradient', 0):.2f}")
        
        if concept_results:
            print(f"\n🎨 CONCEPT IMAGE ANALYSIS:")
            print(f"   Status: {concept_results['analysis']}")
            print(f"   Brightness Std: {concept_results.get('brightness_std', 0):.1f}")
            print(f"   Edge Density: {concept_results.get('edge_density', 0):.4f}")
            print(f"   Pattern Regularity: {concept_results.get('pattern_regularity', 0):.3f}")
        
        overall_valid = depth_results['is_valid'] and (not concept_results or concept_results['is_valid'])
        print(f"\n🏁 OVERALL STATUS: {'✅ PASS' if overall_valid else '❌ FAIL'}")
        
        if not overall_valid:
            print("⚠️  RECOMMENDED ACTION: Regenerate with anti-terrain prompts")

# Quick test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python terrain_guard_rail.py <depth_image_path> [concept_image_path]")
        sys.exit(1)
    
    guard_rail = TerrainGuardRail()
    
    depth_path = sys.argv[1]
    concept_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🔍 Validating: {depth_path}")
    if concept_path:
        print(f"🔍 Concept: {concept_path}")
    
    depth_results = guard_rail.validate_depth_map(depth_path)
    concept_results = guard_rail.validate_concept_image(concept_path) if concept_path else None
    
    guard_rail.print_validation_report(depth_results, concept_results)
