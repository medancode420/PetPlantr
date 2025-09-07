#!/bin/bash
# PetPlantr API Subdomain Setup Guide
# Sets up api.petplantr.com to front the FastAPI service

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
DOMAIN="petplantr.com"
API_SUBDOMAIN="api.petplantr.com"
SERVER_IP="76.76.21.21"  # Your FastAPI server IP
DNS_TTL="300"

echo "${BOLD}${BLUE}🌐 PetPlantr API Subdomain Setup${NC}"
echo "================================="
echo "Setting up: ${API_SUBDOMAIN}"
echo "Target IP: ${SERVER_IP}"
echo ""

# Step 1: Check current DNS status
echo "${BOLD}1. Current DNS Status${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dns() {
    local subdomain="$1"
    echo "Checking DNS for ${subdomain}..."
    
    if command -v dig >/dev/null 2>&1; then
        dig +short "$subdomain" A || echo "No A record found"
    elif command -v nslookup >/dev/null 2>&1; then
        nslookup "$subdomain" | grep "Address:" | tail -n1 || echo "No A record found"
    else
        echo "No DNS tools available (dig/nslookup)"
    fi
}

check_dns "$API_SUBDOMAIN"
echo ""

# Step 2: DNS Configuration Guide
echo "${BOLD}2. DNS Configuration Required${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Add this A record in your DNS provider (GoDaddy):"
echo ""
echo "${YELLOW}Record Type:${NC} A"
echo "${YELLOW}Name:${NC}        api"
echo "${YELLOW}Value:${NC}       ${SERVER_IP}"
echo "${YELLOW}TTL:${NC}         ${DNS_TTL} (5 minutes)"
echo ""
echo "${BOLD}Why ${SERVER_IP}?${NC}"
echo "This is Vercel's anycast IP that automatically routes traffic"
echo "to the correct project based on the requested hostname."
echo "Source: https://vercel.com/docs/projects/domains/add-a-domain"
echo ""
echo "${BOLD}Steps for GoDaddy:${NC}"
echo "1. Log into GoDaddy account"
echo "2. Go to 'My Products' → 'DNS'"
echo "3. Find ${DOMAIN} → 'Manage DNS'"
echo "4. Click 'Add Record'"
echo "5. Select 'A' record type"
echo "6. Enter 'api' in Name field"
echo "7. Enter '${SERVER_IP}' in Value field"
echo "8. Set TTL to 300 seconds"
echo "9. Click 'Save'"
echo ""
echo "${BOLD}Note:${NC} A records are required for Vercel subdomains."
echo "CNAMEs can be used for most subdomains, but A records"
echo "provide better performance with Vercel's edge network."
echo "Source: https://vercel.com/docs/projects/domains/add-a-domain"
echo ""

# Step 3: Test DNS propagation
echo "${BOLD}3. DNS Propagation Test${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_dns_propagation() {
    local max_attempts=10
    local attempt=1
    
    echo "Testing DNS propagation (max ${max_attempts} attempts)..."
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt ${attempt}/${max_attempts}:"
        
        if command -v dig >/dev/null 2>&1; then
            result=$(dig +short "$API_SUBDOMAIN" A)
        elif command -v nslookup >/dev/null 2>&1; then
            result=$(nslookup "$API_SUBDOMAIN" | grep "Address:" | tail -n1 | awk '{print $2}')
        else
            echo "No DNS tools available"
            return 1
        fi
        
        if [ "$result" = "$SERVER_IP" ]; then
            echo "${GREEN}✅ DNS propagated! ${API_SUBDOMAIN} → ${result}${NC}"
            return 0
        elif [ -n "$result" ]; then
            echo "${YELLOW}⚠️  Wrong IP: ${result} (expected: ${SERVER_IP})${NC}"
        else
            echo "${RED}❌ No DNS record found${NC}"
        fi
        
        if [ $attempt -lt $max_attempts ]; then
            echo "Waiting 30 seconds before retry..."
            sleep 30
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo "${RED}❌ DNS propagation timeout${NC}"
    return 1
}

# Step 4: FastAPI CORS Configuration
echo "${BOLD}4. FastAPI CORS Configuration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your FastAPI server needs to allow the new subdomain."
echo "Current CORS config should include:"
echo ""
echo "${YELLOW}ALLOWED_HOSTS:${NC}"
echo "  - petplantr.com"
echo "  - www.petplantr.com"
echo "  - api.petplantr.com  ${GREEN}← Add this${NC}"
echo ""
echo "${YELLOW}CORS Origins:${NC}"
echo "  - https://petplantr.com"
echo "  - https://www.petplantr.com"
echo "  - https://api.petplantr.com  ${GREEN}← Add this${NC}"
echo ""

# Step 5: SSL/HTTPS Setup
echo "${BOLD}5. SSL/HTTPS Setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "For production, ensure SSL certificate covers:"
echo "  - petplantr.com"
echo "  - www.petplantr.com"
echo "  - api.petplantr.com  ${GREEN}← New subdomain${NC}"
echo ""
echo "If using Let's Encrypt, run:"
echo "${YELLOW}certbot --expand -d petplantr.com -d www.petplantr.com -d api.petplantr.com${NC}"
echo ""

# Step 6: Validation
echo "${BOLD}6. Validation${NC}"
echo "━━━━━━━━━━━━━━━━━━━━"

if [ "${1:-}" = "--test-now" ]; then
    echo "Testing DNS propagation now..."
    if test_dns_propagation; then
        echo ""
        echo "${GREEN}✅ DNS setup successful!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Update validation script to use api.petplantr.com"
        echo "2. Test API endpoints: https://api.petplantr.com/api/v1/health"
        echo "3. Update frontend to use new API URL"
        echo ""
        echo "Run validation:"
        echo "${YELLOW}./validate-production-pipeline.sh${NC}"
    else
        echo ""
        echo "${RED}❌ DNS not ready yet${NC}"
        echo ""
        echo "Check:"
        echo "1. DNS record was added correctly"
        echo "2. TTL has expired (5+ minutes)"
        echo "3. No typos in subdomain or IP"
    fi
else
    echo "To test DNS propagation:"
    echo "${YELLOW}$0 --test-now${NC}"
    echo ""
    echo "Manual test:"
    echo "${YELLOW}curl -I https://api.petplantr.com/api/v1/health${NC}"
fi

echo ""
echo "${BOLD}${GREEN}🎉 Setup guide complete!${NC}"
echo ""
echo "Summary:"
echo "• Add A record: api → ${SERVER_IP}"
echo "• Wait 5-30 minutes for propagation"
echo "• Update FastAPI CORS settings"
echo "• Test with validation script"
echo ""
echo "Questions? Check: https://support.godaddy.com/help/add-an-a-record-19238"
