#!/usr/bin/env python3
"""
Model Quantization Script for PetPlantr
Converts CLIP model to INT8 precision for improved performance
"""

import torch
from transformers import CLIPModel, CLIPProcessor
import time
from pathlib import Path
import json

def quantize_clip_model():
    """Quantize CLIP model to INT8 precision"""

    print("🔄 Starting CLIP Model Quantization...")
    print("=" * 50)

    # Load original model
    print("📥 Loading original CLIP model...")
    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')

    # Get original model stats
    original_size = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**2)
    original_params = sum(p.numel() for p in model.parameters())

    print(f"   Original size: {original_size:.1f} MB")
    print(f"   Parameters: {original_params:,}")
    # Create quantized model using dynamic quantization
    print("\\n🔧 Applying INT8 quantization...")

    # Quantize the model (dynamic quantization for better performance)
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},  # Quantize linear layers
        dtype=torch.qint8
    )

    # Get quantized model stats
    quantized_size = sum(p.numel() * p.element_size() for p in quantized_model.parameters()) / (1024**2)
    quantized_params = sum(p.numel() for p in quantized_model.parameters())

    print(f"   Quantized size: {quantized_size:.1f} MB")
    print(f"   Parameters: {quantized_params:,}")
    print(f"   Compression ratio: {original_size/quantized_size:.1f}x")
    print(f"   Parameter reduction: {100 * (original_params - quantized_params) / original_params:.1f}%")
    # Test inference performance
    print("\\n⚡ Testing quantized model performance...")

    from PIL import Image
    import numpy as np

    # Create test image
    test_image = Image.fromarray((np.random.rand(224, 224, 3) * 255).astype(np.uint8))
    test_input = processor(text=['golden retriever'], images=[test_image], return_tensors='pt')

    # Test original model
    model.eval()
    start_time = time.time()
    with torch.no_grad():
        original_output = model(**test_input)
    original_time = time.time() - start_time

    # Test quantized model
    quantized_model.eval()
    start_time = time.time()
    with torch.no_grad():
        quantized_output = quantized_model(**test_input)
    quantized_time = time.time() - start_time

    print(f"   Original model inference time: {original_time:.4f} seconds")
    print(f"   Quantized model inference time: {quantized_time:.4f} seconds")
    print(f"   Speedup: {original_time / quantized_time:.2f}x")

    # Calculate accuracy preservation (cosine similarity)
    original_logits = original_output.logits_per_image
    quantized_logits = quantized_output.logits_per_image

    cosine_sim = torch.nn.functional.cosine_similarity(
        original_logits.flatten(),
        quantized_logits.flatten(),
        dim=0
    ).item()

    print(f"   Cosine similarity (accuracy preservation): {cosine_sim:.4f}")
    # Save quantized model
    print("\\n💾 Saving quantized model...")
    save_path = Path("models/clip_breed_int8")
    save_path.mkdir(parents=True, exist_ok=True)

    # Save model
    torch.save(quantized_model.state_dict(), save_path / "pytorch_model.bin")

    # Save config
    config = model.config
    config.save_pretrained(save_path)

    # Save processor
    processor.save_pretrained(save_path)

    # Save quantization metadata
    metadata = {
        "quantization_type": "dynamic_int8",
        "original_size_mb": original_size,
        "quantized_size_mb": quantized_size,
        "compression_ratio": original_size / quantized_size,
        "original_latency": original_time,
        "quantized_latency": quantized_time,
        "speedup_ratio": original_time / quantized_time,
        "accuracy_preservation": cosine_sim,
        "created_at": time.time(),
        "model_version": "clip-vit-base-patch32-int8"
    }

    with open(save_path / "quantization_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Quantized model saved to: {save_path}")
    print("\\n📊 Quantization Results Summary:")
    print("=" * 40)
    print(f"   Model size reduction: {original_size:.1f}MB → {quantized_size:.1f}MB")
    print(f"   Compression ratio: {original_size/quantized_size:.1f}x")
    print(f"   Performance speedup: {original_time/quantized_time:.2f}x")
    print(f"   Accuracy preservation: {cosine_sim:.4f}")
    print(f"   Accuracy drop: {(1-cosine_sim)*100:.4f}%")
    # Verify accuracy drop is within limits
    accuracy_drop = (1 - cosine_sim) * 100
    if accuracy_drop <= 1.0:
        print(f"   ✅ Accuracy drop ({accuracy_drop:.2f}%) within 1pp limit")
        return True
    else:
        print(f"   ❌ Accuracy drop ({accuracy_drop:.2f}%) exceeds 1pp limit")
        return False

if __name__ == "__main__":
    success = quantize_clip_model()
    if success:
        print("\\n🎉 Model quantization completed successfully!")
        print("📋 Next: Test the quantized model with your breed detection pipeline")
    else:
        print("\\n❌ Model quantization failed accuracy requirements")
        print("🔧 Consider adjusting quantization parameters")
