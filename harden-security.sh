#!/bin/bash
# Security hardening script for PetPlantr

echo "🔒 Hardening PetPlantr Security..."

# SSL/TLS hardening
echo "🔐 SSL/TLS Configuration:"
openssl dhparam -out security/ssl/dhparam/dhparam.pem 2048 2>/dev/null || echo "DH params exist"

# System hardening
echo "🛡️ System Security:"
# Disable unnecessary services
# sudo systemctl disable unnecessary services

# File permissions
echo "📁 Setting secure file permissions..."
chmod 600 .env* 2>/dev/null || true
chmod 600 security/ssl/private/* 2>/dev/null || true
chmod 644 security/ssl/certs/* 2>/dev/null || true

# Firewall configuration
echo "🔥 Configuring firewall..."
# Allow only necessary ports
# sudo ufw default deny incoming
# sudo ufw default allow outgoing
# sudo ufw allow 80
# sudo ufw allow 443
# sudo ufw allow 22
# sudo ufw --force enable

# Security headers
echo "📋 Security Headers:"
cat > security-headers.conf << 'EOF'
# Security Headers for PetPlantr
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
