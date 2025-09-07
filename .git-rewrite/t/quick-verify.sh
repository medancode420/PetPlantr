#!/bin/bash

# Simple verification script for PetPlantr infrastructure
echo "🔍 PetPlantr Infrastructure Quick Check"
echo "======================================"

# Load environment variables
if [ -f ".env.local" ]; then
    export $(grep -v '^#' .env.local | grep -v '^$' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ .env.local not found"
    exit 1
fi

# Check key variables
echo ""
echo "📋 Key Variables:"
echo "  REPLICATE_API_TOKEN: ${REPLICATE_API_TOKEN:0:8}..."
echo "  AWS_S3_BUCKET: $AWS_S3_BUCKET"
echo "  CLOUDFRONT_DOMAIN: $CLOUDFRONT_DOMAIN"

# Test S3 connection
echo ""
echo "🪣 Testing S3 connection..."
if aws s3 ls "s3://$AWS_S3_BUCKET" > /dev/null 2>&1; then
    echo "✅ S3 bucket accessible"
else
    echo "❌ S3 bucket not accessible"
fi

# Test Replicate API
echo ""
echo "🤖 Testing Replicate API..."
REPLICATE_TEST=$(curl -s -H "Authorization: Token $REPLICATE_API_TOKEN" \
    "https://api.replicate.com/v1/models" | head -c 100)

if echo "$REPLICATE_TEST" | grep -q "results"; then
    echo "✅ Replicate API accessible"
else
    echo "❌ Replicate API failed"
fi

# Test CloudFront
echo ""
echo "🌐 Testing CloudFront..."
if curl -s -I "https://$CLOUDFRONT_DOMAIN" | grep -q "200\|403"; then
    echo "✅ CloudFront distribution accessible"
else
    echo "❌ CloudFront distribution failed"
fi

echo ""
echo "🎯 Status: Infrastructure appears ready for testing!"
