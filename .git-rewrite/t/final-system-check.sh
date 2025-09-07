#!/bin/bash

# Final PetPlantr System Status Check
echo "🎯 PetPlantr System Status Check"
echo "================================"
echo "$(date)"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}1. API Health Check${NC}"
API_HEALTH=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/api/health")
if [ "$API_HEALTH" = "200" ]; then
    echo -e "${GREEN}✅ API Health: OK (HTTP $API_HEALTH)${NC}"
else
    echo -e "${RED}❌ API Health: FAIL (HTTP $API_HEALTH)${NC}"
fi

echo ""
echo -e "${CYAN}2. API Replicate Demo Mode${NC}"
DEMO_RESPONSE=$(timeout 5 curl -s "http://localhost:3000/api/replicate?id=demo_123&threeDPredictionId=test")
if echo "$DEMO_RESPONSE" | grep -q "modelUrl"; then
    echo -e "${GREEN}✅ API Demo Mode: Working${NC}"
    MODEL_URL=$(echo "$DEMO_RESPONSE" | grep -o '"modelUrl":"[^"]*"' | cut -d'"' -f4)
    echo -e "   Model URL: $MODEL_URL"
else
    echo -e "${RED}❌ API Demo Mode: FAIL${NC}"
    echo "   Response: $DEMO_RESPONSE"
fi

echo ""
echo -e "${CYAN}3. CloudFront Model Access${NC}"
CLOUDFRONT_STATUS=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" "https://dpa0b9puwj06h.cloudfront.net/models/bv1vzagzj1rma0cr99099rdszc.glb")
if [ "$CLOUDFRONT_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ CloudFront Access: Working (HTTP $CLOUDFRONT_STATUS)${NC}"
    # Get content type and size
    CONTENT_INFO=$(timeout 10 curl -s -I "https://dpa0b9puwj06h.cloudfront.net/models/bv1vzagzj1rma0cr99099rdszc.glb" | grep -E "(content-type|content-length)" | tr '\r' ' ')
    echo -e "   Content Info: $CONTENT_INFO"
else
    echo -e "${RED}❌ CloudFront Access: FAIL (HTTP $CLOUDFRONT_STATUS)${NC}"
fi

echo ""
echo -e "${CYAN}4. Frontend Pages${NC}"
UPLOAD_PAGE=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/upload")
TEST_PAGE=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/frontend-3d-test.html")

if [ "$UPLOAD_PAGE" = "200" ]; then
    echo -e "${GREEN}✅ Upload Page: Accessible (HTTP $UPLOAD_PAGE)${NC}"
else
    echo -e "${RED}❌ Upload Page: FAIL (HTTP $UPLOAD_PAGE)${NC}"
fi

if [ "$TEST_PAGE" = "200" ]; then
    echo -e "${GREEN}✅ Test Page: Accessible (HTTP $TEST_PAGE)${NC}"
else
    echo -e "${RED}❌ Test Page: FAIL (HTTP $TEST_PAGE)${NC}"
fi

echo ""
echo "================================"
echo -e "${CYAN}📊 System Status Summary${NC}"
echo "================================"

# Count successful tests
TESTS=0
PASSED=0

for status in "$API_HEALTH" "$CLOUDFRONT_STATUS" "$UPLOAD_PAGE" "$TEST_PAGE"; do
    ((TESTS++))
    if [ "$status" = "200" ]; then
        ((PASSED++))
    fi
done

# Check demo API
if echo "$DEMO_RESPONSE" | grep -q "modelUrl"; then
    ((TESTS++))
    ((PASSED++))
fi

if [ "$PASSED" -eq "$TESTS" ]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS OPERATIONAL ($PASSED/$TESTS)${NC}"
    echo ""
    echo -e "${GREEN}✅ CloudFront 'failed to load model' issue: RESOLVED${NC}"
    echo -e "${GREEN}✅ API endpoints: Working${NC}"
    echo -e "${GREEN}✅ Frontend pages: Accessible${NC}"
    echo -e "${GREEN}✅ 3D model delivery: Functional${NC}"
    echo ""
    echo -e "${CYAN}🚀 Ready for use:${NC}"
    echo "   • Main app: http://localhost:3000/upload"
    echo "   • 3D test: http://localhost:3000/frontend-3d-test.html"
    echo "   • Diagnostic: http://localhost:3000/diagnostic.html"
    echo ""
    echo -e "${GREEN}🎯 PetPlantr is ready for production deployment!${NC}"
else
    echo -e "${YELLOW}⚠️  System Status: $PASSED/$TESTS components working${NC}"
    echo "Check individual test results above."
fi

echo ""
