#!/usr/bin/env python3
"""
Generate a sample STL file for demo purposes.
Creates a simple planter-like shape to demonstrate the 3D model pipeline.
"""

import math
import os

def write_stl_ascii(filename, vertices, faces):
    """Write STL file in ASCII format"""
    with open(filename, 'w') as f:
        f.write(f"solid {os.path.basename(filename)}\n")
        
        for face in faces:
            # Calculate normal vector
            v0 = vertices[face[0]]
            v1 = vertices[face[1]]
            v2 = vertices[face[2]]
            
            # Vector from v0 to v1
            u = [v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]]
            # Vector from v0 to v2
            v = [v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]]
            
            # Cross product u x v
            normal = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0]
            ]
            
            # Normalize
            length = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
            if length > 0:
                normal = [normal[0]/length, normal[1]/length, normal[2]/length]
            
            f.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
            f.write("    outer loop\n")
            for vertex_idx in face:
                v = vertices[vertex_idx]
                f.write(f"      vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        
        f.write(f"endsolid {os.path.basename(filename)}\n")

def create_planter_stl():
    """Create a simple planter STL model"""
    # Create a simple cylindrical planter with a hollow center
    radius_outer = 5.0
    radius_inner = 4.0
    height = 6.0
    segments = 12
    
    vertices = []
    faces = []
    
    # Generate vertices for outer and inner cylinders
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        
        # Outer cylinder vertices (bottom and top)
        x_outer = radius_outer * math.cos(angle)
        y_outer = radius_outer * math.sin(angle)
        vertices.append([x_outer, y_outer, 0.0])  # Bottom outer
        vertices.append([x_outer, y_outer, height])  # Top outer
        
        # Inner cylinder vertices (bottom and top)
        x_inner = radius_inner * math.cos(angle)
        y_inner = radius_inner * math.sin(angle)
        vertices.append([x_inner, y_inner, 0.5])  # Bottom inner (slightly raised)
        vertices.append([x_inner, y_inner, height])  # Top inner
    
    # Generate faces
    for i in range(segments):
        next_i = (i + 1) % segments
        
        # Outer wall faces
        v1 = i * 4  # Bottom outer current
        v2 = i * 4 + 1  # Top outer current
        v3 = next_i * 4  # Bottom outer next
        v4 = next_i * 4 + 1  # Top outer next
        
        faces.append([v1, v2, v3])
        faces.append([v2, v4, v3])
        
        # Inner wall faces
        v5 = i * 4 + 2  # Bottom inner current
        v6 = i * 4 + 3  # Top inner current
        v7 = next_i * 4 + 2  # Bottom inner next
        v8 = next_i * 4 + 3  # Top inner next
        
        faces.append([v5, v7, v6])
        faces.append([v6, v7, v8])
        
        # Bottom face (ring between outer and inner)
        faces.append([v1, v5, v3])
        faces.append([v3, v5, v7])
        
        # Top face (ring between outer and inner)
        faces.append([v2, v4, v6])
        faces.append([v4, v8, v6])
    
    return vertices, faces

def main():
    print("Generating sample STL file for PetPlantr demo...")
    
    # Create output directory
    output_dir = "/Users/medan/Downloads/PetPlantr/sample-stl"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate planter model
    vertices, faces = create_planter_stl()
    
    # Write STL file
    stl_path = os.path.join(output_dir, "pug_planter_demo.stl")
    write_stl_ascii(stl_path, vertices, faces)
    
    print(f"STL file generated: {stl_path}")
    print(f"Model stats: {len(vertices)} vertices, {len(faces)} faces")
    
    return stl_path

if __name__ == "__main__":
    main()
