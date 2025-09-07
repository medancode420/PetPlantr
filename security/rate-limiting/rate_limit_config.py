# PetPlantr Rate Limiting Configuration
# Redis-based rate limiting with multiple tiers

import os
import redis
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from datetime import datetime, timedelta

# Try to import slowapi, fallback if not available
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.middleware import SlowAPIMiddleware
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False

    class Limiter:
        def __init__(self, key_func=None):
            pass

    def get_remote_address(request):
        return request.client.host if request.client else "unknown"

    class SlowAPIMiddleware:
        pass

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Rate limiting tiers
RATE_LIMITS = {
    "free": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "burst_limit": 20
    },
    "basic": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "burst_limit": 100
    },
    "premium": {
        "requests_per_minute": 300,
        "requests_per_hour": 5000,
        "burst_limit": 500
    },
    "enterprise": {
        "requests_per_minute": 1000,
        "requests_per_hour": 20000,
        "burst_limit": 2000
    }
}

class RateLimiter:
    """Custom rate limiter with Redis backend"""

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis = redis.from_url(redis_url)
        self.prefix = "petplantr:ratelimit"

    def _get_key(self, identifier: str, window: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"{self.prefix}:{identifier}:{window}"

    def _get_window_info(self, window: str) -> tuple[int, str]:
        """Get window duration and format"""
        if window == "minute":
            return 60, "%Y-%m-%d-%H-%M"
        elif window == "hour":
            return 3600, "%Y-%m-%d-%H"
        elif window == "day":
            return 86400, "%Y-%m-%d"
        else:
            raise ValueError(f"Invalid window: {window}")

    def is_allowed(self, identifier: str, limit: int, window: str) -> bool:
        """Check if request is allowed under rate limit"""
        key = self._get_key(identifier, window)
        duration, time_format = self._get_window_info(window)

        # Get current window
        now = datetime.utcnow()
        current_window = now.strftime(time_format)

        # Clean up old windows (keep last 2)
        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(key, 0, now.timestamp() - duration * 2)
        pipeline.zadd(key, {f"{current_window}:{now.timestamp()}": now.timestamp()})
        pipeline.zcard(key)
        pipeline.expire(key, duration * 3)  # Expire key after 3 windows

        _, _, count, _ = pipeline.execute()

        return count <= limit

    def get_remaining_requests(self, identifier: str, limit: int, window: str) -> int:
        """Get remaining requests for the current window"""
        key = self._get_key(identifier, window)
        count = self.redis.zcard(key)
        if isinstance(count, int):
            return max(0, limit - count)
        else:
            # Handle async response or other types
            return max(0, limit - 0)  # Default to 0 if count is not available

    def get_reset_time(self, identifier: str, window: str) -> datetime:
        """Get time when current window resets"""
        duration, _ = self._get_window_info(window)
        now = datetime.utcnow()
        # Calculate next window boundary
        if window == "minute":
            reset = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        elif window == "hour":
            reset = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif window == "day":
            reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            reset = now + timedelta(seconds=duration)

        return reset

# Global rate limiter instance
rate_limiter = RateLimiter()

# FastAPI limiter instance (fallback)
limiter = Limiter(key_func=get_remote_address)

def get_client_tier(request: Request) -> str:
    """Determine client tier based on API key or authentication"""
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key")

    # Simple tier determination (replace with database lookup)
    if api_key:
        if api_key.startswith("premium"):
            return "premium"
        elif api_key.startswith("enterprise"):
            return "enterprise"
        else:
            return "basic"

    # Default to free tier
    return "free"

def get_client_identifier(request: Request) -> str:
    """Get unique client identifier for rate limiting"""
    # Use API key if available, otherwise IP address
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"

    # Fallback to IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP if multiple
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"

async def check_rate_limit(request: Request) -> None:
    """Check rate limit for the current request"""
    try:
        client_id = get_client_identifier(request)
        tier = get_client_tier(request)
        limits = RATE_LIMITS.get(tier, RATE_LIMITS["free"])

        # Check minute limit
        if not rate_limiter.is_allowed(client_id, limits["requests_per_minute"], "minute"):
            reset_time = rate_limiter.get_reset_time(client_id, "minute")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "tier": tier,
                    "limit": limits["requests_per_minute"],
                    "window": "minute",
                    "reset_time": reset_time.isoformat(),
                    "retry_after": int((reset_time - datetime.utcnow()).total_seconds())
                }
            )

        # Check burst limit (shorter window)
        if not rate_limiter.is_allowed(client_id, limits["burst_limit"], "minute"):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Burst rate limit exceeded",
                    "tier": tier,
                    "limit": limits["burst_limit"],
                    "window": "burst",
                    "retry_after": 60
                }
            )

    except redis.ConnectionError:
        # If Redis is down, allow request but log warning
        print("Warning: Redis connection failed, allowing request without rate limiting")
        pass

# Export for use in main application
__all__ = [
    "RateLimiter",
    "rate_limiter",
    "limiter",
    "SlowAPIMiddleware",
    "check_rate_limit",
    "get_client_tier",
    "get_client_identifier",
    "RATE_LIMITS"
]
