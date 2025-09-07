#!/usr/bin/env python3
"""
Realistic Dog Planter Generator - Creates actual dog-shaped planters
"""

import math
import os
from datetime import datetime

def create_realistic_dog_mesh(breed="pug", base_size=100):
    """Create a mesh that actually looks like a dog"""
    vertices = []
    faces = []
    
    # Breed-specific parameters
    breed_params = {
        "pug": {
            "snout_length": 0.3,
            "snout_width": 0.8,
            "head_width": 1.0,
            "ear_size": 0.6,
            "eye_prominence": 0.8,
            "face_flatness": 0.9
        },
        "golden_retriever": {
            "snout_length": 0.7,
            "snout_width": 0.6,
            "head_width": 0.9,
            "ear_size": 0.8,
            "eye_prominence": 0.6,
            "face_flatness": 0.6
        },
        "german_shepherd": {
            "snout_length": 0.8,
            "snout_width": 0.5,
            "head_width": 0.8,
            "ear_size": 1.0,
            "eye_prominence": 0.5,
            "face_flatness": 0.4
        },
        "chihuahua": {
            "snout_length": 0.4,
            "snout_width": 0.7,
            "head_width": 1.1,
            "ear_size": 1.2,
            "eye_prominence": 0.9,
            "face_flatness": 0.8
        }
    }
    
    params = breed_params.get(breed, breed_params["pug"])
    
    print(f"🐕 Generating realistic {breed} planter...")
    print(f"   Snout length: {params['snout_length']:.1f}")
    print(f"   Head width: {params['head_width']:.1f}")
    print(f"   Ear size: {params['ear_size']:.1f}")
    
    # Base dimensions
    head_radius = base_size * 0.4
    body_radius = base_size * 0.45
    height = base_size * 0.8
    
    # Create the main body/planter bowl
    segments = 24
    height_levels = 20
    
    for level in range(height_levels + 1):
        z = (level / height_levels) * height
        level_ratio = z / height
        
        # Different sections of the dog
        if level_ratio < 0.1:
            # Base/paws
            current_radius = body_radius * 1.0
            section = "base"
        elif level_ratio < 0.3:
            # Lower body/chest
            current_radius = body_radius * 0.95
            section = "body"
        elif level_ratio < 0.5:
            # Upper body/neck
            current_radius = body_radius * 0.8
            section = "neck"
        elif level_ratio < 0.7:
            # Head/face area
            current_radius = head_radius * params['head_width']
            section = "head"
        else:
            # Top of head/ears
            current_radius = head_radius * 0.6
            section = "top"
        
        level_vertices = []
        
        for seg in range(segments):
            angle = 2 * math.pi * seg / segments
            
            # Base position
            x = current_radius * math.cos(angle)
            y = current_radius * math.sin(angle)
            
            # Add dog-specific features
            if section == "head":
                # Create snout area
                if -math.pi/6 < angle < math.pi/6:  # Front face
                    # Extend snout forward
                    snout_extension = params['snout_length'] * head_radius * (1 - level_ratio * 2)
                    if snout_extension > 0:
                        y += snout_extension
                    # Flatten face for flat-faced breeds
                    face_factor = 1 - params['face_flatness'] * 0.3
                    x *= face_factor
                
                # Eye areas (slight bulges)
                elif (math.pi/4 < angle < math.pi/2) or (-math.pi/2 < angle < -math.pi/4):
                    eye_bulge = params['eye_prominence'] * head_radius * 0.1
                    distance_from_center = math.sqrt(x*x + y*y)
                    if distance_from_center > 0:
                        x += (x / distance_from_center) * eye_bulge
                        y += (y / distance_from_center) * eye_bulge
                
                # Cheek areas
                elif (math.pi/2 < angle < 3*math.pi/4) or (-3*math.pi/4 < angle < -math.pi/2):
                    cheek_width = 1.1
                    x *= cheek_width
            
            elif section == "top":
                # Ear areas
                if (math.pi/3 < angle < 2*math.pi/3) or (-2*math.pi/3 < angle < -math.pi/3):
                    ear_extension = params['ear_size'] * head_radius * 0.3
                    distance_from_center = math.sqrt(x*x + y*y)
                    if distance_from_center > 0:
                        x += (x / distance_from_center) * ear_extension
                        y += (y / distance_from_center) * ear_extension
            
            # Add some planter-specific features (interior hollow)
            if level_ratio > 0.15:  # Don't hollow out the very bottom
                if section in ["head", "top"]:
                    # Create planting cavity in head area
                    cavity_factor = 0.7
                    x *= cavity_factor
                    y *= cavity_factor
            
            level_vertices.append([x, y, z])
        
        vertices.extend(level_vertices)
    
    # Create faces between levels
    for level in range(height_levels):
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            
            # Current level vertices
            v1 = level * segments + seg
            v2 = level * segments + next_seg
            
            # Next level vertices
            v3 = (level + 1) * segments + seg
            v4 = (level + 1) * segments + next_seg
            
            # Create two triangular faces
            faces.append([v1, v2, v3])
            faces.append([v2, v4, v3])
    
    # Add bottom cap
    bottom_center = len(vertices)
    vertices.append([0, 0, 0])  # Center point
    
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        faces.append([bottom_center, next_seg, seg])
    
    # Add more detailed features
    vertices, faces = add_dog_details(vertices, faces, params, head_radius, height)
    
    print(f"✅ Generated {len(vertices)} vertices, {len(faces)} faces")
    return vertices, faces

def add_dog_details(vertices, faces, params, head_radius, height):
    """Add specific dog features like snout detail, eye sockets, etc."""
    
    # Add snout tip detail
    snout_z = height * 0.6  # Middle of head area
    snout_y = head_radius * params['snout_length']
    snout_tip = len(vertices)
    
    # Create a small snout tip
    vertices.append([0, snout_y, snout_z])
    
    # Add nose area (small triangular detail)
    nose_width = head_radius * 0.1
    vertices.append([-nose_width, snout_y * 0.9, snout_z + head_radius * 0.05])
    vertices.append([nose_width, snout_y * 0.9, snout_z + head_radius * 0.05])
    vertices.append([0, snout_y * 0.8, snout_z + head_radius * 0.1])
    
    # Connect nose triangles
    faces.append([snout_tip, snout_tip + 1, snout_tip + 2])
    faces.append([snout_tip, snout_tip + 2, snout_tip + 3])
    faces.append([snout_tip, snout_tip + 3, snout_tip + 1])
    
    # Add ear details if it's a breed with prominent ears
    if params['ear_size'] > 0.8:
        ear_z = height * 0.75
        ear_radius = head_radius * 0.3
        
        # Left ear
        left_ear_base = len(vertices)
        vertices.append([-head_radius * 0.6, head_radius * 0.2, ear_z])
        vertices.append([-head_radius * 0.8, head_radius * 0.4, ear_z + head_radius * 0.2])
        vertices.append([-head_radius * 0.7, head_radius * 0.1, ear_z + head_radius * 0.3])
        
        # Right ear
        right_ear_base = len(vertices)
        vertices.append([head_radius * 0.6, head_radius * 0.2, ear_z])
        vertices.append([head_radius * 0.8, head_radius * 0.4, ear_z + head_radius * 0.2])
        vertices.append([head_radius * 0.7, head_radius * 0.1, ear_z + head_radius * 0.3])
        
        # Ear triangles
        faces.append([left_ear_base, left_ear_base + 1, left_ear_base + 2])
        faces.append([right_ear_base, right_ear_base + 1, right_ear_base + 2])
    
    return vertices, faces

def save_realistic_stl(vertices, faces, breed, filename=None):
    """Save the realistic dog mesh as STL"""
    if not filename:
        timestamp = int(datetime.now().timestamp())
        filename = f"realistic_{breed}_planter_{timestamp}.stl"
    
    # Ensure output directory exists
    output_dir = "realistic_demo_output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        f.write(f"solid PetPlantr_Realistic_{breed.title()}\n")
        
        for face in faces:
            # Calculate normal (simplified)
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]
            
            # Simple normal calculation
            normal = [0, 0, 1]  # Simplified for speed
            
            f.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v1[0]:.6f} {v1[1]:.6f} {v1[2]:.6f}\n")
            f.write(f"      vertex {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}\n")
            f.write(f"      vertex {v3[0]:.6f} {v3[1]:.6f} {v3[2]:.6f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        
        f.write(f"endsolid PetPlantr_Realistic_{breed.title()}\n")
    
    file_size = os.path.getsize(filepath)
    print(f"💾 Saved realistic {breed} planter: {filename}")
    print(f"📏 File size: {file_size:,} bytes")
    print(f"📊 {len(faces)} triangles, {len(vertices)} vertices")
    
    return filepath

def main():
    """Generate realistic dog planters for different breeds"""
    print("🎯 REALISTIC DOG PLANTER GENERATOR")
    print("=" * 50)
    print("Creating actual dog-shaped planters with recognizable features...")
    
    # Generate different breeds
    breeds = ["pug", "golden_retriever", "german_shepherd", "chihuahua"]
    
    generated_files = []
    
    for breed in breeds:
        print(f"\n🐕 Generating {breed.replace('_', ' ').title()}...")
        vertices, faces = create_realistic_dog_mesh(breed)
        filepath = save_realistic_stl(vertices, faces, breed)
        generated_files.append(filepath)
    
    print(f"\n🎉 GENERATION COMPLETE!")
    print("=" * 30)
    print(f"Generated {len(generated_files)} realistic dog planters:")
    
    for filepath in generated_files:
        print(f"📁 {filepath}")
    
    print(f"\n🎯 These models should look much more like actual dogs!")
    print("Load them in the 3D viewer to see the difference.")
    
    return generated_files

if __name__ == "__main__":
    main()
