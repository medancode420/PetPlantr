"""
Breed Detection API Route
High-performance endpoint with confidence scoring and TTA
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
import torch
from PIL import Image
import io
import base64
import numpy as np
from typing import Dict, List, Optional, Any
import logging
import time
from pydantic import BaseModel
from pydantic import field_validator, model_validator

from src.ai.models.clip_breed import CLIPBreedDetector
from ...core.inference import BreedInferenceEngine

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/breed", tags=["breed-detection"])

# Global inference engine (loaded once)
inference_engine: Optional[BreedInferenceEngine] = None


class BreedDetectionRequest(BaseModel):
    """Request model for breed detection"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    use_tta: bool = True
    confidence_threshold: float = 0.8
    return_top_k: int = 5

    @field_validator("image_base64")
    @classmethod
    def validate_base64(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            data = v
            if data.startswith("data:image"):
                data = data.split(",", 1)[1]
            # Validate strict base64
            base64.b64decode(data, validate=True)
            return v
        except Exception as e:
            raise ValueError(f"Invalid base64 image: {e}")

    @model_validator(mode="after")
    def check_any_source(self):
        if not self.image_url and not self.image_base64:
            raise ValueError("Either image_url or image_base64 must be provided")
        return self


class BreedDetectionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    """Response model for breed detection"""
    predicted_breed: str
    confidence: float
    processing_time: float
    top_predictions: List[Dict[str, float]]
    is_high_confidence: bool
    model_version: str
    metadata: Dict[str, Any]


@router.on_event("startup")
async def load_breed_model():
    """Load breed detection model on startup"""
    global inference_engine
    
    try:
        logger.info("Loading CLIP+LoRA breed detection model...")
        inference_engine = BreedInferenceEngine()
        await inference_engine.load_model()
        logger.info("Breed detection model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load breed detection model: {e}")
        raise e


@router.get("/health")
async def health_check():
    """Health check for breed detection service"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "status": "healthy",
        "model_loaded": True,
        "model_info": inference_engine.get_model_info()
    }


@router.post("/detect", response_model=BreedDetectionResponse)
async def detect_breed(request: BreedDetectionRequest):
    """
    Detect dog breed from image with high accuracy
    Supports both URL and base64 image inputs
    """
    start_time = time.time()
    
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Load image
        image = await _load_image(request.image_url, request.image_base64)
        
        # Run inference
        results = await inference_engine.predict(
            image=image,
            use_tta=request.use_tta,
            confidence_threshold=request.confidence_threshold,
            top_k=request.return_top_k
        )
        
        processing_time = time.time() - start_time
        
        # Format response
        response = BreedDetectionResponse(
            predicted_breed=results['predicted_breed'],
            confidence=results['confidence'],
            processing_time=processing_time,
            top_predictions=results['top_predictions'][:request.return_top_k],
            is_high_confidence=results['is_high_confidence'],
            model_version=results['model_version'],
            metadata={
                'used_tta': request.use_tta,
                'image_size': image.size,
                'processing_time_ms': processing_time * 1000,
                'gpu_used': torch.cuda.is_available()
            }
        )
        
        logger.info(f"Breed detection completed: {results['predicted_breed']} "
                   f"(confidence: {results['confidence']:.3f}, time: {processing_time:.3f}s)")
        
        return response
        
    except Exception as e:
        logger.error(f"Breed detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-file")
async def detect_breed_from_file(
    file: UploadFile = File(...),
    use_tta: bool = True,
    confidence_threshold: float = 0.8,
    top_k: int = 5
):
    """
    Detect breed from uploaded file
    """
    start_time = time.time()
    
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Run inference
        results = await inference_engine.predict(
            image=image,
            use_tta=use_tta,
            confidence_threshold=confidence_threshold,
            top_k=top_k
        )
        
        processing_time = time.time() - start_time
        
        # Add metadata
        results['metadata'] = {
            'filename': file.filename,
            'file_size': len(image_data),
            'image_size': image.size,
            'processing_time_ms': processing_time * 1000,
            'used_tta': use_tta
        }
        
        return JSONResponse(results)
        
    except Exception as e:
        logger.error(f"File-based breed detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/batch-detect")
async def batch_detect_breeds(
    requests: List[BreedDetectionRequest],
    background_tasks: BackgroundTasks
):
    """
    Batch breed detection for multiple images
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Batch size limited to 10 images")
    
    try:
        results = []
        for i, request in enumerate(requests):
            try:
                image = await _load_image(request.image_url, request.image_base64)
                
                result = await inference_engine.predict(
                    image=image,
                    use_tta=request.use_tta,
                    confidence_threshold=request.confidence_threshold,
                    top_k=request.return_top_k
                )
                
                result['batch_index'] = i
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch detection failed for image {i}: {e}")
                results.append({
                    'batch_index': i,
                    'error': str(e),
                    'predicted_breed': None,
                    'confidence': 0.0
                })
        
        return {'results': results, 'total_processed': len(results)}
        
    except Exception as e:
        logger.error(f"Batch breed detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch detection failed: {str(e)}")


@router.get("/breeds")
async def get_supported_breeds():
    """Get list of supported dog breeds"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        'breeds': inference_engine.get_supported_breeds(),
        'total_breeds': len(inference_engine.get_supported_breeds()),
        'model_version': inference_engine.get_model_info()['model_version']
    }


@router.get("/model-info")
async def get_model_info():
    """Get detailed model information"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return inference_engine.get_model_info()


@router.post("/calibrate")
async def calibrate_confidence(
    calibration_data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks
):
    """
    Recalibrate confidence scores based on validation data
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Add calibration task to background
    background_tasks.add_task(
        inference_engine.update_calibration,
        calibration_data
    )
    
    return {
        'status': 'calibration_started',
        'message': 'Confidence calibration running in background'
    }


async def _load_image(image_url: Optional[str] = None, 
                     image_base64: Optional[str] = None) -> Image.Image:
    """Load image from URL or base64 data"""
    
    if image_base64:
        try:
            # Handle base64 data URLs
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]
            
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")
            
    elif image_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load image from URL: {e}")
    else:
        raise HTTPException(status_code=400, detail="Either image_url or image_base64 must be provided")
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Validate image size
    if image.size[0] * image.size[1] > 5000 * 5000:
        raise HTTPException(status_code=400, detail="Image too large (max 5000x5000)")
    
    return image


# Performance monitoring
@router.get("/metrics")
async def get_performance_metrics():
    """Get performance metrics for breed detection"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return inference_engine.get_performance_metrics()
