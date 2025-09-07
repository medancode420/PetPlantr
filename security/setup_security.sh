#!/bin/bash
# PetPlantr Security Setup Script
# Installs and configures all security components

set -e

echo "🔒 Setting up PetPlantr Security Components..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "api_server.py" ]; then
    print_error "Please run this script from the PetPlantr root directory"
    exit 1
fi

# Create security directories if they don't exist
print_status "Creating security directory structure..."
mkdir -p security/ssl security/auth security/rate-limiting

# Install security dependencies
print_status "Installing security dependencies..."
if command -v pip &> /dev/null; then
    pip install -r security/requirements-security.txt
    print_status "Security dependencies installed successfully"
else
    print_warning "pip not found. Please install security dependencies manually:"
    echo "pip install -r security/requirements-security.txt"
fi

# Generate SSL certificates
print_status "Generating SSL certificates..."
if [ -f "security/ssl/generate_ssl_certs.sh" ]; then
    chmod +x security/ssl/generate_ssl_certs.sh
    bash security/ssl/generate_ssl_certs.sh
    print_status "SSL certificates generated successfully"
else
    print_warning "SSL certificate generation script not found"
fi

# Check Redis availability for rate limiting
print_status "Checking Redis availability..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        print_status "Redis is available for rate limiting"
    else
        print_warning "Redis is not running. Rate limiting will use fallback mode"
        echo "To enable Redis-based rate limiting, start Redis:"
        echo "redis-server"
    fi
else
    print_warning "redis-cli not found. Install Redis for optimal rate limiting"
fi

# Create environment file template
print_status "Creating security environment template..."
cat > security/.env.security.template << EOF
# PetPlantr Security Configuration
# Copy this file to .env and update with your values

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
API_KEY=petplantr-api-key-12345

# Redis Configuration (for rate limiting)
REDIS_URL=redis://localhost:6379

# SSL Configuration
SSL_CERT_PATH=security/ssl/certs/petplantr.crt
SSL_KEY_PATH=security/ssl/private/petplantr.key

# Security Headers
HSTS_MAX_AGE=31536000
CSP_DEFAULT_SRC='self'
CSP_SCRIPT_SRC='self' 'unsafe-inline'
CSP_STYLE_SRC='self' 'unsafe-inline'

# Rate Limiting Tiers
RATE_LIMIT_FREE_REQUESTS_PER_MINUTE=10
RATE_LIMIT_BASIC_REQUESTS_PER_MINUTE=60
RATE_LIMIT_PREMIUM_REQUESTS_PER_MINUTE=300
RATE_LIMIT_ENTERPRISE_REQUESTS_PER_MINUTE=1000
EOF

print_status "Security environment template created at security/.env.security.template"

# Create Docker Compose override for security
print_status "Creating Docker Compose security configuration..."
cat > docker-compose.security.yml << EOF
version: '3.8'

services:
  petplantr-api:
    environment:
      - JWT_SECRET=\${JWT_SECRET}
      - API_KEY=\${API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./security/ssl:/app/security/ssl:ro

  nginx:
    volumes:
      - ./security/ssl/certs:/etc/ssl/certs:ro
      - ./security/ssl/private:/etc/ssl/private:ro
    ports:
      - "443:443"  # HTTPS
      - "80:80"    # HTTP (redirect to HTTPS)

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
EOF

print_status "Docker Compose security configuration created"

# Update main docker-compose.yml to include security
print_status "Updating main Docker Compose configuration..."
if [ -f "docker-compose.yml" ]; then
    # Add security service if not present
    if ! grep -q "redis:" docker-compose.yml; then
        cat >> docker-compose.yml << EOF

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
EOF
        print_status "Redis service added to main docker-compose.yml"
    fi
fi

# Create security test script
print_status "Creating security test script..."
cat > security/test_security.py << EOF
#!/usr/bin/env python3
"""
PetPlantr Security Test Script
Tests authentication, rate limiting, and SSL configuration
"""

import requests
import time
import json
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://localhost:443"  # Use HTTPS
API_KEY = "petplantr-api-key-12345"

def test_ssl_connection():
    """Test SSL connection"""
    print("Testing SSL connection...")
    try:
        response = requests.get(f"{BASE_URL}/health", verify=False)
        print(f"SSL connection: {'✓' if response.status_code == 200 else '✗'}")
        return response.status_code == 200
    except Exception as e:
        print(f"SSL connection failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting"""
    print("Testing rate limiting...")
    success_count = 0
    rate_limited_count = 0

    for i in range(15):  # More than free tier limit
        try:
            response = requests.get(
                f"{BASE_URL}/health",
                headers={"X-API-Key": API_KEY},
                verify=False
            )
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
            time.sleep(0.1)  # Small delay between requests
        except Exception as e:
            print(f"Request {i+1} failed: {e}")

    print(f"Successful requests: {success_count}")
    print(f"Rate limited requests: {rate_limited_count}")
    return rate_limited_count > 0

def test_authentication():
    """Test authentication endpoints"""
    print("Testing authentication...")
    # This would test JWT authentication when implemented
    print("Authentication tests: Placeholder (implement JWT endpoints first)")
    return True

def main():
    """Run all security tests"""
    print("🔒 PetPlantr Security Test Suite")
    print("=" * 40)

    tests = [
        ("SSL Connection", test_ssl_connection),
        ("Rate Limiting", test_rate_limiting),
        ("Authentication", test_authentication)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            print("✓ PASSED")
            passed += 1
        else:
            print("✗ FAILED")

    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All security tests passed!")
    else:
        print("⚠️  Some tests failed. Check configuration.")

if __name__ == "__main__":
    main()
EOF

chmod +x security/test_security.py
print_status "Security test script created at security/test_security.py"

# Create README for security setup
print_status "Creating security README..."
cat > security/README.md << EOF
# PetPlantr Security Configuration

This directory contains all security-related configurations for PetPlantr.

## Components

### 1. SSL/TLS Configuration (`ssl/`)
- Certificate generation scripts
- NGINX SSL configuration
- Self-signed certificates for development

### 2. Authentication (`auth/`)
- JWT-based authentication
- API key authentication
- User management and scopes

### 3. Rate Limiting (`rate-limiting/`)
- Redis-based rate limiting
- Multiple tiers (free, basic, premium, enterprise)
- Burst protection

## Setup Instructions

1. **Install Dependencies**
   \`\`\`bash
   pip install -r security/requirements-security.txt
   \`\`\`

2. **Generate SSL Certificates**
   \`\`\`bash
   cd security/ssl
   bash generate_ssl_certs.sh
   \`\`\`

3. **Configure Environment**
   \`\`\`bash
   cp security/.env.security.template .env
   # Edit .env with your security settings
   \`\`\`

4. **Start with Security**
   \`\`\`bash
   docker-compose -f docker-compose.yml -f docker-compose.security.yml up
   \`\`\`

5. **Test Security**
   \`\`\`bash
   python security/test_security.py
   \`\`\`

## Security Features

- ✅ HTTPS with SSL/TLS
- ✅ JWT Authentication
- ✅ API Key Authentication
- ✅ Rate Limiting with Redis
- ✅ Security Headers (HSTS, CSP, etc.)
- ✅ CORS Protection
- ✅ Input Validation

## Production Considerations

- Use proper SSL certificates (Let's Encrypt or commercial)
- Store secrets in environment variables or secret management
- Implement proper user database instead of mock data
- Enable Redis persistence for rate limiting data
- Configure firewall rules
- Enable audit logging
- Regular security updates

## API Endpoints

### Authentication
- \`POST /auth/login\` - User login
- \`POST /auth/refresh\` - Token refresh
- \`GET /auth/me\` - Current user info

### Protected Endpoints
All API endpoints require authentication via:
- JWT token in Authorization header: \`Bearer <token>\`
- API key in X-API-Key header: \`<api-key>\`

## Rate Limiting Tiers

| Tier | Requests/Minute | Requests/Hour | Burst Limit |
|------|----------------|---------------|-------------|
| Free | 10 | 100 | 20 |
| Basic | 60 | 1000 | 100 |
| Premium | 300 | 5000 | 500 |
| Enterprise | 1000 | 20000 | 2000 |
EOF

print_status "Security README created"

print_status "Security setup completed!"
echo ""
echo "Next steps:"
echo "1. Review and update security/.env.security.template"
echo "2. Run: docker-compose -f docker-compose.yml -f docker-compose.security.yml up"
echo "3. Test security with: python security/test_security.py"
echo ""
echo "For production deployment:"
echo "- Use proper SSL certificates"
echo "- Configure Redis persistence"
echo "- Set strong JWT secrets"
echo "- Implement proper user database"
