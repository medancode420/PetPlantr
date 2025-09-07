#!/bin/bash

# 🌐 PetPlantr.com Production Deployment Script
# Automates the deployment process for petplantr.com

set -e  # Exit on any error

echo "🚀 Starting PetPlantr.com Production Deployment"
echo "=============================================="
echo ""

# Configuration
DOMAIN="petplantr.com"
API_DOMAIN="api.petplantr.com"
DEPLOY_DIR="/var/www/petplantr"
BACKUP_DIR="/var/backups/petplantr"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
    
    # Check required commands
    for cmd in nginx npm node python3 uvicorn; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is not installed"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    if [ -d "$DEPLOY_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        BACKUP_NAME="petplantr-backup-$(date +%Y%m%d-%H%M%S)"
        tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$DEPLOY_DIR" .
        log_success "Backup created: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
    else
        log_warning "No existing deployment found, skipping backup"
    fi
}

# Deploy frontend
deploy_frontend() {
    log_info "Deploying frontend..."
    
    # Install dependencies
    cd frontend
    npm ci --production
    
    # Build for production
    npm run build
    
    # Copy to deployment directory
    mkdir -p "$DEPLOY_DIR/frontend"
    rsync -av --delete .next/ "$DEPLOY_DIR/frontend/.next/"
    rsync -av --delete public/ "$DEPLOY_DIR/frontend/public/"
    cp package.json "$DEPLOY_DIR/frontend/"
    cp -r node_modules "$DEPLOY_DIR/frontend/"
    
    log_success "Frontend deployed"
}

# Deploy API
deploy_api() {
    log_info "Deploying API..."
    
    # Copy API files
    mkdir -p "$DEPLOY_DIR/api"
    cp api_server_minimal.py "$DEPLOY_DIR/api/"
    cp requirements-production.txt "$DEPLOY_DIR/api/requirements.txt"
    
    # Install Python dependencies
    cd "$DEPLOY_DIR/api"
    python3 -m pip install -r requirements.txt
    
    log_success "API deployed"
}

# Configure Nginx
configure_nginx() {
    log_info "Configuring Nginx..."
    
    # Copy Nginx configuration
    cp nginx-petplantr.conf /etc/nginx/sites-available/petplantr.com
    
    # Enable site
    ln -sf /etc/nginx/sites-available/petplantr.com /etc/nginx/sites-enabled/
    
    # Test configuration
    nginx -t
    
    log_success "Nginx configured"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    if command -v certbot &> /dev/null; then
        # Using Let's Encrypt
        certbot certonly --nginx -d $DOMAIN -d www.$DOMAIN -d $API_DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
        log_success "SSL certificates obtained"
    else
        log_warning "Certbot not found. Please install SSL certificates manually"
    fi
}

# Setup systemd services
setup_services() {
    log_info "Setting up systemd services..."
    
    # Frontend service
    cat > /etc/systemd/system/petplantr-frontend.service << EOF
[Unit]
Description=PetPlantr Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$DEPLOY_DIR/frontend
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_API_BASE_URL=https://$API_DOMAIN
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # API service
    cat > /etc/systemd/system/petplantr-api.service << EOF
[Unit]
Description=PetPlantr API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$DEPLOY_DIR/api
Environment=NODE_ENV=production
Environment=ENABLE_PRODUCTION_AI=true
Environment=PETPLANTR_MODEL_DIR=$DEPLOY_DIR/models
ExecStart=/usr/local/bin/uvicorn api_server_minimal:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable petplantr-frontend petplantr-api
    
    log_success "Systemd services configured"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start API
    systemctl restart petplantr-api
    sleep 5
    
    # Start frontend
    systemctl restart petplantr-frontend
    sleep 5
    
    # Restart Nginx
    systemctl restart nginx
    
    log_success "Services started"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."
    
    # Check if services are running
    if systemctl is-active --quiet petplantr-api; then
        log_success "API service is running"
    else
        log_error "API service failed to start"
        return 1
    fi
    
    if systemctl is-active --quiet petplantr-frontend; then
        log_success "Frontend service is running"
    else
        log_error "Frontend service failed to start"
        return 1
    fi
    
    # Check health endpoints
    sleep 10  # Give services time to start
    
    if curl -f -s http://localhost:8000/healthz > /dev/null; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    if curl -f -s http://localhost:3000 > /dev/null; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    log_success "Deployment validation passed"
}

# Main deployment function
main() {
    echo "🌐 Domain: $DOMAIN"
    echo "🔗 API Domain: $API_DOMAIN"
    echo "📁 Deploy Directory: $DEPLOY_DIR"
    echo ""
    
    check_prerequisites
    create_backup
    deploy_frontend
    deploy_api
    configure_nginx
    setup_ssl
    setup_services
    start_services
    validate_deployment
    
    echo ""
    echo "🎉 PetPlantr.com deployment completed successfully!"
    echo "================================================="
    echo ""
    echo "🌐 Frontend: https://$DOMAIN"
    echo "🔗 API: https://$API_DOMAIN"
    echo "📊 Metrics: https://$API_DOMAIN/metrics"
    echo "🏥 Health: https://$API_DOMAIN/healthz"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Test the website: https://$DOMAIN"
    echo "   2. Set up monitoring dashboards"
    echo "   3. Configure backups"
    echo "   4. Update DNS if needed"
    echo ""
    log_success "Ready for production traffic! 🚀"
}

# Run deployment
main "$@"
