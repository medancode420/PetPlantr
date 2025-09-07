#!/usr/bin/env python3
"""
Fast Mode GPU Inference Stub
Provides realistic JSON responses for development testing without GPU requirements
"""

import json
import time
import random
from typing import Dict, List, Any

class FastModeInferenceStub:
    """CPU-based stub that mimics GPU inference patterns"""
    
    def __init__(self):
        self.model_loaded = True
        self.response_templates = self._load_response_templates()
    
    def _load_response_templates(self) -> Dict[str, Any]:
        """Load realistic response templates based on production patterns"""
        return {
            "high_confidence": {
                "predicted_breed": "golden_retriever",
                "confidence": 0.92,
                "processing_time": 0.245,
                "top_predictions": [
                    {"breed": "golden_retriever", "probability": 0.92},
                    {"breed": "labrador_retriever", "probability": 0.05},
                    {"breed": "nova_scotia_duck_tolling_retriever", "probability": 0.02}
                ],
                "is_high_confidence": True,
                "model_version": "2.0.0-stub",
                "metadata": {
                    "used_tta": True,
                    "image_size": [512, 512],
                    "processing_time_ms": 245,
                    "gpu_used": False,  # Stub mode
                    "memory_mb": 512,   # Much lower for CPU
                    "fast_mode": True
                }
            },
            "medium_confidence": {
                "predicted_breed": "mixed_breed",
                "confidence": 0.78,
                "processing_time": 0.189,
                "top_predictions": [
                    {"breed": "mixed_breed", "probability": 0.78},
                    {"breed": "shepherd_mix", "probability": 0.15},
                    {"breed": "labrador_mix", "probability": 0.07}
                ],
                "is_high_confidence": False,
                "model_version": "2.0.0-stub",
                "metadata": {
                    "used_tta": True,
                    "image_size": [512, 512],
                    "processing_time_ms": 189,
                    "gpu_used": False,
                    "memory_mb": 512,
                    "fast_mode": True
                }
            },
            "low_confidence": {
                "predicted_breed": "unknown",
                "confidence": 0.45,
                "processing_time": 0.234,
                "top_predictions": [
                    {"breed": "unknown", "probability": 0.45},
                    {"breed": "mixed_breed", "probability": 0.35},
                    {"breed": "other", "probability": 0.20}
                ],
                "is_high_confidence": False,
                "model_version": "2.0.0-stub",
                "metadata": {
                    "used_tta": True,
                    "image_size": [512, 512],
                    "processing_time_ms": 234,
                    "gpu_used": False,
                    "memory_mb": 512,
                    "fast_mode": True
                }
            }
        }
    
    def predict_breed(self, image_data: bytes, use_tta: bool = True) -> Dict[str, Any]:
        """
        Stub breed prediction that mimics realistic response patterns
        
        Args:
            image_data: Image bytes (analyzed for realistic variation)
            use_tta: Test time augmentation flag
            
        Returns:
            Realistic breed detection response
        """
        # Simulate processing time (much faster than GPU)
        start_time = time.time()
        
        # Add small realistic delay
        time.sleep(random.uniform(0.05, 0.15))  # 50-150ms vs 200-500ms GPU
        
        # Determine response type based on image characteristics
        image_size = len(image_data)
        response_type = self._determine_response_type(image_size)
        
        # Get base response template
        response = self.response_templates[response_type].copy()
        
        # Add realistic variations
        response = self._add_realistic_variations(response, use_tta)
        
        # Calculate actual processing time
        actual_processing_time = time.time() - start_time
        response["processing_time"] = round(actual_processing_time, 3)
        response["metadata"]["processing_time_ms"] = int(actual_processing_time * 1000)
        
        return response
    
    def _determine_response_type(self, image_size: int) -> str:
        """Determine response confidence based on image characteristics"""
        if image_size > 100000:  # Large, likely high-quality image
            return "high_confidence"
        elif image_size > 10000:  # Medium size image
            return "medium_confidence"
        else:  # Small or test image
            return "low_confidence"
    
    def _add_realistic_variations(self, response: Dict[str, Any], use_tta: bool) -> Dict[str, Any]:
        """Add realistic variations to make responses feel authentic"""
        
        # Vary confidence slightly
        base_confidence = response["confidence"]
        confidence_variation = random.uniform(-0.03, 0.03)
        response["confidence"] = max(0.0, min(1.0, base_confidence + confidence_variation))
        
        # Update top predictions confidence
        if response["top_predictions"]:
            response["top_predictions"][0]["probability"] = response["confidence"]
            
            # Redistribute remaining probability
            remaining = 1.0 - response["confidence"]
            for i, pred in enumerate(response["top_predictions"][1:], 1):
                pred["probability"] = remaining / (len(response["top_predictions"]) - 1)
        
        # Update high confidence flag
        response["is_high_confidence"] = response["confidence"] >= 0.8
        
        # Vary processing time slightly
        time_variation = random.uniform(0.9, 1.1)
        response["processing_time"] = round(response["processing_time"] * time_variation, 3)
        response["metadata"]["processing_time_ms"] = int(response["processing_time"] * 1000)
        
        # Update TTA usage
        response["metadata"]["used_tta"] = use_tta
        
        return response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return model information for stub mode"""
        return {
            "model_version": "2.0.0-stub",
            "model_type": "FastModeStub",
            "gpu_used": False,
            "fast_mode": True,
            "capabilities": [
                "breed_detection",
                "confidence_scoring", 
                "multi_prediction",
                "tta_support"
            ],
            "performance": {
                "avg_latency_ms": 100,
                "memory_mb": 512,
                "throughput_rps": 50
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for stub mode"""
        return {
            "status": "healthy",
            "model_loaded": True,
            "fast_mode": True,
            "timestamp": time.time(),
            "uptime_seconds": random.randint(100, 10000)
        }

# Example usage for testing
if __name__ == "__main__":
    stub = FastModeInferenceStub()
    
    # Test with different image sizes
    test_cases = [
        b"large_image_data" * 10000,  # Large image
        b"medium_image" * 1000,       # Medium image  
        b"small"                      # Small image
    ]
    
    print("Fast Mode Inference Stub Test Results:")
    print("=" * 50)
    
    for i, image_data in enumerate(test_cases):
        result = stub.predict_breed(image_data)
        print(f"\nTest {i+1} (size: {len(image_data)} bytes):")
        print(f"  Breed: {result['predicted_breed']}")
        print(f"  Confidence: {result['confidence']:.3f}")
        print(f"  Processing: {result['processing_time']*1000:.1f}ms")
        print(f"  High Confidence: {result['is_high_confidence']}")
    
    print(f"\nModel Info:")
    model_info = stub.get_model_info()
    print(f"  Version: {model_info['model_version']}")
    print(f"  Performance: {model_info['performance']['avg_latency_ms']}ms avg")
    
    print(f"\nHealth Check:")
    health = stub.health_check()
    print(f"  Status: {health['status']}")
    print(f"  Fast Mode: {health['fast_mode']}")
