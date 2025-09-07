#!/bin/bash

echo "🧪 PetPlantr Farm Manager - Local Testing Guide"
echo "=============================================="
echo

echo "📋 TESTING METHODS AVAILABLE:"
echo

echo "1️⃣ LOCAL FUNCTION TESTING"
echo "   • Test individual functions without deployment"
echo "   • Fast feedback for development"
echo "   • Uses serverless-offline or manual testing"
echo

echo "2️⃣ UNIT TESTING"
echo "   • Test business logic and utilities"
echo "   • Mock AWS services"
echo "   • Fast execution"
echo

echo "3️⃣ INTEGRATION TESTING"
echo "   • Test with real AWS services"
echo "   • Full end-to-end workflows"
echo "   • Requires deployment"
echo

echo "4️⃣ API TESTING"
echo "   • Test HTTP endpoints"
echo "   • Use existing test scripts"
echo "   • Comprehensive scenario testing"
echo

echo "=============================================="
echo "🚀 QUICK START TESTING"
echo

echo "Step 1: Build the project"
echo "   npm run build"
echo

echo "Step 2: Choose your testing method:"
echo

echo "   Local Testing (serverless-offline):"
echo "   npx serverless offline start"
echo "   curl http://localhost:3000/api/farm/status"
echo

echo "   Deploy & Test (staging):"
echo "   npx serverless deploy --stage dev"
echo "   ./test-advanced-backend.sh [API_URL]"
echo

echo "   Quick Unit Tests:"
echo "   npm test (if configured)"
echo

echo "=============================================="
echo "📊 AVAILABLE TEST SCRIPTS:"
echo

echo "• ./test-advanced-backend.sh      - Comprehensive API testing"
echo "• ./test-enhanced-api.sh          - Enhanced endpoint testing" 
echo "• ./test-frontend-integration.sh  - Frontend-focused testing"
echo "• ./validate-final-build.sh       - Build validation"
echo

echo "=============================================="
echo "Example: Test after deployment"
echo "npx serverless deploy --stage dev"
echo "API_URL=\$(npx serverless info --stage dev --verbose | grep 'ServiceEndpoint:' | awk '{print \$2}')"
echo "./test-advanced-backend.sh \$API_URL"
echo

echo "=============================================="
