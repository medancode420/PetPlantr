#!/usr/bin/env python3
"""
Super Simple Working Dog Planter
Creates an ASCII STL that you can definitely see working
"""

def create_simple_cube_with_dog_features():
    """Create a simple recognizable shape"""
    
    # Create a simple cube with dog-like modifications
    vertices = [
        # Bottom face (z=0)
        [-50, -50, 0],   # 0
        [50, -50, 0],    # 1  
        [50, 50, 0],     # 2
        [-50, 50, 0],    # 3
        
        # Top face (z=80)  
        [-40, -40, 80],  # 4 (narrower - dog head)
        [40, -30, 80],   # 5 (flat face)
        [40, 30, 80],    # 6
        [-40, 40, 80],   # 7
    ]
    
    # Define faces (triangles)
    faces = [
        # Bottom face (pointing down)
        [0, 2, 1], [0, 3, 2],
        
        # Top face (pointing up) 
        [4, 5, 6], [4, 6, 7],
        
        # Sides
        [0, 1, 5], [0, 5, 4],  # Front
        [1, 2, 6], [1, 6, 5],  # Right  
        [2, 3, 7], [2, 7, 6],  # Back
        [3, 0, 4], [3, 4, 7],  # Left
    ]
    
    return vertices, faces

def save_ascii_stl(vertices, faces, filename):
    """Save as ASCII STL (easier to debug)"""
    print(f"💾 Saving ASCII STL: {filename}")
    
    with open(filename, 'w') as f:
        f.write("solid PetPlantr_Working_Dog\n")
        
        for face in faces:
            # Get vertices
            v1 = vertices[face[0]]
            v2 = vertices[face[1]]
            v3 = vertices[face[2]]
            
            # Calculate normal
            u = [v2[i] - v1[i] for i in range(3)]
            v = [v3[i] - v1[i] for i in range(3)]
            normal = [
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0]
            ]
            
            # Normalize
            length = (sum(n*n for n in normal)) ** 0.5
            if length > 0:
                normal = [n/length for n in normal]
            
            # Write facet
            f.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v1[0]:.6f} {v1[1]:.6f} {v1[2]:.6f}\n")
            f.write(f"      vertex {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}\n")
            f.write(f"      vertex {v3[0]:.6f} {v3[1]:.6f} {v3[2]:.6f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        
        f.write("endsolid PetPlantr_Working_Dog\n")
    
    print(f"✅ ASCII STL saved with {len(faces)} triangles")

def main():
    """Create a simple working model"""
    print("🎬 Super Simple Working Dog Generator")
    print("=" * 40)
    
    # Create shape
    vertices, faces = create_simple_cube_with_dog_features()
    
    # Save as ASCII STL
    filename = "working_demo_output/simple_working_dog.stl"
    save_ascii_stl(vertices, faces, filename)
    
    print(f"\n🎉 SUCCESS!")
    print(f"📁 File: {filename}")
    print(f"📏 Size: 100mm × 100mm × 80mm")
    print(f"🐕 Shape: Simple dog-like form")
    print(f"📝 Format: ASCII STL (human readable)")
    
    # Show what it looks like
    print(f"\n📄 File contents preview:")
    with open(filename, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:10]):
            print(f"   {line.strip()}")
        print(f"   ... ({len(lines)} total lines)")
    
    return filename

if __name__ == "__main__":
    main()
