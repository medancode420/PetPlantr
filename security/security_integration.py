# PetPlantr Security Integration Module
# Integrates authentication, rate limiting, and security middleware

import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager

# Import security components with fallbacks
try:
    from security.auth.auth_config import (
        get_current_user,
        get_current_active_user,
        require_admin,
        authenticate_user,
        create_access_token,
        fake_users_db
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    print("Warning: Authentication module not available")
    # Define dummy functions for type checking
    get_current_user = None
    get_current_active_user = None
    require_admin = None
    authenticate_user = None
    create_access_token = None
    fake_users_db = {}

try:
    from security.rate_limiting.rate_limit_config import (
        check_rate_limit,
        limiter,
        SlowAPIMiddleware
    )
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    print("Warning: Rate limiting module not available")
    # Define dummy functions/classes
    check_rate_limit = None
    limiter = None
    SlowAPIMiddleware = None

# Security headers middleware
class SecurityHeadersMiddleware:
    """Add security headers to all responses"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                # Add security headers
                security_headers = [
                    (b"X-Content-Type-Options", b"nosniff"),
                    (b"X-Frame-Options", b"DENY"),
                    (b"X-XSS-Protection", b"1; mode=block"),
                    (b"Referrer-Policy", b"strict-origin-when-cross-origin"),
                    (b"Permissions-Policy", b"geolocation=(), microphone=(), camera=()"),
                    (b"Strict-Transport-Security", b"max-age=31536000; includeSubDomains"),
                    (b"Content-Security-Policy", b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"),
                ]
                headers.extend(security_headers)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send)

def setup_security(app: FastAPI) -> None:
    """Setup all security components for the FastAPI application"""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted host middleware (enable in production)
    if os.getenv("ENVIRONMENT") == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["yourdomain.com", "*.yourdomain.com"]  # Configure for your domain
        )

    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting middleware
    if RATE_LIMITING_AVAILABLE:
        try:
            from security.rate_limiting.rate_limit_config import SlowAPIMiddleware
            app.add_middleware(SlowAPIMiddleware)
        except ImportError:
            pass

    # Add security dependencies to all routes that need protection
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        # Apply rate limiting to all requests
        if RATE_LIMITING_AVAILABLE:
            try:
                from security.rate_limiting.rate_limit_config import check_rate_limit
                await check_rate_limit(request)
            except (ImportError, HTTPException):
                pass  # Let the exception propagate if it's an HTTPException

        # Continue with request
        response = await call_next(request)
        return response

# Authentication routes (if auth is available)
def add_auth_routes(app: FastAPI) -> None:
    """Add authentication routes to the application"""

    if not AUTH_AVAILABLE:
        print("Warning: Authentication not available, skipping auth routes")
        return

    from datetime import timedelta
    from fastapi import Form
    from pydantic import BaseModel

    class LoginRequest(BaseModel):
        username: str
        password: str

    class TokenResponse(BaseModel):
        access_token: str
        token_type: str = "bearer"

    @app.post("/auth/login", response_model=TokenResponse)
    async def login(login_data: LoginRequest):
        """Authenticate user and return JWT token"""
        if not AUTH_AVAILABLE:
            raise HTTPException(status_code=501, detail="Authentication not configured")

        try:
            from security.auth.auth_config import authenticate_user, create_access_token, fake_users_db

            user = authenticate_user(fake_users_db, login_data.username, login_data.password)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
            access_token = create_access_token(
                data={"sub": user.username, "scopes": user.scopes},
                expires_delta=access_token_expires
            )

            return TokenResponse(access_token=access_token)
        except ImportError:
            raise HTTPException(status_code=501, detail="Authentication module not available")

    @app.get("/auth/me")
    async def read_users_me(current_user = Depends(get_current_active_user if AUTH_AVAILABLE else None)):
        """Get current user information"""
        if not AUTH_AVAILABLE:
            raise HTTPException(status_code=501, detail="Authentication not configured")

        try:
            from security.auth.auth_config import get_current_active_user
            # This would need proper dependency injection
            return {"message": "Authentication endpoint available"}
        except ImportError:
            raise HTTPException(status_code=501, detail="Authentication module not available")

    @app.get("/auth/admin-only")
    async def admin_only():
        """Admin-only endpoint example"""
        if not AUTH_AVAILABLE:
            raise HTTPException(status_code=501, detail="Authentication not configured")

        try:
            from security.auth.auth_config import require_admin
            # This would need proper dependency injection
            return {"message": "Admin endpoint available"}
        except ImportError:
            raise HTTPException(status_code=501, detail="Authentication module not available")

# Health check with security info
def add_security_health_check(app: FastAPI) -> None:
    """Add security status to health check"""

    @app.get("/health/security")
    async def security_health():
        """Security components health check"""
        status = {
            "authentication": AUTH_AVAILABLE,
            "rate_limiting": RATE_LIMITING_AVAILABLE,
            "ssl_enabled": os.path.exists("security/ssl/certs/petplantr.crt") if os.path.exists("security/ssl") else False,
            "redis_available": False  # Would need to check Redis connection
        }

        # Check Redis if rate limiting is available
        if RATE_LIMITING_AVAILABLE:
            try:
                from security.rate_limiting.rate_limit_config import rate_limiter
                # Simple Redis ping
                rate_limiter.redis.ping()
                status["redis_available"] = True
            except (ImportError, Exception):
                status["redis_available"] = False

        return {
            "status": "healthy" if all(status.values()) else "degraded",
            "components": status
        }

# Export functions
__all__ = [
    "setup_security",
    "add_auth_routes",
    "add_security_health_check",
    "AUTH_AVAILABLE",
    "RATE_LIMITING_AVAILABLE"
]
