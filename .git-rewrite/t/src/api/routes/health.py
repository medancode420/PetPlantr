"""
Health and Readiness Endpoints for PetPlantr
Implements proper health/readiness separation for production deployments
"""
import time
import logging
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Response
import aiohttp
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency check configuration
DEPENDENCY_CHECKS = {
    'replicate': {
        'enabled': True,
        'timeout_sec': 5.0
    },
    's3': {
        'enabled': True,
        'timeout_sec': 3.0
    },
    'database': {
        'enabled': False,  # Enable when using persistent DB
        'timeout_sec': 2.0
    }
}

class HealthChecker:
    """Centralized health and readiness checking."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check_time = 0
        self.cached_readiness = None
        self.cache_ttl = 30  # Cache readiness for 30 seconds
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Basic health check - should always return 200 unless app is broken.
        Used by load balancers for routing decisions.
        """
        uptime = time.time() - self.start_time
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": uptime,
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    
    async def check_readiness(self) -> Dict[str, Any]:
        """
        Comprehensive readiness check - validates all dependencies.
        Used to determine if traffic should be routed to this instance.
        """
        now = time.time()
        
        # Use cached result if fresh
        if (self.cached_readiness and 
            now - self.last_check_time < self.cache_ttl):
            return self.cached_readiness
        
        results = {
            "status": "ready",
            "timestamp": now,
            "checks": {},
            "overall_healthy": True
        }
        
        # Check all enabled dependencies
        check_tasks = []
        
        if DEPENDENCY_CHECKS['replicate']['enabled']:
            check_tasks.append(self._check_replicate())
        
        if DEPENDENCY_CHECKS['s3']['enabled']:
            check_tasks.append(self._check_s3())
        
        if DEPENDENCY_CHECKS['database']['enabled']:
            check_tasks.append(self._check_database())
        
        # Run all checks concurrently
        if check_tasks:
            check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
            
            for i, result in enumerate(check_results):
                if isinstance(result, Exception):
                    check_name = list(DEPENDENCY_CHECKS.keys())[i]
                    results["checks"][check_name] = {
                        "status": "failed",
                        "error": str(result),
                        "healthy": False
                    }
                    results["overall_healthy"] = False
                elif isinstance(result, dict):
                    results["checks"].update(result)
                    # Check if any dependency in this result is unhealthy
                    for dep_name, dep_info in result.items():
                        if isinstance(dep_info, dict) and not dep_info.get("healthy", True):
                            results["overall_healthy"] = False
        
        # Update status based on overall health
        if not results["overall_healthy"]:
            results["status"] = "not_ready"
        
        # Cache the result
        self.cached_readiness = results
        self.last_check_time = now
        
        return results
    
    async def _check_replicate(self) -> Dict[str, Any]:
        """Check Replicate API connectivity and token validity."""
        replicate_token = os.getenv("REPLICATE_API_TOKEN")
        
        if not replicate_token or len(replicate_token) < 10:
            return {
                "replicate": {
                    "status": "failed",
                    "error": "REPLICATE_API_TOKEN not configured or invalid",
                    "healthy": False,
                    "response_time_ms": 0
                }
            }
        
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(
                total=DEPENDENCY_CHECKS['replicate']['timeout_sec']
            )
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "Authorization": f"Token {replicate_token}",
                    "User-Agent": "PetPlantr-HealthCheck/1.0"
                }
                
                # Use a lightweight endpoint to verify token
                async with session.get(
                    "https://api.replicate.com/v1/models",
                    headers=headers,
                    params={"limit": 1}  # Minimal response
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return {
                            "replicate": {
                                "status": "healthy",
                                "healthy": True,
                                "response_time_ms": round(response_time, 2)
                            }
                        }
                    else:
                        return {
                            "replicate": {
                                "status": "failed",
                                "error": f"HTTP {response.status}",
                                "healthy": False,
                                "response_time_ms": round(response_time, 2)
                            }
                        }
        
        except asyncio.TimeoutError:
            return {
                "replicate": {
                    "status": "failed",
                    "error": "Timeout connecting to Replicate API",
                    "healthy": False,
                    "response_time_ms": DEPENDENCY_CHECKS['replicate']['timeout_sec'] * 1000
                }
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "replicate": {
                    "status": "failed",
                    "error": f"Connection error: {str(e)}",
                    "healthy": False,
                    "response_time_ms": round(response_time, 2)
                }
            }
    
    async def _check_s3(self) -> Dict[str, Any]:
        """Check S3 connectivity with a lightweight probe."""
        start_time = time.time()
        
        try:
            # Get S3 configuration
            bucket = os.getenv("S3_BUCKET")
            region = os.getenv("AWS_REGION", "us-east-1")
            prefix = os.getenv("S3_PREFIX", "artifacts/")
            
            if not bucket:
                return {
                    "s3": {
                        "status": "failed",
                        "error": "S3_BUCKET not configured",
                        "healthy": False,
                        "response_time_ms": 0
                    }
                }
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            
            # Perform a lightweight probe - create and delete a small test object
            probe_key = f"{prefix}health-probes/{uuid.uuid4()}.txt"
            probe_content = b"health-check"
            
            # Put object
            s3_client.put_object(
                Bucket=bucket,
                Key=probe_key,
                Body=probe_content,
                ContentType="text/plain"
            )
            
            # Verify object exists
            s3_client.head_object(Bucket=bucket, Key=probe_key)
            
            # Clean up (best effort)
            try:
                s3_client.delete_object(Bucket=bucket, Key=probe_key)
            except Exception:
                pass  # Ignore cleanup errors
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "s3": {
                    "status": "healthy",
                    "healthy": True,
                    "bucket": bucket,
                    "region": region,
                    "response_time_ms": round(response_time, 2)
                }
            }
        
        except NoCredentialsError:
            response_time = (time.time() - start_time) * 1000
            return {
                "s3": {
                    "status": "failed",
                    "error": "AWS credentials not configured",
                    "healthy": False,
                    "response_time_ms": round(response_time, 2)
                }
            }
        except ClientError as e:
            response_time = (time.time() - start_time) * 1000
            error_code = e.response['Error']['Code']
            return {
                "s3": {
                    "status": "failed",
                    "error": f"AWS S3 error: {error_code}",
                    "healthy": False,
                    "response_time_ms": round(response_time, 2)
                }
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "s3": {
                    "status": "failed",
                    "error": f"S3 connection error: {str(e)}",
                    "healthy": False,
                    "response_time_ms": round(response_time, 2)
                }
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity (placeholder for future use)."""
        # Placeholder for when you add persistent database
        return {
            "database": {
                "status": "healthy",
                "healthy": True,
                "note": "No persistent database configured",
                "response_time_ms": 0
            }
        }

# Global health checker instance
health_checker = HealthChecker()

@router.get("/api/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Always returns 200 unless the application is fundamentally broken.
    Used by load balancers for routing decisions.
    """
    try:
        result = await health_checker.check_health()
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@router.get("/api/ready")
async def readiness_check(response: Response):
    """
    Comprehensive readiness check endpoint.
    
    Returns 200 only when all dependencies are healthy and ready to serve traffic.
    Returns 503 when any critical dependency is unavailable.
    """
    try:
        result = await health_checker.check_readiness()
        
        if not result["overall_healthy"]:
            response.status_code = 503
            logger.warning(f"Readiness check failed: {result}")
        
        return result
    
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        response.status_code = 503
        return {
            "status": "not_ready",
            "timestamp": time.time(),
            "error": f"Readiness check exception: {str(e)}",
            "overall_healthy": False
        }

@router.get("/api/health/dependencies")
async def detailed_dependency_check():
    """
    Detailed dependency status for debugging and monitoring.
    Always returns 200 with detailed status of each dependency.
    """
    try:
        result = await health_checker.check_readiness()
        return {
            "timestamp": time.time(),
            "dependencies": result.get("checks", {}),
            "configuration": {
                "checks_enabled": {k: v["enabled"] for k, v in DEPENDENCY_CHECKS.items()},
                "cache_ttl_seconds": health_checker.cache_ttl
            }
        }
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        return {
            "timestamp": time.time(),
            "error": str(e),
            "dependencies": {},
            "configuration": {}
        }
