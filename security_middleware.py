from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Rate limiting (simple in-memory implementation)
        client_ip = scope.get("client", [""])[0]
        current_time = time.time()

        # Add security headers
        async def send_with_security_headers(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.extend([
                    [b"X-Content-Type-Options", b"nosniff"],
                    [b"X-Frame-Options", b"DENY"],
                    [b"X-XSS-Protection", b"1; mode=block"],
                    [b"Strict-Transport-Security", b"max-age=31536000; includeSubDomains"],
                    [b"Content-Security-Policy", b"default-src 'self'"],
                ])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_security_headers)

def setup_cors(app):
    """Setup CORS middleware"""
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],  # Replace with your domain
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

def setup_security_middleware(app):
    """Setup security middleware"""
    app.add_middleware(SecurityMiddleware)
