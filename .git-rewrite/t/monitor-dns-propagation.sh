#!/bin/bash
# Monitor DNS propagation for api.petplantr.com
# Usage: ./monitor-dns-propagation.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOMAIN="api.petplantr.com"
TARGET_IP="76.76.21.21"
CHECK_INTERVAL=30  # seconds

echo "🌐 Monitoring DNS Propagation for ${DOMAIN}"
echo "Target IP: ${TARGET_IP}"
echo "Check interval: ${CHECK_INTERVAL} seconds"
echo "Press Ctrl+C to stop"
echo ""

check_dns() {
    if command -v dig >/dev/null 2>&1; then
        dig +short "$DOMAIN" A 2>/dev/null
    elif command -v nslookup >/dev/null 2>&1; then
        nslookup "$DOMAIN" 2>/dev/null | grep "Address:" | tail -n1 | awk '{print $2}'
    else
        echo "No DNS tools available"
        return 1
    fi
}

test_api_endpoint() {
    local url="https://${DOMAIN}/api/health"
    local response=$(curl -s --max-time 5 "$url" 2>/dev/null)
    
    if echo "$response" | grep -q '"status":"ok"'; then
        echo "✅ API endpoint responding"
        return 0
    else
        echo "❌ API endpoint not responding"
        return 1
    fi
}

attempt=1
while true; do
    timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] Check #$attempt:"
    
    # Check DNS resolution
    dns_result=$(check_dns)
    if [ "$dns_result" = "$TARGET_IP" ]; then
        echo "  ✅ DNS: ${DOMAIN} → ${dns_result}"
        
        # Test API endpoint
        if test_api_endpoint; then
            echo ""
            echo "${GREEN}🎉 DNS propagated and API is live!${NC}"
            echo ""
            echo "Next steps:"
            echo "  1. Run: ./validate-production-pipeline.sh"
            echo "  2. Test: https://${DOMAIN}/api/health"
            echo "  3. Update frontend to use new API endpoint"
            break
        else
            echo "  ⏳ DNS ready, waiting for API..."
        fi
    elif [ -n "$dns_result" ]; then
        echo "  ⚠️  DNS: ${DOMAIN} → ${dns_result} (expected: ${TARGET_IP})"
    else
        echo "  ❌ DNS: No A record found for ${DOMAIN}"
    fi
    
    echo ""
    attempt=$((attempt + 1))
    sleep $CHECK_INTERVAL
done
