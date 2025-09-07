# SSL/TLS Configuration for PetPlantr Production
# This script generates self-signed certificates for development/testing
# For production, use certificates from Let's Encrypt or your CA

#!/bin/bash

set -e

echo "🔐 Generating SSL/TLS certificates for PetPlantr..."

# Create SSL directory if it doesn't exist
mkdir -p security/ssl

# Generate private key
openssl genrsa -out security/ssl/petplantr.key 2048

# Generate certificate signing request
cat > security/ssl/cert.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = PetPlantr
OU = AI Platform
CN = localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = petplantr.local
DNS.3 = api.petplantr.com
IP.1 = 127.0.0.1
IP.2 = 0.0.0.0
EOF

# Generate self-signed certificate (valid for 365 days)
openssl req -new -x509 -key security/ssl/petplantr.key \
    -out security/ssl/petplantr.crt \
    -days 365 \
    -config security/ssl/cert.conf \
    -extensions v3_req

# Generate DH parameters for forward secrecy
openssl dhparam -out security/ssl/dhparam.pem 2048

# Set proper permissions
chmod 600 security/ssl/petplantr.key
chmod 644 security/ssl/petplantr.crt

echo "✅ SSL certificates generated successfully!"
echo "📁 Certificate files:"
echo "   - Private key: security/ssl/petplantr.key"
echo "   - Certificate: security/ssl/petplantr.crt"
echo "   - DH params: security/ssl/dhparam.pem"
echo ""
echo "🔒 For production deployment:"
echo "   1. Replace self-signed certs with Let's Encrypt certificates"
echo "   2. Update NGINX configuration to use production certs"
echo "   3. Enable HSTS headers"
echo "   4. Configure certificate auto-renewal"
