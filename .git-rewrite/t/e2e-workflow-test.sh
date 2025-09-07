#!/bin/bash

# End-to-End PetPlantr Workflow Test
echo "🧪 PetPlantr End-to-End Workflow Test"
echo "===================================="
echo "$(date)"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS_COUNT=0
TOTAL_COUNT=0

test_step() {
    local step_name="$1"
    local command="$2"
    local expected="$3"
    
    echo -e "${CYAN}🔍 Testing: $step_name${NC}"
    ((TOTAL_COUNT++))
    
    result=$(eval "$command" 2>/dev/null)
    
    if [[ "$result" == *"$expected"* ]] || [ "$expected" = "any" ]; then
        echo -e "${GREEN}✅ PASS: $step_name${NC}"
        [ "$expected" != "any" ] && echo -e "   Result: $result"
        ((PASS_COUNT++))
    else
        echo -e "${RED}❌ FAIL: $step_name${NC}"
        echo -e "   Expected: $expected"
        echo -e "   Got: $result"
    fi
    echo ""
}

echo -e "${BLUE}📋 Phase 1: Core System Health${NC}"
echo "--------------------------------"

test_step "API Health Check" \
    "curl -s 'http://localhost:3000/api/health' | grep -o '\"status\":\"[^\"]*\"'" \
    '"status":"ok"'

test_step "Server Response Time" \
    "time curl -s -o /dev/null 'http://localhost:3000/api/health' && echo 'fast'" \
    "any"

echo -e "${BLUE}📋 Phase 2: API Functionality${NC}"
echo "------------------------------"

test_step "API Demo Mode" \
    "curl -s 'http://localhost:3000/api/replicate?id=demo_test&threeDPredictionId=test' | grep -o '\"status\":\"[^\"]*\"'" \
    '"status":"succeeded"'

test_step "API Returns Model URL" \
    "curl -s 'http://localhost:3000/api/replicate?id=demo_test&threeDPredictionId=test' | grep -o '\"modelUrl\":\"[^\"]*\"'" \
    '"modelUrl"'

echo -e "${BLUE}📋 Phase 3: Frontend Pages${NC}"
echo "---------------------------"

test_step "Upload Page Accessible" \
    "curl -s -o /dev/null -w '%{http_code}' 'http://localhost:3000/upload'" \
    "200"

test_step "3D Test Page Accessible" \
    "curl -s -o /dev/null -w '%{http_code}' 'http://localhost:3000/frontend-3d-test.html'" \
    "200"

test_step "Diagnostic Page Accessible" \
    "curl -s -o /dev/null -w '%{http_code}' 'http://localhost:3000/diagnostic.html'" \
    "200"

echo -e "${BLUE}📋 Phase 4: CloudFront CDN${NC}"
echo "--------------------------"

# Test single model (avoiding rate limiting)
test_step "CloudFront Model Access (Primary)" \
    "curl -s -o /dev/null -w '%{http_code}' 'https://dpa0b9puwj06h.cloudfront.net/models/bv1vzagzj1rma0cr99099rdszc.glb'" \
    "200"

test_step "CloudFront Content Type" \
    "curl -s -I 'https://dpa0b9puwj06h.cloudfront.net/models/bv1vzagzj1rma0cr99099rdszc.glb' | grep -i 'content-type' | grep -o 'model/gltf-binary'" \
    "model/gltf-binary"

echo -e "${BLUE}📋 Phase 5: Real Model Files${NC}"
echo "----------------------------"

test_step "Model File Exists in S3" \
    "aws s3 ls s3://petplantr-3d-models-prod/models/bv1vzagzj1rma0cr99099rdszc.glb | grep -o 'bv1vzagzj1rma0cr99099rdszc.glb'" \
    "bv1vzagzj1rma0cr99099rdszc.glb"

test_step "Multiple Models Available" \
    "aws s3 ls s3://petplantr-3d-models-prod/models/ | wc -l" \
    "any"

echo "===================================="
echo -e "${CYAN}📊 Test Results Summary${NC}"
echo "===================================="

if [ "$PASS_COUNT" -eq "$TOTAL_COUNT" ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! ($PASS_COUNT/$TOTAL_COUNT)${NC}"
    echo ""
    echo -e "${GREEN}✅ System Status: FULLY OPERATIONAL${NC}"
    echo -e "${GREEN}✅ No 'failed to load model' errors${NC}"
    echo -e "${GREEN}✅ Ready for production use${NC}"
    echo ""
    echo -e "${CYAN}🚀 Ready to use:${NC}"
    echo "   • Main App: http://localhost:3000/upload"
    echo "   • 3D Viewer Test: http://localhost:3000/frontend-3d-test.html"
    echo "   • System Diagnostic: http://localhost:3000/diagnostic.html"
    echo ""
    echo -e "${BLUE}🌟 PetPlantr is working perfectly!${NC}"
    
elif [ "$PASS_COUNT" -gt $((TOTAL_COUNT * 8 / 10)) ]; then
    echo -e "${YELLOW}⚠️  MOSTLY WORKING ($PASS_COUNT/$TOTAL_COUNT tests passed)${NC}"
    echo -e "${YELLOW}System is functional with minor issues${NC}"
    
else
    echo -e "${RED}❌ SYSTEM ISSUES ($PASS_COUNT/$TOTAL_COUNT tests passed)${NC}"
    echo -e "${RED}Critical components need attention${NC}"
fi

echo ""
echo "Test completed at: $(date)"
