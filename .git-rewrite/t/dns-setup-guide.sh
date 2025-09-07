#!/bin/bash

# 🌐 DNS Configuration Helper for PetPlantr.com
# Interactive guide to set up DNS records

echo "🌐 DNS Configuration for PetPlantr.com"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "${BLUE}Required DNS Records:${NC}"
echo "--------------------"
echo ""

echo "${GREEN}📋 Copy these DNS records to your domain registrar:${NC}"
echo ""

cat << 'EOF'
┌─────────────────────┬──────┬─────────────────────────┬─────┐
│ Name                │ Type │ Value                   │ TTL │
├─────────────────────┼──────┼─────────────────────────┼─────┤
│ petplantr.com       │  A   │ [YOUR_FRONTEND_IP]      │ 300 │
│ www.petplantr.com   │  A   │ [YOUR_FRONTEND_IP]      │ 300 │
│ api.petplantr.com   │  A   │ [YOUR_API_SERVER_IP]    │ 300 │
└─────────────────────┴──────┴─────────────────────────┴─────┘

Optional CDN:
┌─────────────────────┬──────┬─────────────────────────┬─────┐
│ cdn.petplantr.com   │CNAME │ [CDN_ENDPOINT]          │ 300 │
└─────────────────────┴──────┴─────────────────────────┴─────┘
EOF

echo ""
echo "${YELLOW}💡 Replace [YOUR_FRONTEND_IP] and [YOUR_API_SERVER_IP] with your actual server IPs${NC}"
echo ""

# Check if we can detect current IP
echo "${BLUE}🔍 Your current public IP (for reference):${NC}"
PUBLIC_IP=$(curl -s -4 ifconfig.me 2>/dev/null || echo "Unable to detect")
echo "   $PUBLIC_IP"
echo ""

echo "${BLUE}📝 Step-by-step DNS setup:${NC}"
echo "-------------------------"
echo ""

echo "${GREEN}1. Login to your domain registrar${NC}"
echo "   (GoDaddy, Namecheap, Cloudflare, etc.)"
echo ""

echo "${GREEN}2. Navigate to DNS Management${NC}"
echo "   Look for 'DNS', 'DNS Management', or 'DNS Records'"
echo ""

echo "${GREEN}3. Add the following A records:${NC}"
echo ""
echo "   Record 1:"
echo "   ┌─────────────────┬─────────────────────┐"
echo "   │ Type: A         │ Name: @             │"
echo "   │ Value: [IP]     │ TTL: 300            │"
echo "   └─────────────────┴─────────────────────┘"
echo ""
echo "   Record 2:"
echo "   ┌─────────────────┬─────────────────────┐"
echo "   │ Type: A         │ Name: www           │"
echo "   │ Value: [IP]     │ TTL: 300            │"
echo "   └─────────────────┴─────────────────────┘"
echo ""
echo "   Record 3:"
echo "   ┌─────────────────┬─────────────────────┐"
echo "   │ Type: A         │ Name: api           │"
echo "   │ Value: [API_IP] │ TTL: 300            │"
echo "   └─────────────────┴─────────────────────┘"
echo ""

echo "${GREEN}4. Save your DNS changes${NC}"
echo "   Changes may take 5-60 minutes to propagate"
echo ""

echo "${BLUE}🧪 DNS Verification Commands:${NC}"
echo "----------------------------"
echo ""

cat << 'EOF'
# Check A records
dig A petplantr.com
dig A www.petplantr.com  
dig A api.petplantr.com

# Check from Google DNS
nslookup petplantr.com 8.8.8.8
nslookup api.petplantr.com 8.8.8.8

# Online DNS checker
# https://dnschecker.org/#A/petplantr.com
EOF

echo ""
echo "${BLUE}🌍 Provider-Specific Instructions:${NC}"
echo "---------------------------------"
echo ""

# Generate provider-specific instructions
echo "${GREEN}Cloudflare:${NC}"
cat << 'EOF'
1. Login to Cloudflare dashboard
2. Select your domain
3. Go to DNS > Records
4. Click "Add record"
5. Add A records as shown above
6. Set Proxy status to "Proxied" (orange cloud) for CDN benefits
EOF

echo ""
echo "${GREEN}GoDaddy:${NC}"
cat << 'EOF'
1. Login to GoDaddy account
2. Go to My Products > DNS
3. Click on your domain
4. Click "Add" under Records
5. Select "A" record type
6. Add records as shown above
EOF

echo ""
echo "${GREEN}Namecheap:${NC}"
cat << 'EOF'
1. Login to Namecheap account
2. Go to Domain List
3. Click "Manage" next to your domain
4. Go to "Advanced DNS" tab
5. Add "A Record" entries as shown above
EOF

echo ""
echo "${GREEN}AWS Route 53:${NC}"
cat << 'EOF'
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch '{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "petplantr.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "YOUR_IP"}]
      }
    },
    {
      "Action": "CREATE", 
      "ResourceRecordSet": {
        "Name": "api.petplantr.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "YOUR_API_IP"}]
      }
    }
  ]
}'
EOF

echo ""
echo "${BLUE}⏱️  DNS Propagation Timeline:${NC}"
echo "-----------------------------"
echo "• Immediately: Changes saved to your DNS provider"
echo "• 5-15 minutes: Most global DNS servers updated"
echo "• 30-60 minutes: Full global propagation"
echo "• Up to 24 hours: Some slower DNS servers (rare)"
echo ""

echo "${BLUE}🔧 After DNS Propagation:${NC}"
echo "-------------------------"
echo "1. Run: ./deploy-petplantr.sh"
echo "2. SSL certificates will be automatically obtained"
echo "3. Test: https://petplantr.com"
echo "4. Test API: https://api.petplantr.com/healthz"
echo ""

echo "${GREEN}✅ DNS Configuration Complete!${NC}"
echo "Next step: Wait for propagation, then deploy!"
