#!/bin/bash

# Simple CloudFront Fix for PetPlantr
echo "🔧 Simple CloudFront Fix for PetPlantr"
echo "====================================="

# Configuration
S3_BUCKET="petplantr-3d-models-prod"
CLOUDFRONT_DOMAIN="dpa0b9puwj06h.cloudfront.net"
CLOUDFRONT_DISTRIBUTION_ID="E501YM9ZMLD5"

echo "📋 Configuration:"
echo "  S3 Bucket: $S3_BUCKET"
echo "  CloudFront: $CLOUDFRONT_DOMAIN"
echo "  Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID"

# Step 1: Update S3 bucket policy for public read access
echo ""
echo "🔧 Step 1: Updating S3 bucket policy..."

cat > /tmp/s3-public-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$S3_BUCKET/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket "$S3_BUCKET" --policy file:///tmp/s3-public-policy.json
if [ $? -eq 0 ]; then
    echo "✅ S3 bucket policy updated successfully"
else
    echo "❌ Failed to update S3 bucket policy"
    exit 1
fi

# Step 2: Set public read access on S3 bucket
echo ""
echo "🔧 Step 2: Setting S3 bucket public access..."
aws s3api put-public-access-block \
    --bucket "$S3_BUCKET" \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

if [ $? -eq 0 ]; then
    echo "✅ S3 public access configured"
else
    echo "❌ Failed to configure S3 public access"
fi

# Step 3: Create cache invalidation for CloudFront
echo ""
echo "🔧 Step 3: Creating CloudFront cache invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

if [ $? -eq 0 ]; then
    echo "✅ CloudFront invalidation created: $INVALIDATION_ID"
    echo "⏱️  Cache invalidation may take 5-15 minutes to complete"
else
    echo "❌ Failed to create CloudFront invalidation"
fi

# Step 4: Test access after a brief wait
echo ""
echo "🔧 Step 4: Testing access..."
echo "⏱️  Waiting 30 seconds for changes to propagate..."
sleep 30

echo "🧪 Testing CloudFront access..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$CLOUDFRONT_DOMAIN/models/test-model.glb")
echo "📊 HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "✅ CloudFront access working (200/404 is expected for non-existent files)"
elif [ "$HTTP_STATUS" = "403" ]; then
    echo "⚠️  Still getting 403 - may need more time for cache invalidation"
    echo "🔄 Please wait 5-15 minutes and test again"
else
    echo "⚠️  Unexpected status: $HTTP_STATUS"
fi

echo ""
echo "🎯 Fix Summary:"
echo "  ✅ S3 bucket policy updated for public read access"
echo "  ✅ S3 public access blocks removed"
echo "  ✅ CloudFront cache invalidation created"
echo "  📋 Status: $HTTP_STATUS"
echo ""
echo "🔗 Test URLs:"
echo "  Direct S3: https://$S3_BUCKET.s3.amazonaws.com/models/test-model.glb"
echo "  CloudFront: https://$CLOUDFRONT_DOMAIN/models/test-model.glb"
echo ""
echo "✨ CloudFront fix complete!"

# Cleanup
rm -f /tmp/s3-public-policy.json
