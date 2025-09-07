#!/bin/bash

# 🌐 Quick DNS Status Check for PetPlantr.com

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "${BLUE}🌐 PetPlantr DNS Quick Status${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test each domain
domains=("petplantr.com" "www.petplantr.com" "api.petplantr.com")

for domain in "${domains[@]}"; do
    echo -n "$domain: "
    
    # Quick DNS lookup
    ip=$(dig +short A $domain 2>/dev/null | head -n1)
    
    if [ -n "$ip" ]; then
        echo "${GREEN}✅ $ip${NC}"
    else
        echo "${RED}❌ Not resolved${NC}"
    fi
done

echo ""
echo "For detailed testing, run: ${BLUE}./test-dns.sh${NC}"
echo "For configuration help, run: ${BLUE}./configure-dns-interactive.sh${NC}"
echo ""
