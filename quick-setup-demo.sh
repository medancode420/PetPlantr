#!/usr/bin/env bash
# quick-setup-demo.sh - Quick demonstration of production setup tools
# Shows how to use the new production enhancement scripts

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 PetPlantr Production Setup Demo${NC}"
echo "=================================="
echo

# Check if scripts exist
if [[ ! -f "setup-ssl.sh" ]] || [[ ! -f "enable-monitoring.sh" ]] || [[ ! -f "production-pipeline.sh" ]]; then
    echo -e "${RED}❌ Production scripts not found. Please run the setup first.${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Available Production Tools:${NC}"
echo "1. setup-ssl.sh - SSL/TLS certificate setup"
echo "2. enable-monitoring.sh - Docker monitoring stack"
echo "3. production-pipeline.sh - Complete production deployment"
echo

echo -e "${GREEN}💡 Quick Start Examples:${NC}"
echo

echo -e "${BLUE}Example 1: Quick SSL Setup${NC}"
echo "  ./setup-ssl.sh --type self-signed --domain localhost"
echo

echo -e "${BLUE}Example 2: Enable Monitoring${NC}"
echo "  ./enable-monitoring.sh --prometheus-port 9090 --grafana-port 3000"
echo

echo -e "${BLUE}Example 3: Full Production Pipeline${NC}"
echo "  ./production-pipeline.sh --domain petplantr.com --ssl-type letsencrypt --canary-percentage 10"
echo

echo -e "${BLUE}Example 4: Development Setup${NC}"
echo "  ./production-pipeline.sh --domain localhost --ssl-type self-signed --canary-percentage 100 --no-monitoring"
echo

echo -e "${YELLOW}🔧 Script Options:${NC}"
echo

echo -e "${GREEN}setup-ssl.sh options:${NC}"
./setup-ssl.sh --help | sed 's/^/  /'
echo

echo -e "${GREEN}enable-monitoring.sh options:${NC}"
./enable-monitoring.sh --help | sed 's/^/  /'
echo

echo -e "${GREEN}production-pipeline.sh options:${NC}"
./production-pipeline.sh --help | sed 's/^/  /'
echo

echo -e "${BLUE}🎯 Recommended Production Setup:${NC}"
echo "1. Setup SSL certificates:"
echo "   ./setup-ssl.sh --type letsencrypt --domain yourdomain.com --email admin@yourdomain.com"
echo
echo "2. Enable monitoring:"
echo "   ./enable-monitoring.sh"
echo
echo "3. Run full production deployment:"
echo "   ./production-pipeline.sh --domain yourdomain.com --ssl-type letsencrypt"
echo

echo -e "${YELLOW}📊 What These Tools Provide:${NC}"
echo "✅ Automated SSL certificate management (self-signed, Let's Encrypt, custom)"
echo "✅ Complete monitoring stack (Prometheus + Grafana + Alertmanager)"
echo "✅ Production-ready deployment pipeline with canary releases"
echo "✅ Health checks and validation at each step"
echo "✅ Automatic configuration generation"
echo "✅ Comprehensive deployment reports"
echo "✅ Rollback capabilities"
echo

echo -e "${GREEN}🎉 Ready to enhance your PetPlantr production deployment!${NC}"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "1. Choose your SSL strategy (self-signed for testing, Let's Encrypt for production)"
echo "2. Run the setup scripts in order"
echo "3. Monitor your deployment with the new dashboards"
echo "4. Gradually increase canary traffic as confidence grows"