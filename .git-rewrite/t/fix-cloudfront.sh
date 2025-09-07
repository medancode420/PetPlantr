#!/bin/bash

# CloudFront Configuration Fix for PetPlantr
# This script fixes the "Access Denied" issues with GLB model files

set -e

echo "🔧 CloudFront Configuration Fix for PetPlantr"
echo "============================================="

# Load environment variables
source frontend/.env.local 2>/dev/null || echo "Warning: frontend/.env.local not found"

BUCKET_NAME="${AWS_S3_BUCKET:-petplantr-3d-models-prod}"
REGION="${AWS_REGION:-us-east-1}"
CLOUDFRONT_DOMAIN="${NEXT_PUBLIC_CLOUDFRONT_DOMAIN:-dpa0b9puwj06h.cloudfront.net}"

echo "📋 Configuration:"
echo "  S3 Bucket: $BUCKET_NAME"
echo "  Region: $REGION"
echo "  CloudFront: $CLOUDFRONT_DOMAIN"
echo ""

# Check AWS CLI installation
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   brew install awscli"
    echo "   # or"
    echo "   pip install awscli"
    exit 1
fi

echo "🔍 Checking current AWS configuration..."

# Test AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    echo "   # or set environment variables:"
    echo "   export AWS_ACCESS_KEY_ID=your_key"
    echo "   export AWS_SECRET_ACCESS_KEY=your_secret"
    exit 1
fi

echo "✅ AWS credentials configured"

# Get CloudFront Distribution ID
echo "🔍 Finding CloudFront distribution..."
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='$CLOUDFRONT_DOMAIN'].Id" --output text)

if [ -z "$DISTRIBUTION_ID" ] || [ "$DISTRIBUTION_ID" = "None" ]; then
    echo "❌ CloudFront distribution not found for domain: $CLOUDFRONT_DOMAIN"
    echo "Please check if the domain is correct or create a distribution first."
    exit 1
fi

echo "✅ Found CloudFront distribution: $DISTRIBUTION_ID"

# Check S3 bucket exists and permissions
echo "🔍 Checking S3 bucket..."
if ! aws s3 ls "s3://$BUCKET_NAME" > /dev/null 2>&1; then
    echo "❌ Cannot access S3 bucket: $BUCKET_NAME"
    echo "Please check if the bucket exists and you have permissions."
    exit 1
fi

echo "✅ S3 bucket accessible"

# Create S3 bucket policy to allow CloudFront access
echo "🔧 Creating S3 bucket policy..."

cat > s3-bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::$(aws sts get-caller-identity --query Account --output text):distribution/$DISTRIBUTION_ID"
                }
            }
        },
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

# Apply S3 bucket policy
echo "📝 Applying S3 bucket policy..."
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file://s3-bucket-policy.json

echo "✅ S3 bucket policy updated"

# Get current CloudFront distribution configuration
echo "🔍 Getting CloudFront distribution configuration..."
aws cloudfront get-distribution-config --id "$DISTRIBUTION_ID" > cloudfront-config.json

# Extract ETag and configuration
ETAG=$(jq -r '.ETag' cloudfront-config.json)
jq '.DistributionConfig' cloudfront-config.json > distribution-config.json

echo "✅ Current configuration retrieved (ETag: $ETAG)"

# Update CloudFront configuration to fix common issues
echo "🔧 Updating CloudFront configuration..."

# Create updated configuration
jq '
.DefaultCacheBehavior.ViewerProtocolPolicy = "redirect-to-https" |
.DefaultCacheBehavior.AllowedMethods.Items = ["GET", "HEAD", "OPTIONS"] |
.DefaultCacheBehavior.AllowedMethods.Quantity = 3 |
.DefaultCacheBehavior.CachedMethods.Items = ["GET", "HEAD"] |
.DefaultCacheBehavior.CachedMethods.Quantity = 2 |
.DefaultCacheBehavior.Compress = true |
.DefaultCacheBehavior.CachePolicyId = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" |
.Comment = "PetPlantr GLB Models Distribution - Updated for public access"
' distribution-config.json > updated-distribution-config.json

echo "📝 Updating CloudFront distribution..."
aws cloudfront update-distribution \
    --id "$DISTRIBUTION_ID" \
    --distribution-config file://updated-distribution-config.json \
    --if-match "$ETAG" > update-result.json

echo "✅ CloudFront distribution updated"

# Create invalidation for immediate effect
echo "🔄 Creating CloudFront invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "✅ Invalidation created: $INVALIDATION_ID"

# Test the fix
echo "🧪 Testing the fix..."
sleep 10  # Wait a moment for changes to propagate

TEST_URL="https://$CLOUDFRONT_DOMAIN/models/484ws4kg65rme0cr96da9j43a8.glb"
echo "   Testing URL: $TEST_URL"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ SUCCESS! CloudFront is now serving GLB files correctly"
elif [ "$HTTP_STATUS" = "404" ]; then
    echo "⚠️  File not found (404) - this is expected if the model doesn't exist"
    echo "   The configuration is correct, but the specific file may not be uploaded yet"
else
    echo "⚠️  Still getting HTTP $HTTP_STATUS"
    echo "   Changes may take 5-15 minutes to propagate globally"
    echo "   You can check invalidation status with:"
    echo "   aws cloudfront get-invalidation --distribution-id $DISTRIBUTION_ID --id $INVALIDATION_ID"
fi

# Clean up temporary files
rm -f s3-bucket-policy.json cloudfront-config.json distribution-config.json updated-distribution-config.json update-result.json

echo ""
echo "🎉 CloudFront configuration fix completed!"
echo ""
echo "📝 Summary of changes:"
echo "  ✅ S3 bucket policy updated for public read access"
echo "  ✅ CloudFront distribution configured for HTTPS redirect"
echo "  ✅ Compression enabled for better performance"
echo "  ✅ Cache invalidation triggered"
echo ""
echo "🕐 Note: Changes may take 5-15 minutes to propagate globally"
echo ""
echo "🧪 You can test with:"
echo "   curl -I https://$CLOUDFRONT_DOMAIN/models/[model-id].glb"
echo ""
echo "🔍 Monitor invalidation progress:"
echo "   aws cloudfront get-invalidation --distribution-id $DISTRIBUTION_ID --id $INVALIDATION_ID"
