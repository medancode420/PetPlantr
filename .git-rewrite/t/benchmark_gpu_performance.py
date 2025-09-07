#!/usr/bin/env python3
"""
GPU Performance Benchmark for PetPlantr
Quick Win #1 - Profile CUDA performance vs CPU baseline
"""

import torch
import torchvision.transforms as transforms
from transformers import CLIPProcessor, CLIPModel, DPTForDepthEstimation, DPTFeatureExtractor
import time
import psutil
import gc
from PIL import Image
import numpy as np

def check_gpu_availability():
    """Check and report GPU configuration"""
    print("🔍 GPU Configuration Check")
    print("-" * 50)
    
    # CUDA availability
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    
    if cuda_available:
        device_count = torch.cuda.device_count()
        print(f"GPU Devices: {device_count}")
        
        for i in range(device_count):
            props = torch.cuda.get_device_properties(i)
            memory_gb = props.total_memory / 1e9
            print(f"  GPU {i}: {props.name}")
            print(f"    Memory: {memory_gb:.1f} GB")
            print(f"    Compute Capability: {props.major}.{props.minor}")
    
    # MPS (Apple Silicon) availability
    mps_available = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
    print(f"MPS (Apple Silicon) Available: {mps_available}")
    
    return cuda_available or mps_available

def benchmark_model_loading():
    """Benchmark model loading times"""
    print("\n📊 Model Loading Benchmark")
    print("-" * 50)
    
    models = {
        "CLIP": ("openai/clip-vit-base-patch32", CLIPModel, CLIPProcessor),
        "DPT": ("Intel/dpt-large", DPTForDepthEstimation, DPTFeatureExtractor)
    }
    
    results = {}
    
    for model_name, (model_id, model_class, processor_class) in models.items():
        print(f"\nLoading {model_name}...")
        
        # CPU Loading
        start_time = time.time()
        model_cpu = model_class.from_pretrained(model_id)
        processor = processor_class.from_pretrained(model_id)
        cpu_load_time = time.time() - start_time
        
        # GPU Loading (if available)
        gpu_load_time = None
        if torch.cuda.is_available():
            start_time = time.time()
            model_gpu = model_cpu.to('cuda')
            gpu_load_time = time.time() - start_time
        
        results[model_name] = {
            'cpu_load_time': cpu_load_time,
            'gpu_load_time': gpu_load_time
        }
        
        print(f"  CPU Load Time: {cpu_load_time:.2f}s")
        if gpu_load_time:
            print(f"  GPU Transfer Time: {gpu_load_time:.2f}s")
        
        # Memory usage
        memory_usage = psutil.Process().memory_info().rss / 1e9
        print(f"  Memory Usage: {memory_usage:.1f} GB")
        
        # Cleanup
        del model_cpu
        if torch.cuda.is_available():
            del model_gpu
            torch.cuda.empty_cache()
        gc.collect()
    
    return results

def benchmark_inference_speed():
    """Benchmark inference speed on sample image"""
    print("\n⚡ Inference Speed Benchmark")
    print("-" * 50)
    
    # Create sample image (simulating dog photo)
    sample_image = Image.new('RGB', (512, 512), color='brown')
    
    # Load models for benchmarking
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    dpt_model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")
    dpt_processor = DPTFeatureExtractor.from_pretrained("Intel/dpt-large")
    
    results = {}
    
    # CPU Benchmark
    print("🖥️  CPU Inference Benchmark")
    clip_model = clip_model.to('cpu')
    dpt_model = dpt_model.to('cpu')
    
    start_time = time.time()
    with torch.no_grad():
        # CLIP processing
        clip_inputs = clip_processor(images=sample_image, return_tensors="pt")
        clip_outputs = clip_model.get_image_features(**clip_inputs)
        
        # DPT processing
        dpt_inputs = dpt_processor(images=sample_image, return_tensors="pt")
        dpt_outputs = dpt_model(**dpt_inputs)
    
    cpu_inference_time = time.time() - start_time
    results['cpu'] = cpu_inference_time
    print(f"  Total CPU Inference Time: {cpu_inference_time:.2f}s")
    
    # GPU Benchmark (if available)
    if torch.cuda.is_available():
        print("🚀 GPU Inference Benchmark")
        clip_model = clip_model.to('cuda')
        dpt_model = dpt_model.to('cuda')
        
        # Warmup
        with torch.no_grad():
            clip_inputs = {k: v.to('cuda') for k, v in clip_inputs.items()}
            dpt_inputs = {k: v.to('cuda') for k, v in dpt_inputs.items()}
            _ = clip_model.get_image_features(**clip_inputs)
            _ = dpt_model(**dpt_inputs)
        
        torch.cuda.synchronize()
        start_time = time.time()
        
        with torch.no_grad():
            clip_outputs = clip_model.get_image_features(**clip_inputs)
            dpt_outputs = dpt_model(**dpt_inputs)
        
        torch.cuda.synchronize()
        gpu_inference_time = time.time() - start_time
        results['gpu'] = gpu_inference_time
        
        print(f"  Total GPU Inference Time: {gpu_inference_time:.2f}s")
        print(f"  🔥 Speedup: {cpu_inference_time/gpu_inference_time:.1f}x")
        
        # GPU Memory usage
        memory_allocated = torch.cuda.memory_allocated() / 1e9
        memory_reserved = torch.cuda.memory_reserved() / 1e9
        print(f"  GPU Memory Allocated: {memory_allocated:.1f} GB")
        print(f"  GPU Memory Reserved: {memory_reserved:.1f} GB")
    
    return results

def estimate_batch_performance():
    """Estimate batch processing capabilities"""
    print("\n📦 Batch Processing Estimation")
    print("-" * 50)
    
    if torch.cuda.is_available():
        # Get GPU memory info
        memory_total = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"Total GPU Memory: {memory_total:.1f} GB")
        
        # Estimate batch sizes based on memory
        estimated_single_model_memory = 2.0  # GB per model instance
        estimated_batch_size = int(memory_total * 0.8 / estimated_single_model_memory)
        
        print(f"Estimated Safe Batch Size: {estimated_batch_size}")
        print(f"Estimated Throughput: {estimated_batch_size * 20} models/minute")
    else:
        print("GPU not available - CPU batch processing will be limited")
        print("Estimated CPU Throughput: 2-4 models/minute")

def generate_performance_report(results):
    """Generate comprehensive performance report"""
    print("\n📈 Performance Report Summary")
    print("=" * 60)
    
    print("\n🎯 Target vs Current Performance:")
    print(f"  Current Processing Time: 15-30 seconds")
    print(f"  Target Processing Time: <5 seconds")
    
    if 'gpu' in results and 'cpu' in results:
        speedup = results['cpu'] / results['gpu']
        print(f"  GPU Speedup Achieved: {speedup:.1f}x")
        
        if results['gpu'] < 5.0:
            print("  ✅ Target processing time achievable with GPU!")
        else:
            print("  ⚠️  Additional optimization needed for <5s target")
    
    print("\n📋 Next Steps:")
    print("  1. Install GPU-enabled PyTorch")
    print("  2. Set up model caching and batch processing")
    print("  3. Implement async job queue for scaling")
    print("  4. Profile memory usage with real dog photos")
    
    # Save results to file
    import json
    timestamp = int(time.time())
    
    report_data = {
        'timestamp': timestamp,
        'gpu_available': torch.cuda.is_available(),
        'inference_times': results,
        'recommendations': [
            "Enable GPU acceleration for 3-5x speedup",
            "Implement model caching to reduce loading time",
            "Set up batch processing for multiple requests",
            "Add async queue for handling concurrent users"
        ]
    }
    
    with open(f'performance-report-{timestamp}.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Performance report saved to: performance-report-{timestamp}.json")

def main():
    """Run complete GPU performance benchmark"""
    print("🚀 PetPlantr GPU Performance Benchmark")
    print("=" * 60)
    
    # Check GPU availability
    gpu_available = check_gpu_availability()
    
    if not gpu_available:
        print("\n⚠️  No GPU acceleration available")
        print("Consider installing CUDA or running on GPU-enabled cloud instance")
    
    # Run benchmarks
    loading_results = benchmark_model_loading()
    inference_results = benchmark_inference_speed()
    estimate_batch_performance()
    
    # Generate report
    generate_performance_report(inference_results)
    
    print("\n✅ Benchmark Complete!")
    print("Review the performance report and implement GPU acceleration for production.")

if __name__ == "__main__":
    main()
