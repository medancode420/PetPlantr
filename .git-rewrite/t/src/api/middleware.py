"""
Middleware for PetPlantr Production Monitoring
Implements request timing, metrics collection, and admission control
"""
import time
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import os

logger = logging.getLogger(__name__)

# Import metrics if available
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.metrics import metrics, time_http_request
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None
    logger.warning("Metrics module not available")

class AdmissionController:
    """
    Admission control to prevent overload.
    
    Implements queue depth limits and token bucket for rate limiting.
    """
    
    def __init__(self):
        self.current_requests = {}  # Track by operation type
        self.max_queue_depth_breed = int(os.getenv("MAX_QUEUE_DEPTH_BREED", "50"))
        self.max_queue_depth_mesh = int(os.getenv("MAX_QUEUE_DEPTH_MESH", "100"))
        self.max_tokens_in_use = int(os.getenv("MAX_TOKENS_IN_USE", "6"))
        self.current_tokens = 0
        
    def should_admit_request(self, operation_type: str) -> tuple[bool, str]:
        """
        Check if request should be admitted based on current load.
        
        Returns:
            (should_admit, reason_if_rejected)
        """
        current_count = self.current_requests.get(operation_type, 0)
        
        # Check operation-specific limits
        if operation_type == "breed":
            if current_count >= self.max_queue_depth_breed:
                return False, f"breed_queue_full:{current_count}"
        elif operation_type == "mesh":
            if current_count >= self.max_queue_depth_mesh:
                return False, f"mesh_queue_full:{current_count}"
        
        # Check global token limit
        if self.current_tokens >= self.max_tokens_in_use:
            return False, f"tokens_exhausted:{self.current_tokens}"
        
        return True, ""
    
    def start_request(self, operation_type: str, tokens_required: int = 1):
        """Mark request as started."""
        self.current_requests[operation_type] = self.current_requests.get(operation_type, 0) + 1
        self.current_tokens += tokens_required
        
        if METRICS_AVAILABLE and metrics:
            metrics.update_queue_depth(operation_type, self.current_requests[operation_type])
    
    def end_request(self, operation_type: str, tokens_required: int = 1):
        """Mark request as completed."""
        self.current_requests[operation_type] = max(0, self.current_requests.get(operation_type, 0) - 1)
        self.current_tokens = max(0, self.current_tokens - tokens_required)
        
        if METRICS_AVAILABLE and metrics:
            metrics.update_queue_depth(operation_type, self.current_requests[operation_type])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current admission control statistics."""
        return {
            "current_requests": dict(self.current_requests),
            "current_tokens": self.current_tokens,
            "limits": {
                "max_queue_depth_breed": self.max_queue_depth_breed,
                "max_queue_depth_mesh": self.max_queue_depth_mesh,
                "max_tokens_in_use": self.max_tokens_in_use
            }
        }

# Global admission controller
admission_controller = AdmissionController()

class ProductionMiddleware(BaseHTTPMiddleware):
    """
    Production middleware for metrics, timing, and request tracking.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract route information
        route_path = request.url.path
        method = request.method
        
        # Determine operation type for admission control
        operation_type = self._get_operation_type(route_path)
        tokens_required = self._get_tokens_required(route_path)
        
        # Apply admission control for specific operations
        if operation_type and operation_type in ["breed", "mesh"]:
            should_admit, rejection_reason = admission_controller.should_admit_request(operation_type)
            
            if not should_admit:
                # Log rejection and record metrics
                logger.warning(f"Request rejected by admission control: {rejection_reason}")
                
                if METRICS_AVAILABLE and metrics:
                    metrics.record_admission_rejection(operation_type, rejection_reason)
                    metrics.record_http_request(route_path, method, 503, 0.0)
                
                # Return 503 with admission control information
                return Response(
                    content='{"error": "Service temporarily unavailable due to high load", "reason": "' + rejection_reason + '"}',
                    status_code=503,
                    media_type="application/json",
                    headers={"Retry-After": "30"}
                )
            
            # Admit the request
            admission_controller.start_request(operation_type, tokens_required)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            if METRICS_AVAILABLE and metrics:
                metrics.record_http_request(route_path, method, response.status_code, duration)
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = str(getattr(request.state, "request_id", "unknown"))
            
            return response
        
        except Exception as e:
            duration = time.time() - start_time
            
            # Record error metrics
            if METRICS_AVAILABLE and metrics:
                metrics.record_http_request(route_path, method, 500, duration)
            
            logger.error(f"Request failed: {route_path} {method} - {str(e)}")
            raise
        
        finally:
            # Clean up admission control
            if operation_type and operation_type in ["breed", "mesh"]:
                admission_controller.end_request(operation_type, tokens_required)
    
    def _get_operation_type(self, path: str) -> str:
        """Determine operation type from request path."""
        if "/breed" in path:
            return "breed"
        elif "/mesh" in path or "/3d" in path or "/generate" in path:
            return "mesh"
        elif "/health" in path or "/ready" in path:
            return "health"
        else:
            return "other"
    
    def _get_tokens_required(self, path: str) -> int:
        """Determine how many tokens this operation requires."""
        if "/breed" in path:
            return 1  # Breed detection is lightweight
        elif "/mesh" in path or "/3d" in path or "/generate" in path:
            return 3  # 3D generation is resource intensive
        else:
            return 1

@asynccontextmanager
async def observe_phase(phase_name: str):
    """
    Context manager for timing specific phases of request processing.
    
    Usage:
        async with observe_phase("breed_detection"):
            result = await detect_breed(image)
    """
    start_time = time.time()
    
    if METRICS_AVAILABLE and metrics:
        logger.debug(f"Starting phase: {phase_name}")
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        
        if METRICS_AVAILABLE and metrics:
            metrics.phase_latency.labels(phase=phase_name).observe(duration)
            logger.debug(f"Phase {phase_name} completed in {duration:.3f}s")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request IDs for tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

# Utility functions for route handlers
def get_current_load() -> Dict[str, Any]:
    """Get current system load information."""
    return admission_controller.get_stats()

def is_system_overloaded() -> bool:
    """Check if system is currently overloaded."""
    stats = admission_controller.get_stats()
    
    # Simple heuristic for overload detection
    total_requests = sum(stats["current_requests"].values())
    token_utilization = stats["current_tokens"] / stats["limits"]["max_tokens_in_use"]
    
    return total_requests > 20 or token_utilization > 0.8

def should_degrade_quality() -> bool:
    """Check if we should degrade quality to handle load."""
    return is_system_overloaded()

# Export useful components
__all__ = [
    "ProductionMiddleware",
    "RequestIDMiddleware", 
    "observe_phase",
    "admission_controller",
    "get_current_load",
    "is_system_overloaded", 
    "should_degrade_quality"
]
