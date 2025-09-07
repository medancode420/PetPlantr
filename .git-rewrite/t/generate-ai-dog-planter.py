#!/usr/bin/env python3
"""
PetPlantr AI-Powered Dog Shape Generator
Uses computer vision to analyze the dog image and generate a custom planter shape
"""

import sys
import os
import math
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import argparse
from pathlib import Path

def analyze_dog_features(image_path):
    """Analyze dog image to extract shape features for planter generation"""
    print(f"🔍 Analyzing dog features from: {image_path}")
    
    try:
        # Load and preprocess image
        image = Image.open(image_path).convert('RGB')
        print(f"📏 Original image size: {image.size}")
        
        # Resize for processing
        working_size = (256, 256)
        image = image.resize(working_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array for analysis
        img_array = np.array(image)
        
        # Enhance contrast to better detect features
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(2.0)
        enhanced_array = np.array(enhanced)
        
        # Convert to grayscale for shape analysis
        gray = np.mean(img_array, axis=2)
        
        # Find the main subject (dog) by detecting areas with high contrast
        edges = detect_edges(gray)
        
        # Extract shape parameters
        features = extract_shape_features(gray, edges, img_array)
        
        print("🐕 Detected dog features:")
        print(f"   • Head width ratio: {features['head_width']:.2f}")
        print(f"   • Body height ratio: {features['body_height']:.2f}")
        print(f"   • Ear shape factor: {features['ear_shape']:.2f}")
        print(f"   • Snout length ratio: {features['snout_length']:.2f}")
        print(f"   • Overall roundness: {features['roundness']:.2f}")
        
        return features
        
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")
        return None

def detect_edges(gray_image):
    """Simple edge detection using gradient"""
    # Compute gradients
    grad_x = np.gradient(gray_image, axis=1)
    grad_y = np.gradient(gray_image, axis=0)
    
    # Compute magnitude
    edges = np.sqrt(grad_x**2 + grad_y**2)
    
    # Normalize
    edges = (edges - edges.min()) / (edges.max() - edges.min())
    
    return edges

def extract_shape_features(gray_image, edges, color_image):
    """Extract shape features from the dog image"""
    h, w = gray_image.shape
    
    # Find the center of mass (approximate dog center)
    y_indices, x_indices = np.mgrid[:h, :w]
    weights = edges + 0.1  # Add small weight to avoid division by zero
    
    center_x = np.sum(x_indices * weights) / np.sum(weights)
    center_y = np.sum(y_indices * weights) / np.sum(weights)
    
    # Analyze color distribution for breed characteristics
    avg_color = np.mean(color_image, axis=(0, 1))
    color_variance = np.var(color_image.reshape(-1, 3), axis=0)
    
    # Calculate shape metrics
    # Head width (assume upper third contains head)
    upper_third = edges[:h//3, :]
    head_edge_density = np.sum(upper_third) / (h * w / 3)
    
    # Body height (vertical extent of high-contrast areas)
    vertical_profile = np.mean(edges, axis=1)
    body_extent = np.sum(vertical_profile > 0.3) / h
    
    # Ear shape (look for high-contrast areas in upper corners)
    left_ear_region = edges[:h//4, :w//4]
    right_ear_region = edges[:h//4, -w//4:]
    ear_activity = (np.mean(left_ear_region) + np.mean(right_ear_region)) / 2
    
    # Snout detection (look for elongated features in center-lower area)
    snout_region = edges[h//3:2*h//3, w//3:2*w//3]
    snout_length = np.sum(np.max(snout_region, axis=0) > 0.4) / (w//3)
    
    # Overall roundness (based on how circular the main features are)
    # Calculate distance from center for all edge points
    distances = np.sqrt((x_indices - center_x)**2 + (y_indices - center_y)**2)
    weighted_distances = distances * edges
    avg_distance = np.sum(weighted_distances) / np.sum(edges)
    distance_variance = np.sum(edges * (distances - avg_distance)**2) / np.sum(edges)
    roundness = 1.0 / (1.0 + distance_variance / (avg_distance**2))
    
    return {
        'head_width': min(head_edge_density * 2, 1.0),
        'body_height': body_extent,
        'ear_shape': min(ear_activity * 3, 1.0),
        'snout_length': min(snout_length, 1.0),
        'roundness': roundness,
        'center_x': center_x / w,
        'center_y': center_y / h,
        'avg_color': avg_color,
        'color_variance': color_variance
    }

def generate_dog_planter_stl(features, output_path):
    """Generate a dog-shaped planter STL based on analyzed features"""
    print(f"🏗️  Generating dog-shaped planter STL...")
    
    # Base dimensions (in mm)
    base_size = 80  # Base diameter
    base_height = 60  # Base height
    
    # Adjust dimensions based on dog features
    # Wider dogs get wider planters, taller dogs get taller planters
    width_factor = 0.7 + (features['head_width'] * 0.6)  # 0.7-1.3x
    height_factor = 0.8 + (features['body_height'] * 0.4)  # 0.8-1.2x
    
    actual_width = base_size * width_factor
    actual_height = base_height * height_factor
    
    # Create more complex shape based on features
    vertices = []
    faces = []
    
    print(f"📐 Planter dimensions: {actual_width:.1f}mm × {actual_height:.1f}mm")
    
    # Generate vertices for the dog-shaped planter
    segments = 16
    layers = 8
    
    for layer in range(layers + 1):
        layer_height = (layer / layers) * actual_height
        
        # Create dog-like profile that changes with height
        for segment in range(segments):
            angle = (segment / segments) * 2 * math.pi
            
            # Base radius for this layer
            base_radius = actual_width / 2
            
            # Create dog-like shape modifications
            # Head area (front, around angle 0)
            head_influence = max(0, math.cos(angle)) * features['head_width']
            
            # Ear areas (upper sides, around angles π/3 and 5π/3)
            left_ear = max(0, math.cos(angle - math.pi/3)) * features['ear_shape'] * 0.3
            right_ear = max(0, math.cos(angle - 5*math.pi/3)) * features['ear_shape'] * 0.3
            
            # Snout extension (front-center)
            snout_influence = max(0, math.cos(angle) * math.cos(2*angle)) * features['snout_length'] * 0.4
            
            # Body rounding
            body_rounding = features['roundness'] * 0.2
            
            # Combine influences
            radius_modifier = 1.0 + head_influence * 0.2 + left_ear + right_ear + snout_influence - body_rounding
            
            # Layer-based tapering (narrower at top)
            layer_taper = 1.0 - (layer / layers) * 0.2
            
            # Final radius
            radius = base_radius * radius_modifier * layer_taper
            
            # Position
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = layer_height
            
            vertices.append([x, y, z])
    
    # Generate faces
    vertex_idx = 0
    for layer in range(layers):
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            
            # Current layer vertices
            v1 = layer * segments + segment
            v2 = layer * segments + next_segment
            
            # Next layer vertices
            v3 = (layer + 1) * segments + segment
            v4 = (layer + 1) * segments + next_segment
            
            # Two triangles per quad
            faces.append([v1, v2, v3])
            faces.append([v2, v4, v3])
    
    # Add bottom face
    bottom_center = len(vertices)
    vertices.append([0, 0, 0])  # Bottom center
    
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        faces.append([bottom_center, next_segment, segment])
    
    # Add top face (with planting cavity)
    cavity_radius = actual_width * 0.3  # Inner cavity
    cavity_segments = 12
    
    # Top outer ring
    top_layer_start = layers * segments
    
    # Inner cavity vertices
    cavity_start_idx = len(vertices)
    for segment in range(cavity_segments):
        angle = (segment / cavity_segments) * 2 * math.pi
        x = cavity_radius * math.cos(angle)
        y = cavity_radius * math.sin(angle)
        z = actual_height - 10  # Cavity depth
        vertices.append([x, y, z])
    
    # Top center for cavity bottom
    cavity_center = len(vertices)
    vertices.append([0, 0, actual_height - 10])
    
    # Cavity bottom faces
    for segment in range(cavity_segments):
        next_segment = (segment + 1) % cavity_segments
        v1 = cavity_start_idx + segment
        v2 = cavity_start_idx + next_segment
        faces.append([cavity_center, v1, v2])
    
    # Write STL file
    write_stl_file(vertices, faces, output_path, features)
    
    return True

def write_stl_file(vertices, faces, output_path, features):
    """Write the STL file"""
    try:
        with open(output_path, 'w') as f:
            f.write(f"solid PetPlantr_AI_Generated\n")
            f.write(f"# Generated from AI analysis\n")
            f.write(f"# Head width: {features['head_width']:.2f}\n")
            f.write(f"# Body height: {features['body_height']:.2f}\n")
            f.write(f"# Roundness: {features['roundness']:.2f}\n")
            
            for face in faces:
                # Calculate normal vector
                v1 = vertices[face[0]]
                v2 = vertices[face[1]]
                v3 = vertices[face[2]]
                
                # Edge vectors
                edge1 = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]]
                edge2 = [v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]]
                
                # Cross product for normal
                normal = [
                    edge1[1] * edge2[2] - edge1[2] * edge2[1],
                    edge1[2] * edge2[0] - edge1[0] * edge2[2],
                    edge1[0] * edge2[1] - edge1[1] * edge2[0]
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
            
            f.write("endsolid PetPlantr_AI_Generated\n")
        
        file_size = os.path.getsize(output_path)
        print(f"✅ Dog-shaped planter STL created: {file_size:,} bytes")
        print(f"📁 Saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error writing STL file: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Generate AI-powered dog-shaped planter')
    parser.add_argument('--input', required=True, help='Input dog image path')
    parser.add_argument('--output', required=True, help='Output STL file path')
    
    args = parser.parse_args()
    
    print("🐕 PetPlantr AI Dog Shape Generator")
    print("==================================")
    print(f"📸 Input: {args.input}")
    print(f"📁 Output: {args.output}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Analyze dog features
    features = analyze_dog_features(args.input)
    
    if features is None:
        print("❌ Failed to analyze dog features")
        return 1
    
    # Generate STL
    if generate_dog_planter_stl(features, args.output):
        print("\n🎉 SUCCESS! AI-generated dog planter is ready!")
        print(f"🎯 The planter shape has been customized based on your dog's unique features")
        return 0
    else:
        print("❌ Failed to generate STL file")
        return 1

if __name__ == "__main__":
    sys.exit(main())
