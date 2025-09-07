#!/usr/bin/env python3
"""
STL Model Analyzer - Shows what's actually in the STL file
"""

import struct
import math

def analyze_stl(filename):
    """Analyze and visualize an STL file"""
    print(f"🔍 Analyzing STL File: {filename}")
    print("=" * 50)
    
    try:
        with open(filename, 'rb') as f:
            # Read header
            header = f.read(80)
            print(f"📋 Header: {header[:40].decode('ascii', errors='ignore').strip()}")
            
            # Read triangle count
            triangle_count = struct.unpack('<I', f.read(4))[0]
            print(f"🔺 Triangles: {triangle_count}")
            
            # Read some triangles to analyze
            vertices = []
            min_coords = [float('inf')] * 3
            max_coords = [float('-inf')] * 3
            
            for i in range(min(triangle_count, 100)):  # Analyze first 100 triangles
                # Skip normal (3 floats)
                f.read(12)
                
                # Read 3 vertices (9 floats total)
                for v in range(3):
                    vertex = struct.unpack('<fff', f.read(12))
                    vertices.append(vertex)
                    
                    for j in range(3):
                        min_coords[j] = min(min_coords[j], vertex[j])
                        max_coords[j] = max(max_coords[j], vertex[j])
                
                # Skip attribute bytes
                f.read(2)
            
            # Calculate dimensions
            size = [max_coords[i] - min_coords[i] for i in range(3)]
            
            print(f"📏 Dimensions: {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm")
            print(f"📐 Bounding box:")
            print(f"   X: {min_coords[0]:.1f} to {max_coords[0]:.1f}")
            print(f"   Y: {min_coords[1]:.1f} to {max_coords[1]:.1f}")
            print(f"   Z: {min_coords[2]:.1f} to {max_coords[2]:.1f}")
            
            # Simple shape analysis
            center_x = (min_coords[0] + max_coords[0]) / 2
            center_y = (min_coords[1] + max_coords[1]) / 2
            
            # Check if it's roughly circular (dog-like) or square
            width_height_ratio = size[0] / size[1] if size[1] > 0 else 1
            
            print(f"\n🎯 Shape Analysis:")
            print(f"   Width/Height ratio: {width_height_ratio:.2f}")
            
            if 0.8 <= width_height_ratio <= 1.2:
                print("   ✅ Shape: Roughly circular (dog-like)")
            else:
                print("   ⚠️  Shape: Rectangular/square-like")
                
            # Analyze vertex distribution
            radius_samples = []
            for vertex in vertices[:50]:  # Sample first 50 vertices
                dx = vertex[0] - center_x
                dy = vertex[1] - center_y
                radius = math.sqrt(dx*dx + dy*dy)
                radius_samples.append(radius)
            
            if radius_samples:
                avg_radius = sum(radius_samples) / len(radius_samples)
                radius_variation = max(radius_samples) - min(radius_samples)
                
                print(f"   Average radius: {avg_radius:.1f} mm")
                print(f"   Radius variation: {radius_variation:.1f} mm")
                
                if radius_variation > avg_radius * 0.3:
                    print("   ✅ Complex organic shape (dog features)")
                else:
                    print("   ⚠️  Simple geometric shape")
            
            return True
            
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return False

def create_ascii_visualization(filename):
    """Create a simple ASCII art visualization of the model"""
    print(f"\n🎨 ASCII Visualization")
    print("-" * 30)
    
    try:
        with open(filename, 'rb') as f:
            f.read(80)  # Skip header
            triangle_count = struct.unpack('<I', f.read(4))[0]
            
            # Collect vertices
            vertices = []
            for i in range(min(triangle_count, 200)):
                f.read(12)  # Skip normal
                for v in range(3):
                    vertex = struct.unpack('<fff', f.read(12))
                    vertices.append(vertex)
                f.read(2)  # Skip attributes
            
            if not vertices:
                print("No vertices found")
                return
            
            # Find bounds
            min_x = min(v[0] for v in vertices)
            max_x = max(v[0] for v in vertices)
            min_y = min(v[1] for v in vertices)
            max_y = max(v[1] for v in vertices)
            
            # Create ASCII grid
            width, height = 40, 20
            grid = [[' ' for _ in range(width)] for _ in range(height)]
            
            # Map vertices to grid
            for vertex in vertices[::3]:  # Sample every 3rd vertex
                if max_x > min_x and max_y > min_y:
                    x = int((vertex[0] - min_x) / (max_x - min_x) * (width - 1))
                    y = int((vertex[1] - min_y) / (max_y - min_y) * (height - 1))
                    if 0 <= x < width and 0 <= y < height:
                        grid[height-1-y][x] = '●'
            
            # Print grid
            print("   " + "─" * width)
            for row in grid:
                print("   │" + "".join(row) + "│")
            print("   " + "─" * width)
            print("   (Top-down view of the model)")
            
    except Exception as e:
        print(f"Error creating visualization: {e}")

def main():
    """Analyze the generated STL files"""
    stl_files = [
        "working_demo_output/working_pug_planter_1750980256.stl",
        "enhanced-production-models/ENH_1750972124240_enhanced_planter.stl"
    ]
    
    for i, stl_file in enumerate(stl_files):
        print(f"\n{'='*60}")
        print(f"MODEL {i+1}: {stl_file.split('/')[-1]}")
        print('='*60)
        
        success = analyze_stl(stl_file)
        if success:
            create_ascii_visualization(stl_file)
        
        print()

if __name__ == "__main__":
    main()
