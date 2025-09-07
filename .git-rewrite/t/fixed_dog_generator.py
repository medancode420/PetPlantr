#!/usr/bin/env python3
"""
Fixed PetPlantr Model Generator
Creates a proper, visible dog-shaped planter STL file
"""

import os
import math
import struct
import time

def create_proper_dog_planter():
    """Create a proper dog planter with correct STL format"""
    print("🐕 Creating Proper Dog Planter")
    
    vertices = []
    faces = []
    
    # Parameters
    segments = 20  # Number of circular segments
    height_levels = 10  # Number of height levels
    
    # Size in mm (STL standard)
    base_radius = 60.0  # 6cm radius = 12cm diameter
    height = 80.0       # 8cm height
    
    print(f"📏 Size: {base_radius*2}mm diameter x {height}mm height")
    
    # Generate vertices layer by layer
    for level in range(height_levels):
        z = (level / (height_levels - 1)) * height
        level_ratio = z / height
        
        # Pug-specific radius modification for each level
        if level_ratio < 0.3:  # Base - wide and stable
            level_radius_factor = 1.0
        elif level_ratio < 0.6:  # Middle - pug face features
            level_radius_factor = 0.9  # Slightly narrower
        else:  # Top - ears and forehead
            level_radius_factor = 0.7  # Much narrower
        
        for seg in range(segments):
            angle = 2 * math.pi * seg / segments
            
            # Pug face shaping
            radius_mod = level_radius_factor
            
            # Add pug-specific features based on angle
            if level_ratio > 0.3:  # Only for face area
                # Flat face (front and back flattened)
                if abs(angle) < math.pi/3 or abs(angle - math.pi) < math.pi/3:
                    radius_mod *= 0.8  # Flatten front/back
                
                # Wider cheeks (sides bulged)
                elif (math.pi/3 < angle < 2*math.pi/3) or (4*math.pi/3 < angle < 5*math.pi/3):
                    radius_mod *= 1.1  # Bulge sides
            
            # Calculate position
            final_radius = base_radius * radius_mod
            x = final_radius * math.cos(angle)
            y = final_radius * math.sin(angle)
            
            vertices.append([x, y, z])
    
    print(f"✅ Generated {len(vertices)} vertices")
    
    # Generate faces connecting the levels
    for level in range(height_levels - 1):
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            
            # Four vertices of the quad
            v1 = level * segments + seg
            v2 = level * segments + next_seg
            v3 = (level + 1) * segments + seg
            v4 = (level + 1) * segments + next_seg
            
            # Create two triangles per quad (proper winding)
            faces.append([v1, v3, v2])
            faces.append([v2, v3, v4])
    
    # Add bottom cap
    bottom_center = len(vertices)
    vertices.append([0, 0, 0])
    
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        faces.append([bottom_center, seg, next_seg])
    
    # Add top cap
    top_center = len(vertices)
    vertices.append([0, 0, height])
    
    top_level_start = (height_levels - 1) * segments
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        v1 = top_level_start + seg
        v2 = top_level_start + next_seg
        faces.append([top_center, v2, v1])
    
    print(f"✅ Generated {len(faces)} triangles")
    return vertices, faces

def save_proper_stl(vertices, faces, filename):
    """Save as properly formatted binary STL"""
    print(f"💾 Saving proper STL: {filename}")
    
    with open(filename, 'wb') as f:
        # 80-byte header
        header = b'PetPlantr Pug Planter - Working Version' + b'\x00' * 40
        f.write(header)
        
        # Number of triangles (4 bytes, little endian)
        triangle_count = len(faces)
        f.write(struct.pack('<I', triangle_count))
        print(f"📊 Writing {triangle_count} triangles")
        
        # Write each triangle
        triangles_written = 0
        for face in faces:
            if len(face) >= 3:
                # Get the three vertices
                v1 = vertices[face[0]]
                v2 = vertices[face[1]]
                v3 = vertices[face[2]]
                
                # Calculate normal vector (cross product)
                u = [v2[i] - v1[i] for i in range(3)]
                v = [v3[i] - v1[i] for i in range(3)]
                
                normal = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]
                ]
                
                # Normalize the normal vector
                length = math.sqrt(sum(n*n for n in normal))
                if length > 0:
                    normal = [n/length for n in normal]
                else:
                    normal = [0, 0, 1]
                
                # Write normal vector (3 x 4 bytes = 12 bytes)
                f.write(struct.pack('<fff', normal[0], normal[1], normal[2]))
                
                # Write the three vertices (3 x 3 x 4 bytes = 36 bytes)
                f.write(struct.pack('<fff', v1[0], v1[1], v1[2]))
                f.write(struct.pack('<fff', v2[0], v2[1], v2[2]))
                f.write(struct.pack('<fff', v3[0], v3[1], v3[2]))
                
                # Attribute byte count (2 bytes, always 0)
                f.write(struct.pack('<H', 0))
                
                triangles_written += 1
        
        print(f"✅ Successfully wrote {triangles_written} triangles")
    
    # Verify file size
    file_size = os.path.getsize(filename)
    expected_size = 80 + 4 + (triangle_count * 50)  # header + count + triangles
    print(f"📏 File size: {file_size} bytes (expected: {expected_size})")
    
    if file_size == expected_size:
        print("✅ File size correct!")
    else:
        print("⚠️  File size mismatch - may have issues")

def main():
    """Generate the working dog planter"""
    print("🎬 Fixed PetPlantr Generator")
    print("=" * 40)
    
    # Create output directory
    output_dir = "working_demo_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate the model
    vertices, faces = create_proper_dog_planter()
    
    # Save as STL
    timestamp = int(time.time())
    filename = os.path.join(output_dir, f"working_pug_planter_{timestamp}.stl")
    save_proper_stl(vertices, faces, filename)
    
    print(f"\n🎉 SUCCESS!")
    print(f"📁 File: {filename}")
    print(f"📏 Dimensions: 120mm × 120mm × 80mm")
    print(f"🐕 Shape: Pug-inspired with flat face")
    print(f"🖨️  Ready for 3D printing!")
    
    return filename

if __name__ == "__main__":
    main()
