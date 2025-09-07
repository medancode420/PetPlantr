#!/usr/bin/env python3
"""
PetPlantr Shape-MVD Smoke Test Inference
Validates that promoted weights can generate STL files locally

Usage:
    python infer_shape_mvd.py --weights unet128.pth --input mydog_front.jpg
    python infer_shape_mvd.py --weights s3://petplantr-models/stage1/unet128.pth --input test_images/
"""

import argparse
import os
import sys
from pathlib import Path
import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
import boto3
from typing import Optional, List
import tempfile
import subprocess

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent))

def download_weights_from_s3(s3_path: str, local_path: str) -> bool:
    """Download weights from S3 to local path"""
    try:
        print(f"📥 Downloading weights from {s3_path}...")
        
        # Parse S3 path
        s3_parts = s3_path.replace("s3://", "").split("/", 1)
        bucket = s3_parts[0]
        key = s3_parts[1]
        
        # Download file
        s3_client = boto3.client('s3')
        s3_client.download_file(bucket, key, local_path)
        
        print(f"✅ Weights downloaded to {local_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download weights: {e}")
        return False

def load_model_weights(weights_path: str):
    """Load model and weights"""
    try:
        print(f"🔧 Loading model weights from {weights_path}...")
        
        # Load checkpoint with weights_only=False for compatibility
        checkpoint = torch.load(weights_path, map_location='cpu', weights_only=False)
        
        # Extract model configuration
        config = checkpoint.get('config', {})
        model_type = config.get('model_type', 'unknown')
        
        print(f"📊 Model type: {model_type}")
        print(f"📊 Epochs trained: {config.get('epochs', 'unknown')}")
        print(f"📊 Training loss: {checkpoint.get('train_loss', 'unknown'):.4f}")
        print(f"📊 Validation loss: {checkpoint.get('val_loss', 'unknown'):.4f}")
        
        # Load model architecture (simplified version for testing)
        from transformers import CLIPImageProcessor, CLIPVisionModel
        from diffusers.models.unets.unet_2d_condition import UNet2DConditionModel
        
        # Load CLIP processor and vision model
        processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
        vision_encoder = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
        
        # Load UNet model
        unet = UNet2DConditionModel.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            subfolder="unet"
        )
        
        # Load trained weights
        if 'unet_state_dict' in checkpoint:
            unet.load_state_dict(checkpoint['unet_state_dict'])
            print("✅ UNet weights loaded")
        
        if 'vision_encoder_state_dict' in checkpoint:
            vision_encoder.load_state_dict(checkpoint['vision_encoder_state_dict'])
            print("✅ Vision encoder weights loaded")
        
        # Set to evaluation mode
        unet.eval()
        vision_encoder.eval()
        
        return processor, vision_encoder, unet, config
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None, None, None, None

def process_image(image_path: str, processor):
    """Process input image for inference"""
    try:
        print(f"🖼️  Processing image: {image_path}")
        
        # Load and validate image
        image = Image.open(image_path).convert('RGB')
        print(f"📏 Image size: {image.size}")
        
        # Process with CLIP
        inputs = processor(images=image, return_tensors="pt")
        pixel_values = inputs.pixel_values
        
        return image, pixel_values
        
    except Exception as e:
        print(f"❌ Failed to process image: {e}")
        return None, None

def generate_shape_embedding(pixel_values, vision_encoder, unet):
    """Generate 3D shape embedding from image"""
    try:
        print("🧠 Generating shape embedding...")
        
        with torch.no_grad():
            # Encode image
            vision_outputs = vision_encoder(pixel_values=pixel_values)
            image_embeddings = vision_outputs.last_hidden_state
            
            print(f"📊 Image embedding shape: {image_embeddings.shape}")
            
            # Convert RGB to RGBA for UNet
            if pixel_values.shape[1] == 3:  # RGB
                alpha_channel = torch.ones(pixel_values.shape[0], 1, 
                                         pixel_values.shape[2], pixel_values.shape[3])
                rgba_images = torch.cat([pixel_values, alpha_channel], dim=1)
            else:
                rgba_images = pixel_values
            
            # Generate noise for inference
            noise = torch.randn_like(rgba_images)
            
            # Single denoising step (simplified inference)
            timestep = torch.tensor([100])  # Middle timestep
            
            # UNet forward pass
            noise_pred = unet(
                sample=noise,
                timestep=timestep,
                encoder_hidden_states=image_embeddings
            ).sample
            
            # Compute denoised output
            denoised = noise - noise_pred
            
            print(f"📊 Generated shape tensor: {denoised.shape}")
            
            return denoised, image_embeddings
            
    except Exception as e:
        print(f"❌ Failed to generate shape embedding: {e}")
        return None, None

def convert_to_stl(shape_tensor, output_path: str) -> bool:
    """Convert shape tensor to STL file (mock implementation)"""
    try:
        print(f"🔧 Converting to STL: {output_path}")
        
        # This is a simplified mock conversion
        # In production, this would use proper 3D reconstruction
        
        # Extract features from tensor
        shape_data = shape_tensor.squeeze().cpu().numpy()
        
        # Create a simple STL content (mock planter shape)
        stl_content = create_mock_stl(shape_data)
        
        # Write STL file
        with open(output_path, 'w') as f:
            f.write(stl_content)
        
        # Validate STL file
        file_size = os.path.getsize(output_path)
        print(f"📁 STL file created: {file_size:,} bytes")
        
        if file_size < 100:
            print("⚠️  STL file seems very small - may not be valid")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create STL: {e}")
        return False

def create_mock_stl(shape_data: np.ndarray) -> str:
    """Create mock STL content for testing"""
    
    # Extract some basic shape parameters from the neural network output
    height = min(max(float(np.mean(shape_data)), 0.5), 2.0) * 50  # 25-100mm height
    radius = min(max(float(np.std(shape_data)), 0.3), 1.0) * 30   # 9-30mm radius
    
    # Simple cylinder STL (pet planter shape)
    stl_header = "solid PetPlantr_Generated\n"
    stl_footer = "endsolid PetPlantr_Generated\n"
    
    triangles = []
    
    # Create cylinder faces (simplified)
    segments = 16
    for i in range(segments):
        angle1 = (i * 2 * np.pi) / segments
        angle2 = ((i + 1) * 2 * np.pi) / segments
        
        x1 = radius * np.cos(angle1)
        y1 = radius * np.sin(angle1)
        x2 = radius * np.cos(angle2)
        y2 = radius * np.sin(angle2)
        
        # Bottom face triangles
        triangles.append(f"""  facet normal 0.0 0.0 -1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex {x1:.3f} {y1:.3f} 0.0
      vertex {x2:.3f} {y2:.3f} 0.0
    endloop
  endfacet
""")
        
        # Top face triangles
        triangles.append(f"""  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 {height:.3f}
      vertex {x2:.3f} {y2:.3f} {height:.3f}
      vertex {x1:.3f} {y1:.3f} {height:.3f}
    endloop
  endfacet
""")
        
        # Side faces (2 triangles per segment)
        normal_x = x1 / radius
        normal_y = y1 / radius
        
        triangles.append(f"""  facet normal {normal_x:.3f} {normal_y:.3f} 0.0
    outer loop
      vertex {x1:.3f} {y1:.3f} 0.0
      vertex {x1:.3f} {y1:.3f} {height:.3f}
      vertex {x2:.3f} {y2:.3f} 0.0
    endloop
  endfacet
""")
        
        triangles.append(f"""  facet normal {normal_x:.3f} {normal_y:.3f} 0.0
    outer loop
      vertex {x2:.3f} {y2:.3f} 0.0
      vertex {x1:.3f} {y1:.3f} {height:.3f}
      vertex {x2:.3f} {y2:.3f} {height:.3f}
    endloop
  endfacet
""")
    
    return stl_header + "".join(triangles) + stl_footer

def validate_stl_file(stl_path: str) -> bool:
    """Validate STL file can be opened by common tools"""
    try:
        print(f"🔍 Validating STL file: {stl_path}")
        
        # Check file exists and has content
        if not os.path.exists(stl_path):
            print("❌ STL file does not exist")
            return False
        
        file_size = os.path.getsize(stl_path)
        if file_size < 100:
            print(f"❌ STL file too small: {file_size} bytes")
            return False
        
        # Basic STL format validation
        with open(stl_path, 'r') as f:
            content = f.read()
            
        if not content.startswith('solid'):
            print("❌ STL file doesn't start with 'solid'")
            return False
            
        if 'facet normal' not in content:
            print("❌ STL file missing facet definitions")
            return False
            
        if not content.rstrip().endswith('endsolid'):
            print("❌ STL file doesn't end with 'endsolid'")
            return False
        
        # Count triangles
        triangle_count = content.count('facet normal')
        print(f"📊 STL validation: {triangle_count} triangles, {file_size:,} bytes")
        
        if triangle_count < 10:
            print("⚠️  Very few triangles - model may be too simple")
        
        return True
        
    except Exception as e:
        print(f"❌ STL validation failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='PetPlantr Shape-MVD Smoke Test')
    parser.add_argument('--weights', required=True,
                       help='Path to weights file (local or s3://)')
    parser.add_argument('--input', required=True,
                       help='Input image path or directory')
    parser.add_argument('--output', default='output',
                       help='Output directory for STL files')
    parser.add_argument('--device', default='cpu',
                       choices=['cpu', 'cuda'],
                       help='Device to run inference on')
    
    args = parser.parse_args()
    
    print("🚀 PetPlantr Shape-MVD Smoke Test")
    print("=" * 50)
    print(f"📦 Weights: {args.weights}")
    print(f"🖼️  Input: {args.input}")
    print(f"📁 Output: {args.output}")
    print(f"🖥️  Device: {args.device}")
    print("")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Handle S3 weights download
    weights_path = args.weights
    temp_weights = None
    
    if weights_path.startswith('s3://'):
        temp_weights = tempfile.mktemp(suffix='.pth')
        if not download_weights_from_s3(weights_path, temp_weights):
            sys.exit(1)
        weights_path = temp_weights
    
    # Load model
    processor, vision_encoder, unet, config = load_model_weights(weights_path)
    
    if processor is None:
        sys.exit(1)
    
    # Process input images
    input_path = Path(args.input)
    if input_path.is_file():
        image_files = [input_path]
    elif input_path.is_dir():
        image_files = list(input_path.glob('*.jpg')) + list(input_path.glob('*.png'))
    else:
        print(f"❌ Input path not found: {args.input}")
        sys.exit(1)
    
    if not image_files:
        print(f"❌ No image files found in: {args.input}")
        sys.exit(1)
    
    print(f"📊 Found {len(image_files)} image(s) to process")
    print("")
    
    # Process each image
    success_count = 0
    
    for i, image_file in enumerate(image_files, 1):
        print(f"🎯 Processing image {i}/{len(image_files)}: {image_file.name}")
        
        # Process image
        image, pixel_values = process_image(str(image_file), processor)
        if image is None:
            continue
        
        # Generate shape
        shape_tensor, embeddings = generate_shape_embedding(pixel_values, vision_encoder, unet)
        if shape_tensor is None:
            continue
        
        # Convert to STL
        output_name = f"{image_file.stem}_planter.stl"
        output_path = os.path.join(args.output, output_name)
        
        if convert_to_stl(shape_tensor, output_path):
            if validate_stl_file(output_path):
                print(f"✅ STL generated successfully: {output_path}")
                success_count += 1
            else:
                print(f"❌ STL validation failed: {output_path}")
        else:
            print(f"❌ STL generation failed for: {image_file.name}")
        
        print("")
    
    # Clean up
    if temp_weights:
        os.unlink(temp_weights)
    
    # Summary
    print("🎉 SMOKE TEST COMPLETED")
    print("=" * 30)
    print(f"✅ Successful: {success_count}/{len(image_files)}")
    print(f"❌ Failed: {len(image_files) - success_count}/{len(image_files)}")
    
    if success_count > 0:
        print(f"📁 STL files saved to: {args.output}")
        print("🔗 Next steps:")
        print("   1. Open STL files in MeshLab or similar viewer")
        print("   2. Check for holes or malformed geometry")
        print("   3. Verify facial features are recognizable")
        print("   4. Test 3D printing if geometry looks good")
        
        return 0
    else:
        print("❌ All inferences failed - check model and input images")
        return 1

if __name__ == "__main__":
    exit(main())
