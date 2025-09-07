"""
Core Inference Engine for Breed Detection
Optimized for production deployment with caching and performance monitoring
"""

import os
import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import time
import logging
from pathlib import Path
import json
from functools import lru_cache
import psutil
import threading
from collections import defaultdict, deque

# Fast mode detection for CI/CD and development
FAST_MODE = os.getenv('PETPLANTR_FAST_MODE', 'false').lower() == 'true'

if FAST_MODE:
    # Import fast mode stub when enabled
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from fast_mode_inference_stub import FastModeInferenceStub
        _fast_mode_stub = FastModeInferenceStub()
        logging.info("Fast mode enabled - using inference stubs")
    except ImportError:
        logging.warning("Fast mode requested but stub not available, falling back to GPU")
        FAST_MODE = False

# Prometheus monitoring integration
try:
    import prometheus_client as prom
    PROMETHEUS_AVAILABLE = True
    
    # Prometheus metrics
    LAT_HIST = prom.Histogram(
        "inference_latency_seconds", 
        "Breed detection inference time",
        buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0)
    )
    
    CONFIDENCE_HIST = prom.Histogram(
        "confidence_score",
        "Breed detection confidence scores",
        buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99)
    )
    
    REQUESTS_TOTAL = prom.Counter(
        "breed_detection_requests_total",
        "Total breed detection requests",
        ["status", "breed"]
    )
    
    MEMORY_USAGE = prom.Gauge(
        "inference_memory_mb",
        "Memory usage during inference"
    )
    
    GPU_UTILIZATION = prom.Gauge(
        "inference_gpu_utilization",
        "GPU utilization during inference"
    )
    
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available. Metrics disabled.")

from ..ai.models.clip_breed import CLIPBreedDetector

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor inference performance and resource usage"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.inference_times = deque(maxlen=window_size)
        self.memory_usage = deque(maxlen=window_size)
        self.gpu_usage = deque(maxlen=window_size)
        self.accuracy_history = deque(maxlen=window_size)
        self.confidence_history = deque(maxlen=window_size)
        self.total_requests = 0
        self.error_count = 0
        self.lock = threading.Lock()
    
    def record_request(self) -> None:
        """Record that a request was served (e.g., cached hit)."""
        with self.lock:
            self.total_requests += 1
    
    def record_inference(self, 
                        inference_time: float,
                        confidence: float,
                        memory_mb: float,
                        gpu_util: float = 0.0):
        """Record inference metrics"""
        with self.lock:
            self.inference_times.append(inference_time)
            self.memory_usage.append(memory_mb)
            self.gpu_usage.append(gpu_util)
            self.confidence_history.append(confidence)
            self.total_requests += 1
    
    def record_error(self):
        """Record an error"""
        with self.lock:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        with self.lock:
            if not self.inference_times:
                return {'status': 'no_data'}
            
            return {
                'total_requests': self.total_requests,
                'error_rate': self.error_count / max(1, self.total_requests),
                'avg_inference_time': np.mean(self.inference_times),
                'p95_inference_time': np.percentile(self.inference_times, 95),
                'avg_confidence': np.mean(self.confidence_history),
                'avg_memory_mb': np.mean(self.memory_usage),
                'avg_gpu_util': np.mean(self.gpu_usage) if self.gpu_usage else 0.0,
                'throughput_rps': len(self.inference_times) / max(1, 
                    max(self.inference_times) - min(self.inference_times) + 0.001)
            }


class BreedInferenceEngine:
    """
    Production-ready inference engine for breed detection
    Features:
    - Model loading and caching
    - Performance monitoring
    - Async inference
    - Confidence calibration
    - Error handling and recovery
    """
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 device: Optional[str] = None,
                 batch_size: int = 1,
                 enable_monitoring: bool = True):
        
        self.model_path = model_path or "models/clip_breed_best.pth"
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.batch_size = batch_size
        self.enable_monitoring = enable_monitoring
        
        # Model components
        self.model: Optional[CLIPBreedDetector] = None
        self.processor = None
        self.is_loaded = False
        
        # Performance monitoring
        if enable_monitoring:
            self.performance_monitor = PerformanceMonitor()
        
        # Confidence calibration
        self.confidence_calibration = {
            'temperature': 1.0,
            'bias': 0.0,
            'enabled': True
        }
        
        # Cache for recent predictions
        self.prediction_cache = {}
        self.cache_size = 100
        
        # Model metadata
        self.model_info = {
            'version': '1.0.0',
            'accuracy': 0.95,
            'model_type': 'CLIP+LoRA',
            'num_breeds': 170
        }
        
        logger.info(f"Initialized BreedInferenceEngine on {self.device}")
    
    async def load_model(self):
        """Load the breed detection model"""
        try:
            logger.info("Loading CLIP+LoRA breed detection model...")
            
            # Create model
            self.model = CLIPBreedDetector(
                num_breeds=170,
                lora_rank=16,
                freeze_clip=True
            )
            
            # Load checkpoint if available
            if Path(self.model_path).exists():
                logger.info(f"Loading checkpoint from {self.model_path}")
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                
                # Load calibration if available
                if 'calibration' in checkpoint:
                    self.confidence_calibration.update(checkpoint['calibration'])
                
                # Update model info
                if 'model_info' in checkpoint:
                    self.model_info.update(checkpoint['model_info'])
            else:
                logger.warning(f"No checkpoint found at {self.model_path}, using untrained model")
            
            # Move to device and set to eval mode
            self.model.to(self.device)
            self.model.eval()
            
            # Get processor
            self.processor = self.model.processor
            
            self.is_loaded = True
            logger.info("Model loaded successfully")
            
            # Warm up model with dummy input
            await self._warmup_model()
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise e
    
    async def _warmup_model(self):
        """Warm up model with dummy input"""
        try:
            dummy_image = Image.new('RGB', (224, 224), color='red')
            await self.predict(dummy_image, use_tta=False)
            logger.info("Model warmed up successfully")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    async def predict(self, 
                     image: Image.Image,
                     use_tta: bool = True,
                     confidence_threshold: float = 0.8,
                     top_k: int = 5) -> Dict[str, Any]:
        """
        Run breed prediction on image
        """
        # Fast mode override for CI/CD and development
        if FAST_MODE:
            return _fast_mode_stub.predict_breed(
                image_bytes=None,  # Stub doesn't need actual image
                confidence_threshold=confidence_threshold,
                use_tta=use_tta
            )
        
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(image, use_tta, confidence_threshold)
            
            # Check cache
            if cache_key in self.prediction_cache:
                logger.debug("Cache hit for prediction")
                cached = self.prediction_cache[cache_key]
                # Record that we served a request, even if cached
                if self.enable_monitoring:
                    memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                    gpu_util = self._get_gpu_utilization()
                    self.performance_monitor.record_request()
                    self.performance_monitor.record_inference(
                        inference_time=0.0,  # cached path
                        confidence=cached.get('confidence', 0.0),
                        memory_mb=memory_mb,
                        gpu_util=gpu_util,
                    )
                return cached
            
            # Preprocess image
            processed_image = await self._preprocess_image(image)
            
            # Run inference
            if use_tta:
                results = await self._predict_with_tta(processed_image, confidence_threshold, top_k)
            else:
                results = await self._predict_single(processed_image, confidence_threshold, top_k)
            
            # Apply confidence calibration
            if self.confidence_calibration['enabled']:
                results['confidence'] = self._calibrate_confidence(results['confidence'])
                results['is_high_confidence'] = results['confidence'] >= confidence_threshold
            
            # Add metadata
            results.update({
                'model_version': self.model_info['version'],
                'inference_time': time.time() - start_time,
                'used_tta': use_tta,
                'device': self.device
            })
            
            # Cache result
            if len(self.prediction_cache) >= self.cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self.prediction_cache))
                del self.prediction_cache[oldest_key]
            self.prediction_cache[cache_key] = results
            
            # Record performance metrics
            if self.enable_monitoring:
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                gpu_util = self._get_gpu_utilization()
                self.performance_monitor.record_inference(
                    inference_time=results['inference_time'],
                    confidence=results['confidence'],
                    memory_mb=memory_mb,
                    gpu_util=gpu_util
                )
                
                # Record Prometheus metrics
                if PROMETHEUS_AVAILABLE:
                    LAT_HIST.observe(results['inference_time'])
                    CONFIDENCE_HIST.observe(results['confidence'])
                    MEMORY_USAGE.set(memory_mb)
                    GPU_UTILIZATION.set(gpu_util)
                    REQUESTS_TOTAL.labels(status="success", breed=results['predicted_breed']).inc()
            
            return results
            
        except Exception as e:
            if self.enable_monitoring:
                self.performance_monitor.record_error()
            logger.error(f"Prediction failed: {e}")
            raise e
    
    async def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for model input"""
        
        # Resize if too large
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Process with CLIP processor
        inputs = self.processor(images=image, return_tensors="pt")
        pixel_values = inputs['pixel_values'].to(self.device)
        
        return pixel_values
    
    async def _predict_single(self, 
                             image_tensor: torch.Tensor,
                             confidence_threshold: float,
                             top_k: int) -> Dict[str, Any]:
        """Single inference without TTA"""
        
        with torch.no_grad():
            outputs = self.model(image_tensor)
            
            probs = outputs['probabilities'][0]  # Remove batch dimension
            confidence = outputs['confidence'][0].item()
            
            # Get top-k predictions
            top_probs, top_indices = torch.topk(probs, k=min(top_k, len(probs)))
            
            results = {
                'predicted_breed': self.model.breed_names[top_indices[0].item()],
                'confidence': confidence,
                'top_predictions': [
                    {
                        'breed': self.model.breed_names[idx.item()],
                        'probability': prob.item()
                    }
                    for idx, prob in zip(top_indices, top_probs)
                ],
                'is_high_confidence': confidence >= confidence_threshold
            }
            
            return results
    
    async def _predict_with_tta(self, 
                               image_tensor: torch.Tensor,
                               confidence_threshold: float,
                               top_k: int) -> Dict[str, Any]:
        """Prediction with Test-Time Augmentation"""
        
        # Use model's built-in TTA method
        result = self.model.predict_with_tta(
            image=image_tensor[0],  # Remove batch dimension
            confidence_threshold=confidence_threshold
        )
        
        # Ensure we return top_k predictions
        if len(result['top_5_predictions']) < top_k:
            # Pad with additional predictions if needed
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probs = outputs['probabilities'][0]
                top_probs, top_indices = torch.topk(probs, k=top_k)
                
                result['top_predictions'] = [
                    {
                        'breed': self.model.breed_names[idx.item()],
                        'probability': prob.item()
                    }
                    for idx, prob in zip(top_indices, top_probs)
                ]
        else:
            result['top_predictions'] = result['top_5_predictions'][:top_k]
        
        return result
    
    def _calibrate_confidence(self, confidence: float) -> float:
        """Apply confidence calibration"""
        calibrated = (confidence - self.confidence_calibration['bias']) / self.confidence_calibration['temperature']
        return np.clip(calibrated, 0.0, 1.0)
    
    def _generate_cache_key(self, 
                           image: Image.Image, 
                           use_tta: bool, 
                           confidence_threshold: float) -> str:
        """Generate cache key for prediction"""
        # Simple hash based on image size and parameters
        image_hash = hash((image.size, image.mode, use_tta, confidence_threshold))
        return str(abs(image_hash))
    
    def _get_gpu_utilization(self) -> float:
        """Get GPU utilization if available"""
        try:
            if torch.cuda.is_available():
                return torch.cuda.utilization() / 100.0
            return 0.0
        except:
            return 0.0
    
    def get_supported_breeds(self) -> List[str]:
        """Get list of supported breeds"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        return self.model.breed_names
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        info = self.model_info.copy()
        if self.is_loaded:
            info.update(self.model.get_model_info())
        return info
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.enable_monitoring:
            return {'monitoring': 'disabled'}
        return self.performance_monitor.get_metrics()
    
    async def update_calibration(self, calibration_data: List[Dict[str, Any]]):
        """Update confidence calibration based on validation data"""
        try:
            logger.info("Updating confidence calibration...")
            
            confidences = []
            accuracies = []
            
            for item in calibration_data:
                confidences.append(item['confidence'])
                accuracies.append(item['accuracy'])
            
            # Compute optimal temperature using Platt scaling
            if len(confidences) > 10:
                from sklearn.linear_model import LogisticRegression
                
                confidences = np.array(confidences).reshape(-1, 1)
                accuracies = np.array(accuracies)
                
                # Fit logistic regression for calibration
                lr = LogisticRegression()
                lr.fit(confidences, accuracies)
                
                # Update calibration parameters
                self.confidence_calibration['temperature'] = 1.0 / lr.coef_[0][0]
                self.confidence_calibration['bias'] = -lr.intercept_[0] / lr.coef_[0][0]
                
                logger.info(f"Updated calibration: temp={self.confidence_calibration['temperature']:.3f}, "
                           f"bias={self.confidence_calibration['bias']:.3f}")
            
        except Exception as e:
            logger.error(f"Calibration update failed: {e}")


# Global inference engine instance
_inference_engine: Optional[BreedInferenceEngine] = None


async def get_inference_engine() -> BreedInferenceEngine:
    """Get or create global inference engine"""
    global _inference_engine
    
    if _inference_engine is None:
        _inference_engine = BreedInferenceEngine()
        await _inference_engine.load_model()
    
    return _inference_engine


async def generate_breed(image: Image.Image, use_tta: bool = True) -> Dict[str, Any]:
    """
    Generate breed prediction with Prometheus monitoring
    Main entry point for breed detection API
    """
    if PROMETHEUS_AVAILABLE:
        # Use Prometheus histogram to time the operation
        with LAT_HIST.time():
            result = await _generate_breed_internal(image, use_tta)
    else:
        result = await _generate_breed_internal(image, use_tta)
    
    return result


async def _generate_breed_internal(image: Image.Image, use_tta: bool = True) -> Dict[str, Any]:
    """Internal breed generation with monitoring"""
    start_time = time.time()
    
    try:
        # Get inference engine
        engine = await get_inference_engine()
        
        # Run prediction
        result = await engine.predict(
            image=image,
            use_tta=use_tta,
            confidence_threshold=0.8,
            top_k=5
        )
        
        # Record metrics
        inference_time = time.time() - start_time
        confidence = result.get('confidence', 0.0)
        predicted_breed = result.get('predicted_breed', 'unknown')
        
        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            CONFIDENCE_HIST.observe(confidence)
            REQUESTS_TOTAL.labels(status='success', breed=predicted_breed).inc()
            
            # Memory and GPU metrics
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            MEMORY_USAGE.set(memory_mb)
            
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                GPU_UTILIZATION.set(gpu_util)
            except:
                pass  # GPU monitoring optional
        
        # Add performance metadata
        result.update({
            'processing_time': inference_time,
            'model_version': '2.0.0',
            'metadata': {
                'used_tta': use_tta,
                'image_size': list(image.size),
                'processing_time_ms': int(inference_time * 1000),
                'gpu_used': torch.cuda.is_available(),
                'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
            }
        })
        
        return result
        
    except Exception as e:
        # Record error
        if PROMETHEUS_AVAILABLE:
            REQUESTS_TOTAL.labels(status='error', breed='unknown').inc()
        
        logger.error(f"Breed generation failed: {e}")
        raise e
