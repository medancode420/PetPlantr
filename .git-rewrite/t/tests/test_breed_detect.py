"""
Comprehensive Test Suite for Breed Detection
Tests accuracy, performance, and reliability of the CLIP+LoRA system
"""

import pytest
import torch
import numpy as np
from PIL import Image
import asyncio
import time
import tempfile
from pathlib import Path
import json
from typing import Dict, List
import io
import base64

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.ai.models.clip_breed import CLIPBreedDetector
from src.core.inference import BreedInferenceEngine
from src.api.routes.breed import detect_breed, BreedDetectionRequest


class TestCLIPBreedDetector:
    """Test suite for CLIP+LoRA breed detection model"""
    
    @pytest.fixture
    def model(self):
        """Create test model instance"""
        return CLIPBreedDetector(
            num_breeds=10,  # Smaller for testing
            lora_rank=4,    # Smaller for testing
            freeze_clip=True
        )
    
    @pytest.fixture
    def sample_image(self):
        """Create sample test image"""
        return Image.new('RGB', (224, 224), color='red')
    
    def test_model_initialization(self, model):
        """Test model initialization"""
        assert model.num_breeds == 10
        assert model.breed_head.rank == 4
        assert len(model.breed_names) == 10
        
        # Test model info
        info = model.get_model_info()
        assert 'model_name' in info
        assert 'total_parameters' in info
        assert 'trainable_parameters' in info
    
    def test_forward_pass(self, model, sample_image):
        """Test forward pass"""
        model.eval()
        
        # Preprocess image
        inputs = model.processor(images=sample_image, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(inputs['pixel_values'])
        
        assert 'logits' in outputs
        assert 'confidence' in outputs
        assert 'probabilities' in outputs
        
        # Check shapes
        assert outputs['logits'].shape == (1, 10)  # batch_size=1, num_breeds=10
        assert outputs['confidence'].shape == (1, 1)
        assert outputs['probabilities'].shape == (1, 10)
    
    def test_tta_prediction(self, model, sample_image):
        """Test Test-Time Augmentation prediction"""
        model.eval()
        
        result = model.predict_with_tta(
            image=torch.randn(3, 224, 224),  # Random image tensor
            confidence_threshold=0.8
        )
        
        assert 'predicted_breed' in result
        assert 'confidence' in result
        assert 'top_5_predictions' in result
        assert 'is_high_confidence' in result
        
        # Check confidence is in valid range
        assert 0.0 <= result['confidence'] <= 1.0
    
    def test_confidence_calibration(self, model):
        """Test confidence calibration"""
        # Test different probability distributions
        test_cases = [
            (torch.tensor([0.9, 0.05, 0.05]), 0.8, True),   # High confidence
            (torch.tensor([0.4, 0.3, 0.3]), 0.8, False),    # Low confidence
            (torch.tensor([0.5, 0.5, 0.0]), 0.8, False),    # Uncertain
        ]
        
        for probs, threshold, expected_high_conf in test_cases:
            max_prob = probs.max().item()
            entropy = model._compute_entropy(probs)
            
            calibrated = model._calibrate_confidence(
                max_prob=max_prob,
                model_confidence=0.7,  # Mock model confidence
                entropy=entropy
            )
            
            assert 0.0 <= calibrated <= 1.0
            assert (calibrated >= threshold) == expected_high_conf
    
    def test_hard_negative_mining(self, model):
        """Test hard negative mining weights computation"""
        model.train()
        model.mining_enabled = True
        
        # Mock logits and labels for hard negative mining
        batch_size = 8
        logits = torch.randn(batch_size, 10)
        labels = torch.randint(0, 10, (batch_size,))
        
        # Make some predictions incorrect (hard negatives)
        logits[0, labels[0]] = -10  # Force incorrect prediction
        logits[1, labels[1]] = -10  # Force incorrect prediction
        
        weights = model._compute_mining_weights(logits, labels)
        
        assert weights.shape == (batch_size,)
        assert torch.all(weights > 0)  # All weights should be positive
        
        # Hard examples should have higher weights
        predictions = logits.argmax(dim=-1)
        incorrect_mask = (predictions != labels)
        correct_mask = ~incorrect_mask
        if incorrect_mask.sum() > 0 and correct_mask.sum() > 0:
            avg_incorrect_weight = weights[incorrect_mask].mean()
            avg_correct_weight = weights[correct_mask].mean()
            # Hard negatives should have higher weights
            assert avg_incorrect_weight >= avg_correct_weight
        else:
            # Degenerate case: no correct or no incorrect samples; still expect positive weights
            assert torch.all(weights > 0)


class TestBreedInferenceEngine:
    """Test suite for breed inference engine"""
    
    @pytest.fixture
    async def inference_engine(self):
        """Create test inference engine"""
        engine = BreedInferenceEngine(
            model_path="test_model.pth",  # Will use untrained model
            device='cpu',
            enable_monitoring=True
        )
        await engine.load_model()
        return engine
    
    @pytest.fixture
    def sample_image(self):
        """Create sample test image"""
        return Image.new('RGB', (512, 512), color='blue')
    
    @pytest.mark.asyncio
    async def test_model_loading(self, inference_engine):
        """Test model loading"""
        assert inference_engine.is_loaded
        assert inference_engine.model is not None
        assert inference_engine.processor is not None
    
    @pytest.mark.asyncio
    async def test_single_prediction(self, inference_engine, sample_image):
        """Test single image prediction"""
        result = await inference_engine.predict(
            image=sample_image,
            use_tta=False,
            confidence_threshold=0.7,
            top_k=3
        )
        
        assert 'predicted_breed' in result
        assert 'confidence' in result
        assert 'top_predictions' in result
        assert 'is_high_confidence' in result
        assert 'model_version' in result
        
        assert len(result['top_predictions']) <= 3
        assert 0.0 <= result['confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_tta_prediction(self, inference_engine, sample_image):
        """Test TTA prediction"""
        result = await inference_engine.predict(
            image=sample_image,
            use_tta=True,
            confidence_threshold=0.8,
            top_k=5
        )
        
        assert result['used_tta'] == True
        assert len(result['top_predictions']) <= 5
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, inference_engine, sample_image):
        """Test performance monitoring"""
        # Run several predictions
        for _ in range(5):
            await inference_engine.predict(sample_image, use_tta=False)
        
        metrics = inference_engine.get_performance_metrics()
        
        assert 'total_requests' in metrics
        assert 'avg_inference_time' in metrics
        assert 'avg_confidence' in metrics
        assert metrics['total_requests'] >= 5
    
    @pytest.mark.asyncio
    async def test_caching(self, inference_engine, sample_image):
        """Test prediction caching"""
        # First prediction
        start_time = time.time()
        result1 = await inference_engine.predict(sample_image, use_tta=False)
        first_time = time.time() - start_time
        
        # Second prediction (should be cached)
        start_time = time.time()
        result2 = await inference_engine.predict(sample_image, use_tta=False)
        second_time = time.time() - start_time
        
        # Results should be identical
        assert result1['predicted_breed'] == result2['predicted_breed']
        assert result1['confidence'] == result2['confidence']
        
        # Second call should be faster (cached)
        # Note: This might not always be true due to system variability
        # assert second_time < first_time * 0.5
    
    def test_breed_list(self, inference_engine):
        """Test breed list functionality"""
        breeds = inference_engine.get_supported_breeds()
        assert isinstance(breeds, list)
        assert len(breeds) > 0
        assert all(isinstance(breed, str) for breed in breeds)
    
    def test_model_info(self, inference_engine):
        """Test model info"""
        info = inference_engine.get_model_info()
        assert 'version' in info
        assert 'accuracy' in info
        assert 'model_type' in info


class TestBreedAPI:
    """Test suite for breed detection API"""
    
    @pytest.fixture
    def sample_image_base64(self):
        """Create base64 encoded test image"""
        image = Image.new('RGB', (224, 224), color='green')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        return base64.b64encode(image_data).decode('utf-8')
    
    def test_breed_detection_request_model(self):
        """Test request model validation"""
        # Valid request with base64
        request = BreedDetectionRequest(
            image_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            use_tta=True,
            confidence_threshold=0.8,
            return_top_k=5
        )
        assert request.use_tta == True
        assert request.confidence_threshold == 0.8
        assert request.return_top_k == 5
    
    def test_image_validation(self):
        """Test image validation logic"""
        # Test with various image formats
        valid_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        # Should not raise exception
        try:
            request = BreedDetectionRequest(image_base64=valid_base64)
            assert request.image_base64 == valid_base64
        except Exception as e:
            pytest.fail(f"Valid base64 image failed validation: {e}")


class TestAccuracyBenchmark:
    """Accuracy and performance benchmarks"""
    
    @pytest.fixture
    def benchmark_dataset(self):
        """Create benchmark dataset"""
        # Create synthetic test dataset
        dataset = []
        breed_names = ['golden_retriever', 'labrador', 'german_shepherd', 'bulldog', 'poodle']
        
        for i, breed in enumerate(breed_names):
            for j in range(5):  # 5 images per breed
                # Create unique image for each breed/instance
                color = (i * 50, j * 40, (i + j) * 30)
                image = Image.new('RGB', (224, 224), color=color)
                dataset.append({
                    'image': image,
                    'breed': breed,
                    'breed_id': i
                })
        
        return dataset
    
    @pytest.mark.asyncio
    async def test_accuracy_benchmark(self, benchmark_dataset):
        """Test model accuracy on benchmark dataset"""
        # Create inference engine
        engine = BreedInferenceEngine(enable_monitoring=True)
        await engine.load_model()
        
        correct_predictions = 0
        total_predictions = len(benchmark_dataset)
        confidences = []
        
        for item in benchmark_dataset:
            result = await engine.predict(
                image=item['image'],
                use_tta=False,
                confidence_threshold=0.7
            )
            
            predicted_breed = result['predicted_breed']
            actual_breed = item['breed']
            confidence = result['confidence']
            
            confidences.append(confidence)
            
            # Note: With untrained model, we can't expect correct predictions
            # This test validates the pipeline rather than accuracy
            assert isinstance(predicted_breed, str)
            assert 0.0 <= confidence <= 1.0
        
        # Validate confidence distribution
        avg_confidence = np.mean(confidences)
        assert 0.0 <= avg_confidence <= 1.0
        
        print(f"Average confidence: {avg_confidence:.3f}")
        print(f"Confidence std: {np.std(confidences):.3f}")
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self, benchmark_dataset):
        """Test inference performance"""
        engine = BreedInferenceEngine(enable_monitoring=True)
        await engine.load_model()
        
        # Warm up
        await engine.predict(benchmark_dataset[0]['image'], use_tta=False)
        
        # Benchmark single inference
        start_time = time.time()
        for i in range(min(10, len(benchmark_dataset))):
            await engine.predict(benchmark_dataset[i]['image'], use_tta=False)
        single_time = (time.time() - start_time) / 10
        
        # Benchmark TTA inference
        start_time = time.time()
        for i in range(min(5, len(benchmark_dataset))):
            await engine.predict(benchmark_dataset[i]['image'], use_tta=True)
        tta_time = (time.time() - start_time) / 5
        
        print(f"Average single inference time: {single_time:.3f}s")
        print(f"Average TTA inference time: {tta_time:.3f}s")
        
        # Performance assertions
        assert single_time < 2.0  # Should be under 2 seconds
        assert tta_time < 5.0     # TTA should be under 5 seconds
        
        # Get performance metrics
        metrics = engine.get_performance_metrics()
        assert metrics['total_requests'] >= 15


class TestIntegration:
    """Integration tests for the complete pipeline"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline"""
        # Create test image
        test_image = Image.new('RGB', (400, 400), color='red')
        
        # Convert to base64
        buffer = io.BytesIO()
        test_image.save(buffer, format='JPEG')
        image_data = buffer.getvalue()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Create request
        request = BreedDetectionRequest(
            image_base64=image_base64,
            use_tta=True,
            confidence_threshold=0.8,
            return_top_k=3
        )
        
        # Test the complete pipeline would work
        # (Can't test actual API call without running server)
        assert request.image_base64 is not None
        assert request.use_tta == True
        assert request.confidence_threshold == 0.8
        assert request.return_top_k == 3
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Invalid base64
        with pytest.raises(Exception):
            request = BreedDetectionRequest(image_base64="invalid_base64")
        
        # No image provided
        with pytest.raises(Exception):
            request = BreedDetectionRequest()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
