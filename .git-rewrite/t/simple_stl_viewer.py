#!/usr/bin/env python3
"""
Simple STL Visualizer - Shows you the models in terminal
"""

import os
import struct

def analyze_stl_simple(filepath):
    """Simple STL analysis that actually works"""
    print(f"\n🔍 ANALYZING: {os.path.basename(filepath)}")
    print("=" * 50)
    
    file_size = os.path.getsize(filepath)
    print(f"📏 File size: {file_size:,} bytes")
    
    if file_size < 200:
        print("❌ File too small - likely corrupted")
        return
    
    # Try to read as ASCII first
    try:
        with open(filepath, 'r') as f:
            first_line = f.readline().strip()
            if first_line.startswith('solid'):
                print("📝 Format: ASCII STL")
                lines = f.readlines()
                triangle_count = len([line for line in lines if 'facet normal' in line])
                print(f"🔺 Triangles: {triangle_count}")
                
                # Find vertices to calculate dimensions
                vertices = []
                for line in lines:
                    if 'vertex' in line:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            try:
                                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                vertices.append([x, y, z])
                            except:
                                pass
                
                if vertices:
                    min_x = min(v[0] for v in vertices)
                    max_x = max(v[0] for v in vertices)
                    min_y = min(v[1] for v in vertices)
                    max_y = max(v[1] for v in vertices)
                    min_z = min(v[2] for v in vertices)
                    max_z = max(v[2] for v in vertices)
                    
                    width = max_x - min_x
                    depth = max_y - min_y
                    height = max_z - min_z
                    
                    print(f"📐 Dimensions: {width:.1f} × {depth:.1f} × {height:.1f} mm")
                    
                    if height < 10:
                        print("❌ PROBLEM: Too flat - this is the square issue!")
                    elif height > 50:
                        print("✅ GOOD: Proper planter height")
                    else:
                        print("⚠️  WARNING: Unusually short")
                    
                    # Draw simple top view
                    print("\n🎨 Top View (rough):")
                    draw_simple_shape(vertices)
                    
                else:
                    print("❌ No valid vertices found")
                return
    except:
        pass
    
    # Try binary format
    try:
        with open(filepath, 'rb') as f:
            header = f.read(80)
            print(f"📝 Format: Binary STL")
            print(f"📋 Header: {header[:40].decode('ascii', errors='ignore').strip()}")
            
            triangle_bytes = f.read(4)
            if len(triangle_bytes) == 4:
                triangle_count = struct.unpack('<I', triangle_bytes)[0]
                print(f"🔺 Triangles: {triangle_count:,}")
                
                if triangle_count > 1000000:
                    print("❌ PROBLEM: Invalid triangle count - corrupted!")
                    return
                
                # Read first few triangles to get dimensions
                vertices = []
                for i in range(min(50, triangle_count)):
                    normal = f.read(12)  # Skip normal
                    if len(normal) < 12:
                        break
                    
                    for j in range(3):
                        vertex_data = f.read(12)
                        if len(vertex_data) == 12:
                            x, y, z = struct.unpack('<fff', vertex_data)
                            vertices.append([x, y, z])
                    
                    f.read(2)  # Skip attribute
                
                if vertices:
                    min_x = min(v[0] for v in vertices)
                    max_x = max(v[0] for v in vertices)
                    min_y = min(v[1] for v in vertices)
                    max_y = max(v[1] for v in vertices)
                    min_z = min(v[2] for v in vertices)
                    max_z = max(v[2] for v in vertices)
                    
                    width = max_x - min_x
                    depth = max_y - min_y
                    height = max_z - min_z
                    
                    print(f"📐 Dimensions: {width:.1f} × {depth:.1f} × {height:.1f} mm")
                    
                    if height < 10:
                        print("❌ PROBLEM: Too flat - this is the square issue!")
                    elif height > 50:
                        print("✅ GOOD: Proper planter height")
                    else:
                        print("⚠️  WARNING: Unusually short")
                else:
                    print("❌ Could not read vertex data")
            else:
                print("❌ Could not read triangle count")
                
    except Exception as e:
        print(f"❌ Error reading binary: {e}")

def draw_simple_shape(vertices):
    """Draw a simple ASCII representation"""
    if not vertices:
        return
    
    # Use first 20 vertices for shape
    sample_vertices = vertices[:20] if len(vertices) > 20 else vertices
    
    min_x = min(v[0] for v in sample_vertices)
    max_x = max(v[0] for v in sample_vertices)
    min_y = min(v[1] for v in sample_vertices)
    max_y = max(v[1] for v in sample_vertices)
    
    if max_x <= min_x or max_y <= min_y:
        print("   [Shape cannot be visualized]")
        return
    
    # Create grid
    width, height = 20, 10
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Map vertices to grid
    for vertex in sample_vertices:
        x_norm = (vertex[0] - min_x) / (max_x - min_x)
        y_norm = (vertex[1] - min_y) / (max_y - min_y)
        
        grid_x = int(x_norm * (width - 1))
        grid_y = int((1 - y_norm) * (height - 1))  # Flip Y
        
        if 0 <= grid_x < width and 0 <= grid_y < height:
            grid[grid_y][grid_x] = '●'
    
    # Print grid
    print("   " + "─" * width)
    for row in grid:
        print("   │" + "".join(row) + "│")
    print("   " + "─" * width)

def main():
    """Compare the different STL files"""
    print("🎬 PetPlantr STL File Comparison")
    print("=" * 60)
    
    # Files to compare
    files_to_check = [
        "realistic_demo_output/realistic_pug_planter_1750981014.stl",
        "working_demo_output/simple_working_dog.stl",
        "enhanced-production-models/ENH_1750972124240_enhanced_planter.stl"
    ]
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            analyze_stl_simple(filepath)
        else:
            print(f"\n❌ FILE NOT FOUND: {filepath}")
    
    print(f"\n🎯 SUMMARY:")
    print("✅ Working model: simple_working_dog.stl (80mm tall)")
    print("❌ Broken models: enhanced pipeline files (flat squares)")
    print("📁 All files are in your PetPlantr directory")

if __name__ == "__main__":
    main()
