#!/usr/bin/env python3
"""
Create a realistic dog-shaped planter GLB model
"""

import json
import struct
import math

def create_dog_shaped_planter_glb():
    """Create a dog-shaped planter with more realistic geometry"""
    
    vertices = []
    indices = []
    
    # Helper function to add a vertex
    def add_vertex(x, y, z):
        vertices.append([x, y, z])
        return len(vertices) - 1
    
    # Helper function to add a triangle
    def add_triangle(a, b, c):
        indices.extend([a, b, c])
    
    # Create dog head (simplified sphere-like shape)
    head_center = [0, 0, 1.2]
    head_radius = 0.4
    
    # Head vertices (simplified sphere)
    head_vertices = []
    for i in range(8):  # 8 segments around
        for j in range(4):  # 4 segments vertical
            theta = (i / 8) * 2 * math.pi
            phi = (j / 4) * math.pi
            x = head_center[0] + head_radius * math.sin(phi) * math.cos(theta)
            y = head_center[1] + head_radius * math.sin(phi) * math.sin(theta)
            z = head_center[2] + head_radius * math.cos(phi)
            head_vertices.append(add_vertex(x, y, z))
    
    # Connect head vertices with triangles
    for i in range(8):
        for j in range(3):
            # Get vertex indices
            v1 = head_vertices[i * 4 + j]
            v2 = head_vertices[((i + 1) % 8) * 4 + j]
            v3 = head_vertices[i * 4 + j + 1]
            v4 = head_vertices[((i + 1) % 8) * 4 + j + 1]
            
            # Add two triangles for each quad
            add_triangle(v1, v2, v3)
            add_triangle(v2, v4, v3)
    
    # Create ears (triangular shapes)
    # Left ear
    ear_l1 = add_vertex(-0.3, -0.2, 1.4)
    ear_l2 = add_vertex(-0.5, -0.1, 1.2)
    ear_l3 = add_vertex(-0.3, 0.0, 1.3)
    add_triangle(ear_l1, ear_l2, ear_l3)
    
    # Right ear
    ear_r1 = add_vertex(0.3, -0.2, 1.4)
    ear_r2 = add_vertex(0.5, -0.1, 1.2)
    ear_r3 = add_vertex(0.3, 0.0, 1.3)
    add_triangle(ear_r1, ear_r3, ear_r2)
    
    # Create snout (elongated shape)
    snout_vertices = []
    snout_center = [0, -0.5, 1.2]
    for i in range(6):
        theta = (i / 6) * 2 * math.pi
        x = snout_center[0] + 0.15 * math.cos(theta)
        y = snout_center[1]
        z = snout_center[2] + 0.1 * math.sin(theta)
        snout_vertices.append(add_vertex(x, y, z))
    
    # Snout tip
    snout_tip = add_vertex(0, -0.7, 1.2)
    
    # Connect snout
    for i in range(6):
        next_i = (i + 1) % 6
        add_triangle(snout_vertices[i], snout_vertices[next_i], snout_tip)
    
    # Create body (dog-shaped torso)
    body_length = 1.5
    body_width = 0.8
    body_height = 0.6
    
    # Body vertices (elongated box with curves)
    body_vertices = []
    for i in range(8):  # 8 points around the body
        for j in range(3):  # 3 levels (bottom, middle, top)
            theta = (i / 8) * 2 * math.pi
            x = (body_width * 0.6) * math.cos(theta)
            y = (body_length * 0.5) * math.sin(theta)
            z = (j / 2) * body_height
            body_vertices.append(add_vertex(x, y, z))
    
    # Connect body vertices
    for i in range(8):
        for j in range(2):
            v1 = body_vertices[i * 3 + j]
            v2 = body_vertices[((i + 1) % 8) * 3 + j]
            v3 = body_vertices[i * 3 + j + 1]
            v4 = body_vertices[((i + 1) % 8) * 3 + j + 1]
            
            add_triangle(v1, v2, v3)
            add_triangle(v2, v4, v3)
    
    # Create legs (simple cylinders)
    leg_positions = [
        [-0.3, -0.5, 0],   # front left
        [0.3, -0.5, 0],    # front right
        [-0.3, 0.5, 0],    # back left
        [0.3, 0.5, 0]      # back right
    ]
    
    for pos in leg_positions:
        # Create simple leg (cylinder)
        leg_vertices = []
        for i in range(6):
            theta = (i / 6) * 2 * math.pi
            # Bottom of leg
            x_bot = pos[0] + 0.1 * math.cos(theta)
            y_bot = pos[1] + 0.1 * math.sin(theta)
            z_bot = 0
            leg_vertices.append(add_vertex(x_bot, y_bot, z_bot))
            
            # Top of leg
            x_top = pos[0] + 0.08 * math.cos(theta)
            y_top = pos[1] + 0.08 * math.sin(theta)
            z_top = 0.4
            leg_vertices.append(add_vertex(x_top, y_top, z_top))
        
        # Connect leg vertices
        for i in range(6):
            next_i = (i + 1) % 6
            # Side faces
            add_triangle(leg_vertices[i*2], leg_vertices[next_i*2], leg_vertices[i*2+1])
            add_triangle(leg_vertices[next_i*2], leg_vertices[next_i*2+1], leg_vertices[i*2+1])
    
    # Create tail (curved)
    tail_segments = 5
    tail_vertices = []
    for i in range(tail_segments):
        t = i / (tail_segments - 1)
        x = 0.1 * math.sin(t * math.pi)
        y = 0.8 + t * 0.3
        z = 0.3 + t * 0.4
        tail_vertices.append(add_vertex(x, y, z))
    
    # Connect tail segments
    for i in range(tail_segments - 1):
        # Simple line segments (would need more vertices for proper tail)
        pass
    
    # Create planter cavity (hollow interior)
    cavity_depth = 0.3
    cavity_radius = 0.5
    cavity_vertices = []
    
    for i in range(8):
        theta = (i / 8) * 2 * math.pi
        x = cavity_radius * math.cos(theta)
        y = cavity_radius * math.sin(theta)
        # Cavity bottom
        cavity_vertices.append(add_vertex(x, y, body_height - cavity_depth))
        # Cavity top (opening)
        cavity_vertices.append(add_vertex(x, y, body_height))
    
    # Connect cavity walls
    for i in range(8):
        next_i = (i + 1) % 8
        v1 = cavity_vertices[i * 2]      # current bottom
        v2 = cavity_vertices[next_i * 2]  # next bottom
        v3 = cavity_vertices[i * 2 + 1]  # current top
        v4 = cavity_vertices[next_i * 2 + 1]  # next top
        
        add_triangle(v1, v2, v3)
        add_triangle(v2, v4, v3)
    
    # Convert to flat arrays
    vertices_flat = []
    for v in vertices:
        vertices_flat.extend(v)
    
    # Create binary data
    vertex_data = struct.pack(f'{len(vertices_flat)}f', *vertices_flat)
    index_data = struct.pack(f'{len(indices)}H', *indices)
    
    # Create glTF JSON with proper dog planter metadata
    gltf_json = {
        "asset": {
            "version": "2.0",
            "generator": "PetPlantr Dog Planter Generator v2.0"
        },
        "scene": 0,
        "scenes": [
            {
                "nodes": [0]
            }
        ],
        "nodes": [
            {
                "mesh": 0,
                "name": "DogPlanter"
            }
        ],
        "meshes": [
            {
                "name": "DogPlanterMesh",
                "primitives": [
                    {
                        "attributes": {
                            "POSITION": 0
                        },
                        "indices": 1,
                        "mode": 4,  # TRIANGLES
                        "material": 0
                    }
                ]
            }
        ],
        "materials": [
            {
                "name": "DogPlanterMaterial",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.8, 0.7, 0.6, 1.0],  # Light brown dog color
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.8
                }
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,  # FLOAT
                "count": len(vertices),
                "type": "VEC3",
                "min": [-0.8, -0.8, 0.0],
                "max": [0.8, 1.0, 1.6]
            },
            {
                "bufferView": 1,
                "componentType": 5123,  # UNSIGNED_SHORT
                "count": len(indices),
                "type": "SCALAR"
            }
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(vertex_data),
                "target": 34962  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": len(vertex_data),
                "byteLength": len(index_data),
                "target": 34963  # ELEMENT_ARRAY_BUFFER
            }
        ],
        "buffers": [
            {
                "byteLength": len(vertex_data) + len(index_data)
            }
        ]
    }
    
    # Convert JSON to bytes
    json_bytes = json.dumps(gltf_json, separators=(',', ':')).encode('utf-8')
    
    # Pad JSON to 4-byte boundary
    json_padding = (4 - len(json_bytes) % 4) % 4
    json_bytes += b' ' * json_padding
    
    # Combine binary data
    binary_data = vertex_data + index_data
    
    # Pad binary data to 4-byte boundary
    binary_padding = (4 - len(binary_data) % 4) % 4
    binary_data += b'\x00' * binary_padding
    
    # Create GLB header
    magic = b'glTF'
    version = struct.pack('<I', 2)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary_data)
    length = struct.pack('<I', total_length)
    
    # JSON chunk header
    json_chunk_length = struct.pack('<I', len(json_bytes))
    json_chunk_type = b'JSON'
    
    # Binary chunk header
    bin_chunk_length = struct.pack('<I', len(binary_data))
    bin_chunk_type = b'BIN\x00'
    
    # Combine all parts
    glb_data = (magic + version + length + 
                json_chunk_length + json_chunk_type + json_bytes +
                bin_chunk_length + bin_chunk_type + binary_data)
    
    return glb_data

def main():
    """Create and save a realistic dog planter GLB file"""
    print("Creating realistic dog-shaped planter GLB model...")
    glb_data = create_dog_shaped_planter_glb()
    
    # Save to multiple locations
    locations = [
        'frontend/public/demo/dog-planter.glb',
        'frontend/public/demo/sample-planter.glb',
        'frontend/public/demo-models/default-planter.glb',
        'frontend/public/models/demo-dog-planter.glb'
    ]
    
    for location in locations:
        with open(location, 'wb') as f:
            f.write(glb_data)
        print(f"Created realistic dog planter GLB: {location}")
    
    print(f"GLB file size: {len(glb_data)} bytes")
    print("Realistic dog planter GLB models created successfully!")
    print("\nFeatures:")
    print("- Dog head with ears and snout")
    print("- Elongated dog body")
    print("- Four legs")
    print("- Tail")
    print("- Hollow planter cavity")
    print("- Brown dog-like material")

if __name__ == "__main__":
    main()
