#!/usr/bin/env bash
# setup-ssl.sh - SSL/TLS certificate setup for PetPlantr production
# Supports Let's Encrypt, self-signed certificates, and custom certificates

set -euo pipefail

# Configuration
DOMAIN="${DOMAIN:-localhost}"
EMAIL="${EMAIL:-admin@petplantr.com}"
SSL_TYPE="${SSL_TYPE:-self-signed}"  # Options: letsencrypt, self-signed, custom
CERT_DIR="${CERT_DIR:-./security/ssl}"
FORCE="${FORCE:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }

# Create certificate directories
create_cert_dirs() {
    log_info "Creating SSL certificate directories..."
    mkdir -p "$CERT_DIR/certs"
    mkdir -p "$CERT_DIR/private"
    mkdir -p "$CERT_DIR/dhparam"
    log_success "Certificate directories created"
}

# Generate self-signed certificates
generate_self_signed() {
    log_info "Generating self-signed SSL certificates for $DOMAIN..."

    local key_file="$CERT_DIR/private/selfsigned.key"
    local cert_file="$CERT_DIR/certs/selfsigned.crt"

    # Check if certificates already exist
    if [[ -f "$cert_file" ]] && [[ "$FORCE" != "true" ]]; then
        log_warn "Self-signed certificates already exist. Use --force to regenerate."
        return 0
    fi

    # Generate private key
    openssl genrsa -out "$key_file" 2048

    # Generate certificate
    openssl req -new -x509 -key "$key_file" -out "$cert_file" -days 365 -subj "/C=US/ST=State/L=City/O=PetPlantr/CN=$DOMAIN"

    # Set proper permissions
    chmod 600 "$key_file"
    chmod 644 "$cert_file"

    log_success "Self-signed certificates generated"
    log_info "Certificate: $cert_file"
    log_info "Private Key: $key_file"
}

# Setup Let's Encrypt certificates
setup_letsencrypt() {
    log_info "Setting up Let's Encrypt SSL certificates for $DOMAIN..."

    # Check if certbot is installed
    if ! command -v certbot >/dev/null 2>&1; then
        log_error "Certbot is not installed. Please install it first:"
        log_error "  Ubuntu/Debian: sudo apt install certbot"
        log_error "  CentOS/RHEL: sudo yum install certbot"
        exit 1
    fi

    # Check if running as root (required for certbot)
    if [[ $EUID -ne 0 ]]; then
        log_error "Let's Encrypt setup requires root privileges"
        log_error "Please run with sudo or as root"
        exit 1
    fi

    # Get certificate
    certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive

    # Copy certificates to our directory
    local letsencrypt_dir="/etc/letsencrypt/live/$DOMAIN"
    cp "$letsencrypt_dir/fullchain.pem" "$CERT_DIR/certs/"
    cp "$letsencrypt_dir/privkey.pem" "$CERT_DIR/private/"
    cp "$letsencrypt_dir/chain.pem" "$CERT_DIR/certs/"

    # Set proper permissions
    chmod 600 "$CERT_DIR/private/privkey.pem"
    chmod 644 "$CERT_DIR/certs/fullchain.pem"
    chmod 644 "$CERT_DIR/certs/chain.pem"

    log_success "Let's Encrypt certificates installed"
}

# Generate DH parameters for better security
generate_dhparam() {
    log_info "Generating Diffie-Hellman parameters..."

    local dhparam_file="$CERT_DIR/dhparam/dhparam.pem"

    if [[ -f "$dhparam_file" ]] && [[ "$FORCE" != "true" ]]; then
        log_warn "DH parameters already exist. Use --force to regenerate."
        return 0
    fi

    openssl dhparam -out "$dhparam_file" 2048
    chmod 644 "$dhparam_file"

    log_success "DH parameters generated: $dhparam_file"
}

# Setup custom certificates
setup_custom_certs() {
    log_info "Setting up custom SSL certificates..."

    local cert_src="${CUSTOM_CERT:-}"
    local key_src="${CUSTOM_KEY:-}"

    if [[ -z "$cert_src" ]] || [[ -z "$key_src" ]]; then
        log_error "Custom certificate setup requires CUSTOM_CERT and CUSTOM_KEY environment variables"
        log_error "Example:"
        log_error "  export CUSTOM_CERT=/path/to/cert.pem"
        log_error "  export CUSTOM_KEY=/path/to/key.pem"
        exit 1
    fi

    if [[ ! -f "$cert_src" ]] || [[ ! -f "$key_src" ]]; then
        log_error "Certificate files not found:"
        log_error "  CERT: $cert_src"
        log_error "  KEY: $key_src"
        exit 1
    fi

    # Copy certificates
    cp "$cert_src" "$CERT_DIR/certs/custom.crt"
    cp "$key_src" "$CERT_DIR/private/custom.key"

    # Set proper permissions
    chmod 600 "$CERT_DIR/private/custom.key"
    chmod 644 "$CERT_DIR/certs/custom.crt"

    log_success "Custom certificates installed"
}

# Update environment configuration
update_env_config() {
    log_info "Updating environment configuration..."

    local env_file=".env.production"

    if [[ ! -f "$env_file" ]]; then
        log_warn "Environment file $env_file not found, creating..."
        touch "$env_file"
    fi

    # Update SSL paths in environment file
    if [[ "$SSL_TYPE" == "letsencrypt" ]]; then
        sed -i.bak '/SSL_CERT_PATH/d' "$env_file"
        sed -i.bak '/SSL_KEY_PATH/d' "$env_file"
        echo "SSL_CERT_PATH=$CERT_DIR/certs/fullchain.pem" >> "$env_file"
        echo "SSL_KEY_PATH=$CERT_DIR/private/privkey.pem" >> "$env_file"
    elif [[ "$SSL_TYPE" == "self-signed" ]]; then
        sed -i.bak '/SSL_CERT_PATH/d' "$env_file"
        sed -i.bak '/SSL_KEY_PATH/d' "$env_file"
        echo "SSL_CERT_PATH=$CERT_DIR/certs/selfsigned.crt" >> "$env_file"
        echo "SSL_KEY_PATH=$CERT_DIR/private/selfsigned.key" >> "$env_file"
    elif [[ "$SSL_TYPE" == "custom" ]]; then
        sed -i.bak '/SSL_CERT_PATH/d' "$env_file"
        sed -i.bak '/SSL_KEY_PATH/d' "$env_file"
        echo "SSL_CERT_PATH=$CERT_DIR/certs/custom.crt" >> "$env_file"
        echo "SSL_KEY_PATH=$CERT_DIR/private/custom.key" >> "$env_file"
    fi

    log_success "Environment configuration updated"
}

# Test SSL configuration
test_ssl_config() {
    log_info "Testing SSL configuration..."

    local cert_file=""
    local key_file=""

    case "$SSL_TYPE" in
        letsencrypt)
            cert_file="$CERT_DIR/certs/fullchain.pem"
            key_file="$CERT_DIR/private/privkey.pem"
            ;;
        self-signed)
            cert_file="$CERT_DIR/certs/selfsigned.crt"
            key_file="$CERT_DIR/private/selfsigned.key"
            ;;
        custom)
            cert_file="$CERT_DIR/certs/custom.crt"
            key_file="$CERT_DIR/private/custom.key"
            ;;
    esac

    # Test certificate validity
    if openssl x509 -in "$cert_file" -text -noout >/dev/null 2>&1; then
        log_success "Certificate is valid"
    else
        log_error "Certificate validation failed"
        return 1
    fi

    # Test private key
    if openssl rsa -in "$key_file" -check >/dev/null 2>&1; then
        log_success "Private key is valid"
    else
        log_error "Private key validation failed"
        return 1
    fi

    # Show certificate info
    log_info "Certificate Information:"
    openssl x509 -in "$cert_file" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)" | sed 's/^/  /'
}

# Generate SSL configuration for NGINX
generate_nginx_ssl_config() {
    log_info "Generating NGINX SSL configuration..."

    local nginx_ssl_file="./security/ssl/nginx_ssl.conf"

    cat > "$nginx_ssl_file" << EOF
# SSL Configuration for PetPlantr
# Generated by setup-ssl.sh on $(date)

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # SSL Certificate Configuration
    ssl_certificate $CERT_DIR/certs/fullchain.pem;
    ssl_certificate_key $CERT_DIR/private/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Diffie-Hellman Parameters
    ssl_dhparam $CERT_DIR/dhparam/dhparam.pem;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to PetPlantr API
    location / {
        proxy_pass http://petplantr:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}
EOF

    log_success "NGINX SSL configuration generated: $nginx_ssl_file"
}

# Setup auto-renewal for Let's Encrypt
setup_auto_renewal() {
    if [[ "$SSL_TYPE" != "letsencrypt" ]]; then
        return 0
    fi

    log_info "Setting up automatic certificate renewal..."

    local renewal_script="./scripts/renew-ssl.sh"

    cat > "$renewal_script" << 'EOF'
#!/bin/bash
# SSL Certificate Renewal Script
# Run this script to renew Let's Encrypt certificates

set -e

CERT_DIR="./security/ssl"
DOMAIN="localhost"  # Update this with your actual domain

echo "Renewing SSL certificates for $DOMAIN..."

# Renew certificates
certbot renew

# Reload services
if command -v docker >/dev/null 2>&1; then
    echo "Reloading Docker containers..."
    docker compose restart nginx
else
    echo "Please manually reload your web server"
fi

echo "SSL certificates renewed successfully"
EOF

    chmod +x "$renewal_script"

    # Setup cron job for renewal (if running as root)
    if [[ $EUID -eq 0 ]]; then
        log_info "Setting up cron job for automatic renewal..."
        (crontab -l 2>/dev/null; echo "0 12 * * * $PWD/scripts/renew-ssl.sh") | crontab -
        log_success "Automatic renewal configured (runs daily at 12:00)"
    else
        log_warn "Not running as root - automatic renewal not configured"
        log_info "To setup automatic renewal, run as root or add to cron manually:"
        log_info "  sudo crontab -e"
        log_info "  Add: 0 12 * * * $PWD/scripts/renew-ssl.sh"
    fi
}

# Main SSL setup function
main() {
    log_info "Starting SSL/TLS certificate setup for PetPlantr"
    log_info "Domain: $DOMAIN"
    log_info "SSL Type: $SSL_TYPE"

    create_cert_dirs

    case "$SSL_TYPE" in
        letsencrypt)
            setup_letsencrypt
            ;;
        self-signed)
            generate_self_signed
            ;;
        custom)
            setup_custom_certs
            ;;
        *)
            log_error "Invalid SSL type: $SSL_TYPE"
            log_error "Valid options: letsencrypt, self-signed, custom"
            exit 1
            ;;
    esac

    generate_dhparam
    update_env_config
    test_ssl_config
    generate_nginx_ssl_config
    setup_auto_renewal

    log_success "🎉 SSL/TLS setup completed successfully!"
    log_info ""
    log_info "📋 Next steps:"
    log_info "  1. Update your DNS to point to this server"
    log_info "  2. Restart your web server to load new certificates"
    log_info "  3. Test HTTPS access: https://$DOMAIN/api/v1/health"
    log_info ""
    log_info "🔒 SSL Certificate Details:"
    case "$SSL_TYPE" in
        letsencrypt)
            log_info "  Type: Let's Encrypt (Auto-renewing)"
            log_info "  Certificate: $CERT_DIR/certs/fullchain.pem"
            log_info "  Private Key: $CERT_DIR/private/privkey.pem"
            ;;
        self-signed)
            log_info "  Type: Self-signed (Development)"
            log_info "  Certificate: $CERT_DIR/certs/selfsigned.crt"
            log_info "  Private Key: $CERT_DIR/private/selfsigned.key"
            ;;
        custom)
            log_info "  Type: Custom certificates"
            log_info "  Certificate: $CERT_DIR/certs/custom.crt"
            log_info "  Private Key: $CERT_DIR/private/custom.key"
            ;;
    esac
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --type)
            SSL_TYPE="$2"
            shift 2
            ;;
        --cert-dir)
            CERT_DIR="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --domain DOMAIN     Domain name (default: localhost)"
            echo "  --email EMAIL       Email for Let's Encrypt (default: admin@petplantr.com)"
            echo "  --type TYPE         SSL type: letsencrypt, self-signed, custom (default: self-signed)"
            echo "  --cert-dir DIR      Certificate directory (default: ./security/ssl)"
            echo "  --force            Force regeneration of certificates"
            echo "  --help             Show this help"
            echo ""
            echo "Environment variables for custom certificates:"
            echo "  CUSTOM_CERT         Path to custom certificate file"
            echo "  CUSTOM_KEY          Path to custom private key file"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main setup
main