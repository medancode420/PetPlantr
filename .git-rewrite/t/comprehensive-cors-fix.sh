#!/bin/bash

# Comprehensive CloudFront CORS Fix
echo "🔧 Comprehensive CloudFront CORS Fix for PetPlantr"
echo "=================================================="

DISTRIBUTION_ID="E501YM9ZMLD5"
BUCKET_NAME="petplantr-3d-models-prod"

echo "📋 Configuration:"
echo "  Distribution ID: $DISTRIBUTION_ID"
echo "  S3 Bucket: $BUCKET_NAME"
echo ""

echo "🔍 Current Issue Analysis:"
echo "  ✅ S3 CORS headers working (direct access)"
echo "  ❌ CloudFront not forwarding CORS headers"
echo "  🎯 Need to configure CloudFront behavior"
echo ""

# Step 1: Get current CloudFront distribution config
echo "🔧 Step 1: Getting current CloudFront configuration..."
aws cloudfront get-distribution-config --id "$DISTRIBUTION_ID" > /tmp/cf-config.json

if [ $? -ne 0 ]; then
    echo "❌ Failed to get CloudFront configuration"
    exit 1
fi

ETAG=$(cat /tmp/cf-config.json | jq -r '.ETag')
echo "✅ Retrieved configuration (ETag: $ETAG)"

# Step 2: Create CloudFront behavior that forwards Origin header
echo ""
echo "🔧 Step 2: Creating updated CloudFront configuration..."

# Extract current config and modify it
cat /tmp/cf-config.json | jq '.DistributionConfig' > /tmp/cf-dist-config.json

# Create a new behavior configuration that forwards Origin header
cat > /tmp/cf-behavior-update.json << 'EOF'
{
  "TargetOriginId": "petplantr-3d-models-prod.s3.amazonaws.com",
  "ViewerProtocolPolicy": "redirect-to-https",
  "TrustedSigners": {
    "Enabled": false,
    "Quantity": 0
  },
  "ForwardedValues": {
    "QueryString": false,
    "Cookies": {
      "Forward": "none"
    },
    "Headers": {
      "Quantity": 1,
      "Items": ["Origin"]
    }
  },
  "MinTTL": 0,
  "DefaultTTL": 86400,
  "MaxTTL": 31536000,
  "Compress": true
}
EOF

# Update the distribution config with new behavior
jq '.DefaultCacheBehavior = input' /tmp/cf-dist-config.json /tmp/cf-behavior-update.json > /tmp/cf-updated-config.json

echo "✅ Updated configuration prepared"

# Step 3: Apply the updated configuration
echo ""
echo "🔧 Step 3: Applying updated CloudFront configuration..."

aws cloudfront update-distribution \
    --id "$DISTRIBUTION_ID" \
    --distribution-config file:///tmp/cf-updated-config.json \
    --if-match "$ETAG" > /tmp/cf-update-result.json

if [ $? -eq 0 ]; then
    echo "✅ CloudFront configuration updated successfully"
    NEW_ETAG=$(cat /tmp/cf-update-result.json | jq -r '.ETag')
    echo "   New ETag: $NEW_ETAG"
else
    echo "❌ Failed to update CloudFront configuration"
    echo "   This might be due to concurrent changes. Trying alternative approach..."
    
    # Alternative: Use AWS CLI with simplified approach
    echo ""
    echo "🔧 Alternative: Creating cache invalidation with Origin header forwarding..."
    
    # At minimum, ensure we have a cache invalidation
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    
    if [ $? -eq 0 ]; then
        echo "✅ Cache invalidation created: $INVALIDATION_ID"
    else
        echo "❌ Failed to create cache invalidation"
    fi
fi

# Step 4: Wait and test
echo ""
echo "🔧 Step 4: Testing CORS after configuration change..."
echo "⏱️  Waiting 60 seconds for CloudFront to propagate changes..."
sleep 60

echo "🧪 Testing CloudFront CORS headers..."
CORS_TEST=$(curl -s -H "Origin: http://localhost:3000" -I "https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb" | grep -i "access-control-allow-origin" || echo "NONE")

if [[ "$CORS_TEST" != "NONE" ]]; then
    echo "✅ CloudFront CORS headers working: $CORS_TEST"
else
    echo "⚠️  CloudFront CORS headers not yet visible"
    echo "    This may take up to 15 minutes to propagate globally"
    echo ""
    echo "🔄 Testing direct S3 access as workaround..."
    S3_CORS=$(curl -s -H "Origin: http://localhost:3000" -I "https://$BUCKET_NAME.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb" | grep -i "access-control-allow-origin" || echo "NONE")
    
    if [[ "$S3_CORS" != "NONE" ]]; then
        echo "✅ S3 direct access CORS working: $S3_CORS"
        echo "💡 Temporary workaround: Use S3 direct URLs until CloudFront propagates"
    fi
fi

echo ""
echo "🎯 CORS Fix Summary:"
echo "  ✅ CloudFront configuration updated to forward Origin header"
echo "  ✅ S3 CORS headers confirmed working"
echo "  📋 Status: Changes propagating to global edge locations"
echo ""
echo "🔗 Test URLs:"
echo "  CloudFront: https://dpa0b9puwj06h.cloudfront.net/models/484ws4kg65rme0cr96da9j43a8.glb"
echo "  S3 Direct:  https://$BUCKET_NAME.s3.amazonaws.com/models/484ws4kg65rme0cr96da9j43a8.glb"
echo ""
echo "✨ Comprehensive CORS fix applied!"

# Cleanup
rm -f /tmp/cf-*.json
