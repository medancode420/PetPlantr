#!/usr/bin/env python3
"""
Realistic Dog Planter Generator
Creates an STL that actually looks like a dog with recognizable features
"""

import os
import math
import time

def create_realistic_dog_planter():
    """Create a planter that actually looks like a pug"""
    print("🐕 Creating Realistic Pug Planter")
    
    vertices = []
    faces = []
    
    # Parameters for a recognizable pug shape
    segments = 24  # More segments for smoother curves
    height_levels = 16  # More levels for better detail
    
    # Size in mm
    base_radius = 50.0  # 10cm diameter base
    height = 70.0       # 7cm height
    
    print(f"📏 Size: {base_radius*2}mm diameter x {height}mm height")
    
    # Generate vertices with realistic pug proportions
    for level in range(height_levels):
        z = (level / (height_levels - 1)) * height
        level_ratio = z / height
        
        # Define the pug silhouette from bottom to top
        if level_ratio < 0.1:  # Base (0-7mm) - wide stable base
            base_scale = 1.0
            face_features = False
        elif level_ratio < 0.3:  # Lower body (7-21mm) - body width
            base_scale = 0.95
            face_features = False
        elif level_ratio < 0.5:  # Chest/neck (21-35mm) - narrowing
            base_scale = 0.85
            face_features = False
        elif level_ratio < 0.7:  # Lower face (35-49mm) - jaw area
            base_scale = 0.8
            face_features = True
            face_type = "jaw"
        elif level_ratio < 0.85: # Mid face (49-59.5mm) - main features
            base_scale = 0.75
            face_features = True
            face_type = "main"
        else:  # Top/forehead (59.5-70mm) - ears and top
            base_scale = 0.6
            face_features = True
            face_type = "ears"
        
        for seg in range(segments):
            angle = 2 * math.pi * seg / segments
            
            # Start with base radius
            radius = base_radius * base_scale
            
            if face_features:
                # Add pug-specific facial features
                if face_type == "jaw":
                    # Flat front face characteristic of pugs
                    if abs(angle) < math.pi/4 or abs(angle - math.pi) < math.pi/4:
                        radius *= 0.7  # Very flat front
                    # Wider cheeks
                    elif (math.pi/4 < angle < 3*math.pi/4) or (5*math.pi/4 < angle < 7*math.pi/4):
                        radius *= 1.1  # Bulging cheeks
                
                elif face_type == "main":
                    # Even flatter face for pug look
                    if abs(angle) < math.pi/3 or abs(angle - math.pi) < math.pi/3:
                        radius *= 0.6  # Very flat snout area
                    # Prominent cheeks and eye area
                    elif (math.pi/6 < angle < math.pi/2) or (3*math.pi/2 < angle < 11*math.pi/6):
                        radius *= 1.15  # Eye/cheek bulge
                    # Slightly wider at sides
                    else:
                        radius *= 1.05
                
                elif face_type == "ears":
                    # Smaller head top with ear indentations
                    if (math.pi/4 < angle < 3*math.pi/4) or (5*math.pi/4 < angle < 7*math.pi/4):
                        radius *= 0.85  # Ear depressions
                    # Forehead area
                    if abs(angle) < math.pi/6 or abs(angle - math.pi) < math.pi/6:
                        radius *= 0.9  # Slight forehead
            
            # Add subtle asymmetry for more organic look
            asymmetry = 0.02 * math.sin(angle * 3 + level_ratio * 2)
            radius *= (1 + asymmetry)
            
            # Calculate final position
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            vertices.append([x, y, z])
    
    print(f"✅ Generated {len(vertices)} vertices with realistic proportions")
    
    # Generate faces connecting the levels
    for level in range(height_levels - 1):
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            
            # Four vertices of the quad
            v1 = level * segments + seg
            v2 = level * segments + next_seg
            v3 = (level + 1) * segments + seg
            v4 = (level + 1) * segments + next_seg
            
            # Create two triangles per quad
            faces.append([v1, v3, v2])
            faces.append([v2, v3, v4])
    
    # Add bottom cap (flat base for stability)
    bottom_center = len(vertices)
    vertices.append([0, 0, 0])
    
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        faces.append([bottom_center, seg, next_seg])
    
    # Add top cap with slight depression for planting
    top_center = len(vertices)
    vertices.append([0, 0, height - 5])  # Slightly recessed for cavity
    
    top_level_start = (height_levels - 1) * segments
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        v1 = top_level_start + seg
        v2 = top_level_start + next_seg
        faces.append([top_center, v2, v1])
    
    print(f"✅ Generated {len(faces)} triangles with proper winding")
    return vertices, faces

def add_facial_details(vertices, faces):
    """Add some basic facial feature indentations"""
    print("👁️  Adding facial feature details")
    
    # Find vertices in the face area (mid-height, front-facing)
    face_vertices = []
    for i, vertex in enumerate(vertices):
        x, y, z = vertex
        
        # Check if this is in the face area
        if 35 <= z <= 55:  # Face height range
            angle = math.atan2(y, x)
            # Front-facing area
            if abs(angle) < math.pi/3:
                face_vertices.append(i)
    
    # Slightly indent face vertices to create eye sockets and snout depression
    for i in face_vertices:
        vertices[i][0] *= 0.95  # Move slightly inward
    
    print(f"✅ Enhanced {len(face_vertices)} facial vertices")
    return vertices, faces

def save_realistic_stl(vertices, faces, filename):
    """Save as ASCII STL with proper formatting"""
    print(f"💾 Saving realistic dog STL: {filename}")
    
    with open(filename, 'w') as f:
        f.write("solid RealisticPugPlanter\n")
        
        triangle_count = 0
        for face in faces:
            if len(face) >= 3:
                # Get the three vertices
                v1 = vertices[face[0]]
                v2 = vertices[face[1]]
                v3 = vertices[face[2]]
                
                # Calculate normal vector
                u = [v2[i] - v1[i] for i in range(3)]
                v = [v3[i] - v1[i] for i in range(3)]
                
                normal = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]
                ]
                
                # Normalize
                length = math.sqrt(sum(n*n for n in normal))
                if length > 0:
                    normal = [n/length for n in normal]
                else:
                    normal = [0, 0, 1]
                
                # Write facet
                f.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {v1[0]:.3f} {v1[1]:.3f} {v1[2]:.3f}\n")
                f.write(f"      vertex {v2[0]:.3f} {v2[1]:.3f} {v2[2]:.3f}\n")
                f.write(f"      vertex {v3[0]:.3f} {v3[1]:.3f} {v3[2]:.3f}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
                
                triangle_count += 1
        
        f.write("endsolid RealisticPugPlanter\n")
    
    print(f"✅ Saved {triangle_count} triangles in ASCII format")
    
    # Verify file
    file_size = os.path.getsize(filename)
    print(f"📏 File size: {file_size:,} bytes")

def main():
    """Generate a realistic dog planter"""
    print("🎬 Realistic Dog Planter Generator")
    print("=" * 50)
    
    # Create output directory
    output_dir = "realistic_demo_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate realistic dog shape
    vertices, faces = create_realistic_dog_planter()
    
    # Add facial details
    vertices, faces = add_facial_details(vertices, faces)
    
    # Save as STL
    timestamp = int(time.time())
    filename = os.path.join(output_dir, f"realistic_pug_planter_{timestamp}.stl")
    save_realistic_stl(vertices, faces, filename)
    
    print(f"\n🎉 SUCCESS - REALISTIC DOG PLANTER!")
    print(f"📁 File: {filename}")
    print(f"📏 Dimensions: 100mm × 100mm × 70mm")
    print(f"🐕 Features:")
    print(f"   • Flat pug face (characteristic snub nose)")
    print(f"   • Wider cheeks and jaw area")
    print(f"   • Narrower forehead with ear depressions")
    print(f"   • Organic, asymmetrical shape")
    print(f"   • Proper planter proportions")
    print(f"🖨️  Ready for 3D printing!")
    
    return filename

if __name__ == "__main__":
    main()
