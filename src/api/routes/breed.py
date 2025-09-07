"""
Breed Detection API Route
High-performance endpoint with confidence scoring and TTA
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
import io
import base64
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import importlib
import logging
import time
from pydantic import BaseModel
from pydantic import field_validator, model_validator

from ...core.settings import get_flag, get_int
from ...services import breed_detection as svc
import asyncio

# Optional torch import to avoid hard dependency at import time
try:
    import torch  # type: ignore
    def _cuda_available() -> bool:
        try:
            if torch is None:  # type: ignore
                return False
            return bool(torch.cuda.is_available())  # type: ignore[attr-defined]
        except Exception:
            return False
except Exception:  # torch not installed
    torch = None  # type: ignore
    def _cuda_available() -> bool:
        return False

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/breed", tags=["breed-detection"])

# No global engine here; service manages its own model state


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
            # Enforce max base64 payload size (bytes after decoding)
            max_bytes = get_int("MAX_BASE64_BYTES", 8 * 1024 * 1024)
            if len(data) * 3 // 4 > max_bytes:
                raise ValueError("base64 image too large")
            return v
        except Exception as e:
            raise ValueError(f"Invalid base64 image: {e}")

    @model_validator(mode="after")
    def check_any_source(self):
        if not self.image_url and not self.image_base64:
            raise ValueError("Either image_url or image_base64 must be provided")
        # Validate thresholds
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        if not (1 <= self.return_top_k <= 20):
            raise ValueError("return_top_k must be between 1 and 20")
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


# Model is loaded in app lifespan via service; routes check flag + load status


@router.get("/health")
async def health_check():
    """Health check for breed detection service"""
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "status": "healthy",
        "model_loaded": True,
    "model_info": svc.get_model_info()
    }


@router.post("/detect", response_model=BreedDetectionResponse)
async def detect_breed(request: BreedDetectionRequest):
    """
    Detect dog breed from image with high accuracy
    Supports both URL and base64 image inputs
    """
    start_time = time.time()
    
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Load image
        image = await _load_image(request.image_url, request.image_base64)

        # Run inference
        results = await svc.predict(
            image=image,
            confidence_threshold=request.confidence_threshold,
            top_k=request.return_top_k,
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
                'gpu_used': _cuda_available(),
            },
        )

        logger.info(
            f"Breed detection completed: {results['predicted_breed']} "
            f"(confidence: {results['confidence']:.3f}, time: {processing_time:.3f}s)"
        )

        return response

    except HTTPException:
        # Preserve service-layer HTTP errors (e.g., 503 busy)
        raise
    except Exception as e:
        logger.error(f"Breed detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-file")
async def detect_breed_from_file(
    file: UploadFile = File(...),
    use_tta: bool = True,
    confidence_threshold: float = 0.8,
    top_k: int = 5,
):
    """Detect breed from uploaded file."""
    start_time = time.time()

    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read and process image
        image_data = await file.read()
        # Lazy import PIL via importlib to avoid static import errors
        _PILImage = importlib.import_module("PIL.Image")
        image = _PILImage.open(io.BytesIO(image_data))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Run inference
        results = await svc.predict(
            image=image,
            confidence_threshold=confidence_threshold,
            top_k=top_k,
        )

        processing_time = time.time() - start_time

        # Add metadata
        results["metadata"] = {
            "filename": file.filename,
            "file_size": len(image_data),
            "image_size": image.size,
            "processing_time_ms": processing_time * 1000,
            "used_tta": use_tta,
        }

        return JSONResponse(results)

    except HTTPException:
        # Preserve service-layer HTTP errors (e.g., 503 busy)
        raise
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
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(requests) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Batch size limited to 10 images")
    
    try:
        results = []
        for i, request in enumerate(requests):
            try:
                image = await _load_image(request.image_url, request.image_base64)
                
                result = await svc.predict(
                    image=image,
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
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
    'breeds': svc.get_supported_breeds(),
    'total_breeds': len(svc.get_supported_breeds()),
    'model_version': svc.get_model_info().get('model_version', 'unknown')
    }


@router.get("/analytics")
async def get_breed_analytics():
    """Get analytics and statistics about supported breeds"""
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    breeds = svc.get_supported_breeds()
    
    # Basic analytics
    analytics = {
        "total_breeds": len(breeds),
        "model_version": svc.get_model_info().get("model_version", "unknown"),
        "breed_categories": {
            "herding": len([b for b in breeds if any(term in b.lower() for term in ['collie', 'shepherd', 'retriever', 'setter', 'spaniel'])]),
            "hound": len([b for b in breeds if any(term in b.lower() for term in ['hound', 'beagle', 'greyhound', 'whippet'])]),
            "terrier": len([b for b in breeds if 'terrier' in b.lower()]),
            "toy": len([b for b in breeds if any(term in b.lower() for term in ['pug', 'chihuahua', 'maltese', 'shih_tzu'])]),
            "working": len([b for b in breeds if any(term in b.lower() for term in ['mastiff', 'boxer', 'rottweiler', 'siberian_husky'])]),
            "other": 0  # Will be calculated
        },
        "sample_breeds": breeds[:10],  # First 10 breeds as examples
        "performance_metrics": svc.get_performance_metrics()
    }
    
    # Calculate other category
    total_categorized = sum(analytics["breed_categories"].values())
    analytics["breed_categories"]["other"] = analytics["total_breeds"] - total_categorized
    
    return analytics


@router.get("/model-info")
async def get_model_info():
    """Get detailed model information"""
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return svc.get_model_info()


@router.post("/calibrate")
async def calibrate_confidence(
    calibration_data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks
):
    """
    Recalibrate confidence scores based on validation data
    """
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Add calibration task to background
    background_tasks.add_task(svc.update_calibration, calibration_data)
    
    return {
        'status': 'calibration_started',
        'message': 'Confidence calibration running in background'
    }


@router.get("/search/{query}")
async def search_breeds(query: str, limit: int = 5):
    """Search for breeds matching the query"""
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    breeds = svc.get_supported_breeds()
    query_lower = query.lower()
    
    # Find matching breeds
    matches = [breed for breed in breeds if query_lower in breed.lower()]
    
    # Sort by relevance (exact matches first, then prefix matches)
    exact_matches = [b for b in matches if b.lower().startswith(query_lower)]
    other_matches = [b for b in matches if not b.lower().startswith(query_lower)]
    sorted_matches = exact_matches + other_matches
    
    return {
        "query": query,
        "total_matches": len(sorted_matches),
        "results": sorted_matches[:limit],
        "has_more": len(sorted_matches) > limit
    }


async def _load_image(image_url: Optional[str] = None, 
                     image_base64: Optional[str] = None) -> Any:
    """Load image from URL or base64 data"""
    
    # Lazy import PIL via importlib
    _PILImage = importlib.import_module("PIL.Image")

    if image_base64:
        try:
            # Handle base64 data URLs
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]
            
            image_data = base64.b64decode(image_base64)
            image = _PILImage.open(io.BytesIO(image_data))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")
            
    elif image_url:
        try:
            import httpx
            timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                # HEAD check to validate content-type and size if available
                try:
                    head = await client.head(image_url)
                    ctype = head.headers.get('content-type', '')
                    clen = head.headers.get('content-length')
                    if ctype and 'image' not in ctype.lower():
                        raise HTTPException(status_code=400, detail="URL is not an image")
                    if clen and int(clen) > get_int("MAX_IMAGE_BYTES", 10 * 1024 * 1024):
                        raise HTTPException(status_code=400, detail="Image too large")
                except httpx.HTTPError:
                    # proceed to GET, some servers may not support HEAD
                    pass

                # Simple retry with backoff for GET
                last_exc: Exception | None = None
                for attempt in range(3):
                    try:
                        resp = await client.get(image_url)
                        resp.raise_for_status()
                        ctype2 = resp.headers.get('content-type', '')
                        if ctype2 and 'image' not in ctype2.lower():
                            raise HTTPException(status_code=400, detail="Downloaded content is not an image")
                        if len(resp.content) > get_int("MAX_IMAGE_BYTES", 10 * 1024 * 1024):
                            raise HTTPException(status_code=400, detail="Image too large")
                        image = _PILImage.open(io.BytesIO(resp.content))
                        break
                    except Exception as e:
                        last_exc = e
                        await asyncio.sleep(2 ** attempt)
                else:
                    raise HTTPException(status_code=502, detail=f"Image fetch failed: {last_exc}")
        except HTTPException:
            raise
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
    if not get_flag("ENABLE_BREED_API", False):
        raise HTTPException(status_code=503, detail="Breed API disabled")
    if not svc.get_model_info().get("loaded"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return svc.get_performance_metrics()
