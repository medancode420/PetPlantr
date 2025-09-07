"""
PetPlantr Modal Test Run - $5 Credits
Test the Modal setup with a small subset before full training
"""

import modal
import os
from pathlib import Path

app = modal.App("petplantr-test")

# Lightweight image for testing
image = modal.Image.debian_slim().pip_install([
    "torch>=2.1.0",
    "torchvision>=0.16.0", 
    "pillow>=10.0.0",
    "numpy>=1.24.0"
])

@app.function(
    image=image,
    gpu=modal.gpu.T4(),  # Cheaper GPU for testing
    timeout=600,  # 10 minutes
    memory=8192   # 8GB RAM
)
def test_gpu_setup():
    """Test GPU setup and basic functionality"""
    import torch
    import numpy as np
    from PIL import Image
    
    print("🚀 Modal GPU Test Starting...")
    print(f"   CUDA Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"   GPU Device: {torch.cuda.get_device_name()}")
        print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        
        # Test tensor operations
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        print(f"   Matrix Multiplication Test: ✅ {z.shape}")
        
        # Test image processing
        test_image = Image.new('RGB', (512, 512), color='red')
        print(f"   Image Processing Test: ✅ {test_image.size}")
        
        return {
            "status": "success",
            "gpu_available": True,
            "gpu_name": torch.cuda.get_device_name(),
            "gpu_memory_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
            "cost_estimate": "~$0.10 for this test"
        }
    else:
        return {
            "status": "error", 
            "gpu_available": False,
            "message": "CUDA not available"
        }

@app.function(
    image=image,
    timeout=300
)
def test_dataset_processing():
    """Test dataset processing without GPU"""
    import numpy as np
    from PIL import Image
    
    print("📊 Testing Dataset Processing...")
    
    # Simulate processing 10 images
    processed_count = 0
    for i in range(10):
        # Create test image
        img = Image.new('RGB', (512, 512), color=(i*25, 100, 200))
        
        # Simulate processing
        img_array = np.array(img)
        processed_img = Image.fromarray(img_array)
        
        processed_count += 1
        print(f"   Processed image {i+1}/10")
    
    return {
        "status": "success",
        "processed_images": processed_count,
        "cost_estimate": "~$0.05 for this test"
    }

@app.local_entrypoint()
def main():
    """Run Modal tests"""
    print("🎯 PetPlantr Modal Test Suite")
    print("=" * 40)
    print("Budget: $5 available (testing with ~$0.20)")
    print("Goal: Verify setup before full training")
    print("")
    
    # Test 1: Dataset processing (CPU only)
    print("🔄 Test 1: Dataset Processing (CPU)")
    try:
        dataset_result = test_dataset_processing.remote()
        print(f"✅ Dataset Test: {dataset_result}")
    except Exception as e:
        print(f"❌ Dataset Test Failed: {e}")
    
    print("")
    
    # Test 2: GPU setup
    print("🔄 Test 2: GPU Setup (T4)")
    try:
        gpu_result = test_gpu_setup.remote()
        print(f"✅ GPU Test: {gpu_result}")
    except Exception as e:
        print(f"❌ GPU Test Failed: {e}")
    
    print("")
    print("🎉 Modal Tests Complete!")
    print("💰 Estimated cost: ~$0.20 of $5.00 available")
    print("")
    print("📋 Next Steps:")
    print("1. If tests pass: Add payment card for $25 more credits")
    print("2. Upload enhanced dataset package")
    print("3. Run full Shape-MVD training ($2.50)")

if __name__ == "__main__":
    main()
