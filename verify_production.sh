#!/bin/bash
# PetPlantr Production Verification Script
# Tests all production endpoints and services

DOMAIN="${1:-petplantr.com}"
SERVER_IP="${SERVER_IP:-96.245.127.40}"

echo "🔍 Verifying PetPlantr production setup for $DOMAIN"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_endpoint() {
    local name="$1"
    local url="$2"
    local expected="${3:-200}"

    echo -n "Testing $name... "
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

echo "🌐 Domain & DNS Tests:"
echo "---------------------"
check_endpoint "DNS Resolution" "https://$DOMAIN" "200|301"
check_endpoint "API Health" "https://$DOMAIN/api/v1/health" "200"
check_endpoint "HTTP Redirect" "http://$DOMAIN" "301"

echo ""
echo "🔒 SSL & Security Tests:"
echo "-----------------------"
# SSL test would require openssl
echo "SSL Certificate: Manual check required"
echo "Security Headers: Manual check required"

echo ""
echo "📊 Monitoring Tests:"
echo "-------------------"
check_endpoint "Prometheus" "http://localhost:9090/-/healthy" "200"
check_endpoint "Grafana" "http://localhost:3030/api/health" "200"
check_endpoint "System Monitor" "http://localhost:9100/health" "200"

echo ""
echo "🔧 Service Tests:"
echo "----------------"
check_endpoint "API Server" "http://localhost:8000/api/v1/health" "200"

echo ""
echo "📁 File System Tests:"
echo "--------------------"
[ -d "./models" ] && echo -e "Models Directory: ${GREEN}✅ PASS${NC}" || echo -e "Models Directory: ${RED}❌ FAIL${NC}"
[ -d "./ssl" ] && echo -e "SSL Directory: ${GREEN}✅ PASS${NC}" || echo -e "SSL Directory: ${RED}❌ FAIL${NC}"
[ -d "./backups" ] && echo -e "Backups Directory: ${GREEN}✅ PASS${NC}" || echo -e "Backups Directory: ${RED}❌ FAIL${NC}"

echo ""
echo "🎯 Verification Complete!"
echo "========================"
echo "Run this script after domain setup to verify production readiness"
echo "Usage: ./verify_production.sh [domain]"
