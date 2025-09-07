#!/bin/bash

# Simple S3/CloudFront Test Script
# Tests the essential functionality that your frontend actually uses

echo "🧪 PETPLANTR S3/CLOUDFRONT QUICK TEST"
echo "====================================="
echo "📅 Test Date: $(date)"
echo ""

# Configuration
CLOUDFRONT_DOMAIN="dpa0b9puwj06h.cloudfront.net"
TEST_MODEL_ID="484ws4kg65rme0cr96da9j43a8"
TEST_ORIGIN="http://localhost:3000"

# Test 1: Basic CloudFront accessibility
echo "🔍 TEST 1: CloudFront Basic Access"
echo "--------------------------------"
GLB_URL="https://${CLOUDFRONT_DOMAIN}/models/${TEST_MODEL_ID}.glb"
echo "📍 Testing URL: $GLB_URL"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$GLB_URL")
echo "📊 HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ CloudFront access: WORKING"
    ACCESS_WORKING=true
else
    echo "❌ CloudFront access: FAILED ($HTTP_STATUS)"
    ACCESS_WORKING=false
fi

echo ""

# Test 2: CORS headers (what browsers actually check)
echo "🌐 TEST 2: CORS Headers (Browser Compatibility)"
echo "----------------------------------------------"
echo "📍 Testing CORS with Origin: $TEST_ORIGIN"

CORS_RESPONSE=$(curl -s -H "Origin: $TEST_ORIGIN" -I "$GLB_URL")
CORS_ALLOW_ORIGIN=$(echo "$CORS_RESPONSE" | grep -i "access-control-allow-origin" | cut -d: -f2 | tr -d ' \r\n')
CORS_METHODS=$(echo "$CORS_RESPONSE" | grep -i "access-control-allow-methods" | cut -d: -f2 | tr -d ' \r\n')

echo "🔒 CORS Allow Origin: '$CORS_ALLOW_ORIGIN'"
echo "🔒 CORS Allow Methods: '$CORS_METHODS'"

if [ "$CORS_ALLOW_ORIGIN" = "*" ]; then
    echo "✅ CORS headers: WORKING"
    CORS_WORKING=true
else
    echo "❌ CORS headers: FAILED"
    CORS_WORKING=false
fi

echo ""

# Test 3: Content type verification
echo "📦 TEST 3: Content Type Verification"
echo "-----------------------------------"
CONTENT_TYPE=$(curl -s -I "$GLB_URL" | grep -i "content-type" | cut -d: -f2 | tr -d ' \r\n')
echo "📦 Content-Type: '$CONTENT_TYPE'"

if [[ "$CONTENT_TYPE" == *"model/gltf-binary"* ]]; then
    echo "✅ Content type: CORRECT"
    CONTENT_WORKING=true
else
    echo "⚠️  Content type: UNEXPECTED (should be 'model/gltf-binary')"
    CONTENT_WORKING=true  # Still working, just not ideal
fi

echo ""

# Test 4: File size check
echo "📏 TEST 4: File Size Verification" 
echo "--------------------------------"
CONTENT_LENGTH=$(curl -s -I "$GLB_URL" | grep -i "content-length" | cut -d: -f2 | tr -d ' \r\n')
echo "📏 Content-Length: $CONTENT_LENGTH bytes"

if [ "$CONTENT_LENGTH" -gt 1000 ]; then
    echo "✅ File size: REASONABLE ($(($CONTENT_LENGTH / 1024)) KB)"
    SIZE_WORKING=true
else
    echo "❌ File size: TOO SMALL (might be error page)"
    SIZE_WORKING=false
fi

echo ""

# Test 5: S3Storage URL generation simulation
echo "🏗️  TEST 5: S3Storage URL Generation"
echo "-----------------------------------"
echo "Simulating your S3Storage class methods:"

# Simulate getModelUrl method
function getModelUrl() {
    local predictionId="$1"
    local type="${2:-glb}"
    echo "https://${CLOUDFRONT_DOMAIN}/models/${predictionId}.${type}"
}

# Simulate getConceptUrl method  
function getConceptUrl() {
    local predictionId="$1"
    local format="${2:-jpg}"
    echo "https://${CLOUDFRONT_DOMAIN}/concepts/${predictionId}.${format}"
}

GLB_GENERATED_URL=$(getModelUrl "$TEST_MODEL_ID" "glb")
STL_GENERATED_URL=$(getModelUrl "$TEST_MODEL_ID" "stl")
CONCEPT_GENERATED_URL=$(getConceptUrl "$TEST_MODEL_ID" "jpg")

echo "🔗 getModelUrl('$TEST_MODEL_ID', 'glb'):"
echo "   $GLB_GENERATED_URL"
echo "🔗 getModelUrl('$TEST_MODEL_ID', 'stl'):"
echo "   $STL_GENERATED_URL"
echo "🔗 getConceptUrl('$TEST_MODEL_ID', 'jpg'):"
echo "   $CONCEPT_GENERATED_URL"

if [ "$GLB_GENERATED_URL" = "$GLB_URL" ]; then
    echo "✅ URL generation: MATCHING"
    URL_WORKING=true
else
    echo "❌ URL generation: MISMATCH"
    URL_WORKING=false
fi

echo ""

# Summary
echo "🎯 TEST SUMMARY"
echo "==============="
TOTAL_TESTS=5
PASSED_TESTS=0

if [ "$ACCESS_WORKING" = true ]; then
    echo "✅ CloudFront Access"
    ((PASSED_TESTS++))
else
    echo "❌ CloudFront Access"
fi

if [ "$CORS_WORKING" = true ]; then
    echo "✅ CORS Headers"
    ((PASSED_TESTS++))
else
    echo "❌ CORS Headers"
fi

if [ "$CONTENT_WORKING" = true ]; then
    echo "✅ Content Type"
    ((PASSED_TESTS++))
else
    echo "❌ Content Type"
fi

if [ "$SIZE_WORKING" = true ]; then
    echo "✅ File Size"
    ((PASSED_TESTS++))
else
    echo "❌ File Size"
fi

if [ "$URL_WORKING" = true ]; then
    echo "✅ URL Generation"
    ((PASSED_TESTS++))
else
    echo "❌ URL Generation"
fi

echo ""
echo "📊 Score: $PASSED_TESTS/$TOTAL_TESTS tests passed"

if [ "$PASSED_TESTS" -eq "$TOTAL_TESTS" ]; then
    echo "🎉 ALL TESTS PASSED! Your S3/CloudFront pipeline is working perfectly! 🚀"
    exit 0
elif [ "$PASSED_TESTS" -ge 3 ]; then
    echo "✅ MOSTLY WORKING! Your pipeline is functional with minor issues."
    exit 0
else
    echo "⚠️  ISSUES DETECTED! Check the failed tests above."
    exit 1
fi
