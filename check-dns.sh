#!/bin/bash
# check-dns.sh: Monitors AWS EKS DNS propagation for the cluster.

# Set variables (user-provided or default)
CLUSTER_NAME="${1:-petplantr-production}"
REGION="${2:-us-east-1}"
PROJECT_DIR="${3:-/Users/medan/Downloads/PetPlantr}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 PetPlantr DNS Propagation Monitor${NC}"
echo "======================================"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Project Directory: $PROJECT_DIR"
echo ""

# Change to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ Error: Could not change to directory $PROJECT_DIR${NC}"
    exit 1
}

# Fetch endpoint if not set
echo -e "${YELLOW}📡 Fetching cluster endpoint from AWS...${NC}"
ENDPOINT=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query "cluster.endpoint" --output text 2>/dev/null)

if [ -z "$ENDPOINT" ] || [ "$ENDPOINT" = "None" ]; then
    echo -e "${RED}❌ Error: Could not fetch cluster endpoint.${NC}"
    echo "   - Check AWS credentials: aws configure"
    echo "   - Verify cluster name: $CLUSTER_NAME"
    echo "   - Verify region: $REGION"
    echo "   - Ensure cluster exists: aws eks list-clusters --region $REGION"
    exit 1
fi

HOST=$(echo "$ENDPOINT" | sed -e 's|^https://||' -e 's|/.*$||')
echo -e "${GREEN}✅ Cluster endpoint found: $ENDPOINT${NC}"
echo -e "${GREEN}✅ Host to monitor: $HOST${NC}"
echo ""

# Poll loop (every 5 min, max 30 min = 6 attempts)
echo -e "${YELLOW}⏳ Starting DNS propagation monitoring...${NC}"
echo "   Polling every 5 minutes for up to 30 minutes (6 attempts)"
echo ""

for i in {1..6}; do
    echo -e "${BLUE}🔍 Attempt $i/6 - Checking DNS resolution...${NC}"

    if nslookup "$HOST" 2>/dev/null | grep -A 5 "Non-authoritative answer" | grep -q "Address:" | grep -v "53#"; then
        echo ""
        echo -e "${GREEN}🎉 SUCCESS: DNS resolved for $HOST!${NC}"
        echo -e "${GREEN}🚀 You can now proceed with kubectl access.${NC}"
        echo ""
        echo -e "${YELLOW}💡 Next steps:${NC}"
        echo "   1. Update kubeconfig: aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION"
        echo "   2. Test connection: kubectl get nodes"
        echo "   3. Deploy application: kubectl apply -f k8s/"
        echo ""
        exit 0
    fi

    if [ $i -eq 6 ]; then
        echo -e "${RED}❌ DNS propagation timeout after 30 minutes.${NC}"
        echo ""
        echo -e "${YELLOW}🔧 Troubleshooting options:${NC}"
        echo "   1. Try manual DNS check: nslookup $HOST"
        echo "   2. Use direct IP access (see README)"
        echo "   3. Check AWS console for cluster status"
        echo "   4. Wait longer (sometimes takes 45-60 min)"
        echo ""
        exit 1
    fi

    echo -e "${YELLOW}⏳ DNS not resolved yet. Waiting 5 minutes...${NC}"
    echo "   Next check at: $(date -v+5M '+%H:%M:%S')"
    echo ""
    sleep 300
done
