#!/usr/bin/env python3

# Create a minimal demo GLB file for testing
# This creates a simple cube that's much smaller than the current 3.6MB file

import struct
import json
import base64

def create_minimal_glb():
    """Create a minimal GLB file with a simple cube"""
    
    # Simple cube vertices (8 vertices)
    vertices = [
        -1.0, -1.0,  1.0,  # 0
         1.0, -1.0,  1.0,  # 1
         1.0,  1.0,  1.0,  # 2
        -1.0,  1.0,  1.0,  # 3
        -1.0, -1.0, -1.0,  # 4
         1.0, -1.0, -1.0,  # 5
         1.0,  1.0, -1.0,  # 6
        -1.0,  1.0, -1.0,  # 7
    ]
    
    # Cube indices (12 triangles)
    indices = [
        0, 1, 2,   0, 2, 3,  # front
        1, 5, 6,   1, 6, 2,  # right
        5, 4, 7,   5, 7, 6,  # back
        4, 0, 3,   4, 3, 7,  # left
        3, 2, 6,   3, 6, 7,  # top
        4, 5, 1,   4, 1, 0,  # bottom
    ]
    
    # Pack vertex data
    vertex_data = b''
    for v in vertices:
        vertex_data += struct.pack('<f', v)
    
    # Pack index data
    index_data = b''
    for i in indices:
        index_data += struct.pack('<H', i)
    
    # Create minimal glTF JSON
    gltf_json = {
        "asset": {"version": "2.0", "generator": "PetPlantr Demo"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 1
            }]
        }],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,  # FLOAT
                "count": 8,
                "type": "VEC3",
                "min": [-1.0, -1.0, -1.0],
                "max": [1.0, 1.0, 1.0]
            },
            {
                "bufferView": 1,
                "componentType": 5123,  # UNSIGNED_SHORT
                "count": 36,
                "type": "SCALAR"
            }
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(vertex_data)
            },
            {
                "buffer": 0,
                "byteOffset": len(vertex_data),
                "byteLength": len(index_data)
            }
        ],
        "buffers": [{
            "byteLength": len(vertex_data) + len(index_data)
        }]
    }
    
    # Convert JSON to bytes
    json_bytes = json.dumps(gltf_json, separators=(',', ':')).encode('utf-8')
    
    # Pad JSON to 4-byte boundary
    json_padding = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b' ' * json_padding
    
    # Binary data
    bin_data = vertex_data + index_data
    bin_padding = (4 - (len(bin_data) % 4)) % 4
    bin_data += b'\x00' * bin_padding
    
    # Create GLB header
    glb_header = struct.pack('<III', 0x46546C67, 2, 20 + 8 + len(json_bytes) + 8 + len(bin_data))
    
    # JSON chunk
    json_chunk = struct.pack('<II', len(json_bytes), 0x4E4F534A) + json_bytes
    
    # Binary chunk
    bin_chunk = struct.pack('<II', len(bin_data), 0x004E4942) + bin_data
    
    return glb_header + json_chunk + bin_chunk

if __name__ == "__main__":
    glb_data = create_minimal_glb()
    
    with open("/Users/medan/Downloads/PetPlantr/frontend/public/demo/sample-planter-small.glb", "wb") as f:
        f.write(glb_data)
    
    print(f"Created minimal demo GLB file: {len(glb_data)} bytes")
    print("This is a simple cube that can be used as a demo 3D model")
