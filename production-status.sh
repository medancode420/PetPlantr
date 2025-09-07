#!/usr/bin/env bash
# production-status.sh - Check production readiness and deployment status

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }

# Check if file exists
check_file() {
    local file="$1"
    local description="$2"

    if [[ -f "$file" ]]; then
        echo -e "✅ $description: ${GREEN}Found${NC}"
        return 0
    else
        echo -e "❌ $description: ${RED}Missing${NC}"
        return 1
    fi
}

# Check if directory exists
check_dir() {
    local dir="$1"
    local description="$2"

    if [[ -d "$dir" ]]; then
        echo -e "✅ $description: ${GREEN}Found${NC}"
        return 0
    else
        echo -e "❌ $description: ${RED}Missing${NC}"
        return 1
    fi
}

# Check Docker
check_docker() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        echo -e "✅ Docker: ${GREEN}Running${NC}"
        return 0
    else
        echo -e "❌ Docker: ${RED}Not available or not running${NC}"
        return 1
    fi
}

# Check Docker Compose
check_docker_compose() {
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        echo -e "✅ Docker Compose: ${GREEN}Available${NC}"
        return 0
    else
        echo -e "❌ Docker Compose: ${RED}Not available${NC}"
        return 1
    fi
}

# Main status check
main() {
    echo "🔍 PetPlantr Production Readiness Check"
    echo "========================================"
    echo ""

    local total_checks=0
    local passed_checks=0

    # Infrastructure Checks
    echo "🏗️  Infrastructure:"
    ((total_checks++))
    check_docker && ((passed_checks++))
    ((total_checks++))
    check_docker_compose && ((passed_checks++))

    echo ""

    # Configuration Files
    echo "📄 Configuration Files:"
    local config_files=(
        ".env.production:.env.production (copy from template)"
        ".env.security:.env.security (copy from template)"
        "docker-compose.yml:Docker Compose configuration"
        "Dockerfile.production:Production Dockerfile"
        "requirements-production.txt:Production requirements"
        ".env.production.template:Production environment template"
        ".env.security.template:Security environment template"
    )

    for config in "${config_files[@]}"; do
        IFS=':' read -r file description <<< "$config"
        ((total_checks++))
        check_file "$file" "$description" && ((passed_checks++))
    done

    echo ""

    # Security Setup
    echo "🔒 Security Setup:"
    local security_dirs=(
        "security/ssl/certs:SSL certificates directory"
        "security/ssl/private:SSL private keys directory"
    )

    for dir_check in "${security_dirs[@]}"; do
        IFS=':' read -r dir description <<< "$dir_check"
        ((total_checks++))
        check_dir "$dir" "$description" && ((passed_checks++))
    done

    # Check for SSL certificates
    if [[ -d "security/ssl/certs" ]]; then
        if [[ -f "security/ssl/certs/fullchain.pem" ]]; then
            echo -e "✅ SSL Certificate: ${GREEN}Found${NC}"
            ((passed_checks++))
        else
            echo -e "❌ SSL Certificate: ${RED}Missing fullchain.pem${NC}"
        fi
        ((total_checks++))
    fi

    echo ""

    # Scripts and Tools
    echo "🛠️  Scripts and Tools:"
    local scripts=(
        "deploy-production.sh:Production deployment script"
        "setup-monitoring.sh:Monitoring setup script"
        "PRODUCTION_DEPLOYMENT_GUIDE.md:Deployment guide"
    )

    for script in "${scripts[@]}"; do
        IFS=':' read -r file description <<< "$script"
        ((total_checks++))
        check_file "$file" "$description" && ((passed_checks++))
    done

    echo ""

    # Calculate readiness percentage
    local readiness=$(( passed_checks * 100 / total_checks ))

    echo "📊 Production Readiness: $readiness% ($passed_checks/$total_checks checks passed)"
    echo ""

    # Readiness assessment
    if [[ $readiness -ge 90 ]]; then
        log_success "🎉 Ready for production deployment!"
        echo ""
        echo "🚀 Next steps:"
        echo "1. Configure your environment variables in .env.production and .env.security"
        echo "2. Setup SSL certificates (see PRODUCTION_DEPLOYMENT_GUIDE.md)"
        echo "3. Run: ./deploy-production.sh"
        echo "4. Optional: Setup monitoring with ./setup-monitoring.sh"
    elif [[ $readiness -ge 70 ]]; then
        log_warn "⚠️  Mostly ready, but some configuration needed"
        echo ""
        echo "📋 Missing items:"
        [[ ! -f ".env.production" ]] && echo "  - Create .env.production from template"
        [[ ! -f ".env.security" ]] && echo "  - Create .env.security from template"
        [[ ! -d "security/ssl/certs" ]] && echo "  - Setup SSL certificates"
    else
        log_error "❌ Not ready for production"
        echo ""
        echo "🔧 Critical missing items:"
        ! check_docker && echo "  - Install and start Docker"
        ! check_docker_compose && echo "  - Install Docker Compose"
        [[ ! -f "docker-compose.yml" ]] && echo "  - Docker Compose configuration missing"
        [[ ! -f "Dockerfile.production" ]] && echo "  - Production Dockerfile missing"
    fi

    echo ""
    echo "📖 For detailed instructions, see: PRODUCTION_DEPLOYMENT_GUIDE.md"
}

# Run main check
main
