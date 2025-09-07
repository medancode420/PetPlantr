# PetPlantr Security Configuration

This directory contains all security-related configurations for PetPlantr.

## Components

### 1. SSL/TLS Configuration ()
- Certificate generation scripts
- NGINX SSL configuration
- Self-signed certificates for development

### 2. Authentication ()
- JWT-based authentication
- API key authentication
- User management and scopes

### 3. Rate Limiting ()
- Redis-based rate limiting
- Multiple tiers (free, basic, premium, enterprise)
- Burst protection

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r security/requirements-security.txt
   ```

2. **Generate SSL Certificates**
   ```bash
   cd security/ssl
   bash generate_ssl_certs.sh
   ```

3. **Configure Environment**
   ```bash
   cp security/.env.security.template .env
   # Edit .env with your security settings
   ```

4. **Start with Security**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.security.yml up
   ```

5. **Test Security**
   ```bash
   python security/test_security.py
   ```

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
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `GET /auth/me` - Current user info

### Protected Endpoints
All API endpoints require authentication via:
- JWT token in Authorization header: `Bearer <token>`
- API key in X-API-Key header: `<api-key>`

## Rate Limiting Tiers

| Tier | Requests/Minute | Requests/Hour | Burst Limit |
|------|----------------|---------------|-------------|
| Free | 10 | 100 | 20 |
| Basic | 60 | 1000 | 100 |
| Premium | 300 | 5000 | 500 |
| Enterprise | 1000 | 20000 | 2000 |
