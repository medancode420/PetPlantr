#!/usr/bin/env python3
"""
Debug Neural Network Dog Planter Generation
Analyze why the neural network isn't creating proper dog planter shapes
"""

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import tempfile
import os
from neural_network_image_to_3d import NeuralNetworkImageTo3D

def create_debug_dog_image():
    """Create a clear dog silhouette for debugging"""
    print("🎨 Creating debug dog silhouette...")
    
    # Create high contrast dog silhouette
    img = Image.new('RGB', (512, 512), color=(255, 255, 255))  # White background
    draw = ImageDraw.Draw(img)
    
    # Draw clear dog silhouette in black for high contrast
    # Body (large oval)
    draw.ellipse([150, 250, 350, 400], fill=(0, 0, 0))
    # Head (circle)
    draw.ellipse([200, 150, 300, 250], fill=(0, 0, 0))
    # Ears (triangular)
    draw.ellipse([180, 130, 220, 180], fill=(0, 0, 0))
    draw.ellipse([280, 130, 320, 180], fill=(0, 0, 0))
    # Legs (rectangles)
    draw.rectangle([170, 380, 190, 450], fill=(0, 0, 0))
    draw.rectangle([210, 380, 230, 450], fill=(0, 0, 0))
    draw.rectangle([270, 380, 290, 450], fill=(0, 0, 0))
    draw.rectangle([310, 380, 330, 450], fill=(0, 0, 0))
    # Tail
    draw.ellipse([340, 280, 380, 320], fill=(0, 0, 0))
    
    # Add some depth variation with gray tones
    # Body center (lighter for depth)
    draw.ellipse([180, 280, 320, 370], fill=(64, 64, 64))
    # Head center
    draw.ellipse([220, 170, 280, 230], fill=(64, 64, 64))
    
    img.save('debug_dog_silhouette.png')
    print("   ✅ Saved: debug_dog_silhouette.png")
    return img

def debug_neural_network_processing():
    """Debug the neural network processing step by step"""
    print("\n🔍 DEBUGGING NEURAL NETWORK PROCESSING")
    print("=" * 60)
    
    # Create test image
    test_image = create_debug_dog_image()
    
    # Initialize converter
    print("\n🧠 Initializing neural network converter...")
    converter = NeuralNetworkImageTo3D()
    
    # Let's examine the CLIP features
    print("\n🔍 Step 1: CLIP Semantic Analysis")
    inputs = converter.clip_processor(images=test_image, return_tensors="pt")
    import torch
    with torch.no_grad():
        image_features = converter.clip_model.get_image_features(**inputs)
    
    print(f"   📊 CLIP features shape: {image_features.shape}")
    print(f"   📊 Feature magnitude: {torch.norm(image_features).item():.3f}")
    print(f"   📊 Feature range: {image_features.min().item():.3f} to {image_features.max().item():.3f}")
    
    # Let's examine the DPT depth estimation
    print("\n🏔️ Step 2: DPT Depth Estimation")
    dpt_inputs = converter.depth_processor(images=test_image, return_tensors="pt")
    with torch.no_grad():
        predicted_depth = converter.depth_model(**dpt_inputs).predicted_depth
    
    print(f"   📊 DPT depth shape: {predicted_depth.shape}")
    print(f"   📊 Depth range: {predicted_depth.min().item():.3f} to {predicted_depth.max().item():.3f}")
    
    # Convert depth to numpy for analysis
    depth_np = predicted_depth.squeeze().cpu().numpy()
    
    # Visualize what the neural networks are seeing
    print("\n📊 Step 3: Analyzing Neural Network Understanding")
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Neural Network Debug Analysis', fontsize=16)
    
    # Original image
    axes[0,0].imshow(test_image)
    axes[0,0].set_title('Original Dog Image')
    axes[0,0].axis('off')
    
    # DPT depth map
    im1 = axes[0,1].imshow(depth_np, cmap='viridis')
    axes[0,1].set_title('DPT Neural Depth Estimation')
    axes[0,1].axis('off')
    plt.colorbar(im1, ax=axes[0,1])
    
    # Depth histogram
    axes[1,0].hist(depth_np.flatten(), bins=50, alpha=0.7)
    axes[1,0].set_title('Depth Value Distribution')
    axes[1,0].set_xlabel('Depth Value')
    axes[1,0].set_ylabel('Frequency')
    
    # CLIP feature visualization (show some sample features)
    feature_subset = image_features.squeeze()[:100].cpu().numpy()
    axes[1,1].bar(range(len(feature_subset)), feature_subset)
    axes[1,1].set_title('CLIP Feature Sample (first 100)')
    axes[1,1].set_xlabel('Feature Index')
    axes[1,1].set_ylabel('Feature Value')
    
    plt.tight_layout()
    plt.savefig('neural_network_debug_analysis.png', dpi=150, bbox_inches='tight')
    print("   ✅ Saved: neural_network_debug_analysis.png")
    
    # Analyze what the neural network "sees"
    print("\n🧠 Neural Network Analysis Results:")
    
    # Check if depth map has meaningful variation
    depth_variation = np.std(depth_np)
    print(f"   📊 Depth variation (std): {depth_variation:.4f}")
    
    if depth_variation < 0.01:
        print("   ⚠️ WARNING: Very low depth variation - neural network may not be detecting the dog shape")
    
    # Check for dog-like patterns in depth
    dog_area_pixels = np.sum((depth_np > np.mean(depth_np)))
    total_pixels = depth_np.size
    dog_ratio = dog_area_pixels / total_pixels
    
    print(f"   📊 Potential dog area: {dog_ratio:.1%} of image")
    
    if dog_ratio < 0.1 or dog_ratio > 0.9:
        print("   ⚠️ WARNING: Dog detection may be poor - unusual area ratio")
    
    # Check semantic features
    feature_magnitude = torch.norm(image_features).item()
    if feature_magnitude < 1.0:
        print(f"   ⚠️ WARNING: Low CLIP feature magnitude ({feature_magnitude:.3f}) - weak semantic understanding")
    else:
        print(f"   ✅ Good CLIP feature magnitude ({feature_magnitude:.3f})")
    
    return test_image, depth_np, image_features

def test_alternative_approach():
    """Test if we can improve the neural network understanding"""
    print("\n🚀 TESTING IMPROVED NEURAL APPROACH")
    print("=" * 60)
    
    # Try with better preprocessing
    test_image = create_debug_dog_image()
    
    # Convert to grayscale first (sometimes helps with depth models)
    gray_image = test_image.convert('L').convert('RGB')
    gray_image.save('debug_dog_grayscale.png')
    
    # Initialize converter
    converter = NeuralNetworkImageTo3D()
    
    print("🔍 Testing grayscale version...")
    result_gray = converter.convert_image_to_3d('debug_dog_grayscale.png', 'debug_dog_gray.stl', method='neural_depth')
    print(f"   Grayscale result: {result_gray['success']}, vertices: {result_gray.get('vertex_count', 'N/A')}")
    
    print("🔍 Testing original color version...")
    result_color = converter.convert_image_to_3d('debug_dog_silhouette.png', 'debug_dog_color.stl', method='neural_depth')
    print(f"   Color result: {result_color['success']}, vertices: {result_color.get('vertex_count', 'N/A')}")
    
    return result_gray, result_color

def main():
    """Main debugging function"""
    print("🐕 NEURAL NETWORK DOG PLANTER DEBUG SESSION")
    print("=" * 80)
    print("Investigating why neural networks aren't creating proper dog planters...")
    
    # Step 1: Debug neural processing
    test_image, depth_map, features = debug_neural_network_processing()
    
    # Step 2: Test alternative approaches
    result_gray, result_color = test_alternative_approach()
    
    # Step 3: Provide diagnosis
    print("\n🔬 DIAGNOSIS AND RECOMMENDATIONS")
    print("=" * 60)
    
    depth_variation = np.std(depth_map)
    
    if depth_variation < 0.01:
        print("❌ PROBLEM IDENTIFIED: Poor depth detection")
        print("   The DPT model is not detecting meaningful depth in the dog silhouette")
        print("   Recommendation: Need to use a different depth model or preprocessing")
    
    if result_gray['vertex_count'] == result_color['vertex_count']:
        print("❌ PROBLEM IDENTIFIED: No shape differentiation")
        print("   Neural network generating same output regardless of input")
        print("   Recommendation: Need better semantic understanding integration")
    
    print("\n💡 PROPOSED SOLUTIONS:")
    print("1. Use a different depth estimation model (MiDaS, LeReS)")
    print("2. Implement proper Zero-1-to-3 for multi-view generation")
    print("3. Add semantic segmentation to identify dog parts")
    print("4. Use Point-E or TripoSR for direct 3D generation")
    print("5. Implement custom training on dog-specific data")
    
    print(f"\n📁 Debug files generated:")
    print(f"   - debug_dog_silhouette.png")
    print(f"   - neural_network_debug_analysis.png")
    print(f"   - debug_dog_gray.stl")
    print(f"   - debug_dog_color.stl")

if __name__ == "__main__":
    main()
