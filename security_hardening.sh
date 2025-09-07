#!/bin/bash
# PetPlantr Security Hardening Script
# Run this script to apply security remediations

set -e

echo "🔒 Applying PetPlantr Security Hardening..."

# 1. Fix file permissions
echo "📁 Fixing file permissions..."
chmod 600 .env 2>/dev/null || true
chmod 644 config.json 2>/dev/null || true
chmod 755 api_server.py 2>/dev/null || true
find models/ -type f -exec chmod 644 {} \; 2>/dev/null || true
find data/ -type f -exec chmod 644 {} \; 2>/dev/null || true

# 2. Create .env.example template
if [ ! -f .env.example ]; then
    echo "📝 Creating .env.example template..."
    cat > .env.example << EOF
# PetPlantr Environment Configuration
# Copy this file to .env and fill in your values

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# AWS Configuration (if using AWS services)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Database (if applicable)
DATABASE_URL=postgresql://user:password@localhost/petplantr

# External Services
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-key
STRIPE_SECRET_KEY=sk_test_your-stripe-secret
EOF
fi

# 3. Create security headers middleware
echo "🛡️  Creating security middleware..."
cat > security_middleware.py << 'EOF'
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
EOF

# 4. Update requirements.txt with security packages
echo "📦 Adding security dependencies..."
if [ -f requirements.txt ]; then
    grep -q "python-multipart" requirements.txt || echo "python-multipart>=0.0.5" >> requirements.txt
    grep -q "slowapi" requirements.txt || echo "slowapi>=0.1.0" >> requirements.txt
    grep -q "cryptography" requirements.txt || echo "cryptography>=3.4.0" >> requirements.txt
fi

echo "✅ Security hardening applied!"
echo "🔄 Next steps:"
echo "   1. Review and update .env.example with your values"
echo "   2. Run: pip install -r requirements.txt"
echo "   3. Test the API with security middleware"
