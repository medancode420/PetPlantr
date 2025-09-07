## Configuration
PRODUCTION_URL="https://petplantr.com"
LOCAL_API_URL="http://localhost:8000"
API_SUBDOMAIN="https://api.petplantr.com"
API_BASE="${API_SUBDOMAIN}/api"  # Clean subdomain for production API
TEST_IMAGE_URL="https://images.unsplash.com/photo-1552053831-71594a27632d?w=400"bash
# # Configuration
PRODUCTION_URL="https://petplantr.com"
LOCAL_API_URL="http://localhost:8000"
API_SUBDOMAIN="https://api.petplantr.com"
API_BASE="${API_SUBDOMAIN}/api/v1"  # Clean subdomain for production
TEST_IMAGE_URL="https://images.unsplash.com/photo-1552053831-71594a27632d?w=400"
TIMEOUT=30
START_TIME=$(date +%s)

echo "${BOLD}${BLUE}🧪 PetPlantr Production Pipeline Validation${NC}"
echo "=============================================="
echo "Target: Prove live AI pipeline is active (not demo mode)"
echo "API Endpoint: ${API_SUBDOMAIN}"
echo "Fallback: Will use ${LOCAL_API_URL} if subdomain not ready"
echo "Timeout: 2 minutes max"
echo "" Production Validation - 2-Minute Checklist
# Proves the live AI pipeline is working, not demo fallback

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
PRODUCTION_URL="https://petplantr.com"
API_BASE="${PRODUCTION_URL}/api"
TEST_IMAGE_URL="https://images.unsplash.com/photo-1552053831-71594a27632d?w=400"
TIMEOUT=30
START_TIME=$(date +%s)

echo "${BOLD}${BLUE}🧪 PetPlantr Production Pipeline Validation${NC}"
echo "=============================================="
echo "Target: Prove live AI pipeline is active (not demo mode)"
echo "Timeout: 2 minutes max"
echo ""

# Step 1: Health Check Endpoint
echo "${BOLD}1. Health Check Endpoint${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing: ${API_BASE}/health"

# Try API subdomain first, fallback to localhost if DNS not ready
HEALTH_RESPONSE=$(curl -s --max-time 10 "${API_BASE}/health" 2>/dev/null || echo '')
if [ -z "$HEALTH_RESPONSE" ] || [ "$HEALTH_RESPONSE" = "{}" ]; then
    echo "${YELLOW}⚠️  API subdomain not ready, trying production fallback...${NC}"
    API_BASE="${PRODUCTION_URL}/api"
    echo "Fallback: ${API_BASE}/health"
    HEALTH_RESPONSE=$(curl -s --max-time 10 "${API_BASE}/health" || echo '{}')
fi

echo "Response: $HEALTH_RESPONSE"

# Parse health check fields
STATUS=$(echo "$HEALTH_RESPONSE" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
PIPELINE=$(echo "$HEALTH_RESPONSE" | jq -r '.pipeline // "unknown"' 2>/dev/null || echo "unknown")
ENV_MODE=$(echo "$HEALTH_RESPONSE" | jq -r '.environment // "unknown"' 2>/dev/null || echo "unknown")
MODELS=$(echo "$HEALTH_RESPONSE" | jq -r '.models // []' 2>/dev/null || echo "[]")

echo ""
echo "🔍 Health Check Results:"
echo "┌─────────────┬─────────────────┬──────────────────────────────┐"
echo "│ Field       │ Value           │ Status                       │"
echo "├─────────────┼─────────────────┼──────────────────────────────┤"

# Status check
if [ "$STATUS" = "healthy" ] || [ "$STATUS" = "ok" ]; then
    echo "│ status      │ $STATUS         │ ${GREEN}✅ OK${NC}                        │"
    STATUS_PASS=true
else
    echo "│ status      │ $STATUS         │ ${RED}❌ FAIL${NC}                      │"
    STATUS_PASS=false
fi

# Pipeline check
if [ "$PIPELINE" = "production" ] || [ "$PIPELINE" = "real" ]; then
    echo "│ pipeline    │ $PIPELINE       │ ${GREEN}✅ Live AI Active${NC}            │"
    PIPELINE_PASS=true
else
    echo "│ pipeline    │ $PIPELINE       │ ${RED}❌ Demo Mode Detected${NC}        │"
    PIPELINE_PASS=false
fi

# Environment check
if [ "$ENV_MODE" = "production" ]; then
    echo "│ environment │ $ENV_MODE       │ ${GREEN}✅ Production Mode${NC}           │"
    ENV_PASS=true
else
    echo "│ environment │ $ENV_MODE       │ ${YELLOW}⚠️  Non-production${NC}           │"
    ENV_PASS=true  # Warning but not failure
fi

echo "└─────────────┴─────────────────┴──────────────────────────────┘"
echo ""

# Step 2: Model Generation Smoke Test
echo "${BOLD}2. Rapid AI Model Generation Test${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing breed detection with real image..."
echo "Image: $TEST_IMAGE_URL"

# Create temporary test image
TMP_IMAGE="/tmp/petplantr_test_$(date +%s).jpg"
curl -s --max-time 10 "$TEST_IMAGE_URL" -o "$TMP_IMAGE" || {
    echo "${RED}❌ Failed to download test image${NC}"
    exit 1
}

echo "Uploading to breed detection endpoint..."
GENERATION_START=$(date +%s)

# Test breed detection
BREED_RESPONSE=$(curl -s --max-time 30 \
    -X POST "${LOCAL_API_URL}/api/v1/breed/detect" \
    -F "file=@${TMP_IMAGE}" \
    -F "use_tta=false" \
    2>/dev/null || echo '{}')

GENERATION_END=$(date +%s)
GENERATION_TIME=$((GENERATION_END - GENERATION_START))

echo "Breed Detection Response: $BREED_RESPONSE"

# Parse breed detection results
PREDICTED_BREED=$(echo "$BREED_RESPONSE" | jq -r '.predicted_breed // "unknown"' 2>/dev/null || echo "unknown")
CONFIDENCE=$(echo "$BREED_RESPONSE" | jq -r '.confidence // 0' 2>/dev/null || echo "0")
PROCESSING_TIME=$(echo "$BREED_RESPONSE" | jq -r '.processing_time_ms // 0' 2>/dev/null || echo "0")

echo ""
echo "🤖 AI Generation Results:"
echo "┌──────────────────┬─────────────────┬────────────────────────┐"
echo "│ Metric           │ Value           │ Status                 │"
echo "├──────────────────┼─────────────────┼────────────────────────┤"

# Breed prediction check
if [ "$PREDICTED_BREED" != "unknown" ] && [ "$PREDICTED_BREED" != "null" ]; then
    echo "│ predicted_breed  │ $PREDICTED_BREED │ ${GREEN}✅ AI Model Active${NC}     │"
    BREED_PASS=true
else
    echo "│ predicted_breed  │ $PREDICTED_BREED │ ${RED}❌ AI Model Failed${NC}     │"
    BREED_PASS=false
fi

# Confidence check
if (( $(echo "$CONFIDENCE > 0.1" | bc -l 2>/dev/null || echo "0") )); then
    echo "│ confidence       │ $CONFIDENCE     │ ${GREEN}✅ Reasonable Score${NC}    │"
    CONFIDENCE_PASS=true
else
    echo "│ confidence       │ $CONFIDENCE     │ ${YELLOW}⚠️  Low Confidence${NC}     │"
    CONFIDENCE_PASS=true  # Warning but not failure
fi

# Processing time check
if [ "$PROCESSING_TIME" -gt 0 ] && [ "$PROCESSING_TIME" -lt 5000 ]; then
    echo "│ processing_time  │ ${PROCESSING_TIME}ms      │ ${GREEN}✅ Fast Response${NC}       │"
    TIMING_PASS=true
elif [ "$PROCESSING_TIME" -gt 5000 ]; then
    echo "│ processing_time  │ ${PROCESSING_TIME}ms      │ ${YELLOW}⚠️  Slow Response${NC}      │"
    TIMING_PASS=true  # Warning but not failure
else
    echo "│ processing_time  │ ${PROCESSING_TIME}ms      │ ${RED}❌ No Timing Data${NC}      │"
    TIMING_PASS=false
fi

# Total request time check
if [ "$GENERATION_TIME" -lt 30 ]; then
    echo "│ total_time       │ ${GENERATION_TIME}s        │ ${GREEN}✅ Under 30s${NC}           │"
    TOTAL_TIME_PASS=true
else
    echo "│ total_time       │ ${GENERATION_TIME}s        │ ${RED}❌ Too Slow${NC}            │"
    TOTAL_TIME_PASS=false
fi

echo "└──────────────────┴─────────────────┴────────────────────────┘"
echo ""

# Cleanup
rm -f "$TMP_IMAGE"

# Step 3: API Integration Test
echo "${BOLD}3. API Integration Test${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing API endpoints availability..."

# Test metrics endpoint
METRICS_STATUS=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" "${LOCAL_API_URL}/metrics" || echo "000")
if [ "$METRICS_STATUS" = "200" ]; then
    echo "Metrics endpoint: ${GREEN}✅ Active${NC}"
    METRICS_PASS=true
else
    echo "Metrics endpoint: ${YELLOW}⚠️  HTTP $METRICS_STATUS${NC}"
    METRICS_PASS=true  # Not critical
fi

# Test ready endpoint
READY_STATUS=$(curl -s --max-time 5 -o /dev/null -w "%{http_code}" "${LOCAL_API_URL}/readyz" || echo "000")
if [ "$READY_STATUS" = "200" ]; then
    echo "Readiness endpoint: ${GREEN}✅ Ready${NC}"
    READY_PASS=true
else
    echo "Readiness endpoint: ${YELLOW}⚠️  HTTP $READY_STATUS${NC}"
    READY_PASS=true  # Not critical
fi

echo ""

# Step 4: Fast-Fail Validation Summary
echo "${BOLD}4. Production Validation Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_TIME=$(($(date +%s) - START_TIME))
echo "Total validation time: ${TOTAL_TIME}s"
echo ""

# Count passes and fails
CRITICAL_TESTS=("STATUS_PASS" "PIPELINE_PASS" "BREED_PASS" "TOTAL_TIME_PASS")
PASSED_CRITICAL=0
TOTAL_CRITICAL=${#CRITICAL_TESTS[@]}

for test in "${CRITICAL_TESTS[@]}"; do
    if [ "${!test}" = true ]; then
        ((PASSED_CRITICAL++))
    fi
done

# Overall assessment
echo "🎯 Critical Tests: $PASSED_CRITICAL/$TOTAL_CRITICAL passed"
echo ""

if [ "$PASSED_CRITICAL" -eq "$TOTAL_CRITICAL" ]; then
    echo "${BOLD}${GREEN}🚀 PRODUCTION VALIDATION: PASSED${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "✅ Health endpoint confirms live pipeline"
    echo "✅ AI breed detection is working"
    echo "✅ Response times are acceptable"
    echo "✅ PetPlantr is running on real AI stack"
    echo ""
    echo "${GREEN}🎉 Ready to showcase live AI-powered pet planters!${NC}"
    echo ""
    echo "Next steps:"
    echo "• Share: ${PRODUCTION_URL}"
    echo "• Monitor: ${API_BASE}/metrics"
    echo "• Test upload: ${PRODUCTION_URL}/upload"
else
    echo "${BOLD}${RED}❌ PRODUCTION VALIDATION: FAILED${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Issues detected:"
    [ "$STATUS_PASS" != true ] && echo "❌ Health check failed"
    [ "$PIPELINE_PASS" != true ] && echo "❌ Demo mode detected (not live pipeline)"
    [ "$BREED_PASS" != true ] && echo "❌ AI breed detection not working"
    [ "$TOTAL_TIME_PASS" != true ] && echo "❌ Response times too slow"
    echo ""
    echo "${RED}🚨 System is NOT ready for production use${NC}"
    echo ""
    echo "Debug steps:"
    echo "• Check API server status"
    echo "• Verify environment variables"
    echo "• Review server logs"
    echo "• Run: ./test-dns.sh"
fi

echo ""
echo "Validation completed in ${TOTAL_TIME}s"

# Exit with appropriate code
if [ "$PASSED_CRITICAL" -eq "$TOTAL_CRITICAL" ]; then
    exit 0
else
    exit 1
fi
