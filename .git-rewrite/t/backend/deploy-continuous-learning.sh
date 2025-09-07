#!/bin/bash

# Deploy Step Functions definition to S3
# This script uploads the ASL definition file to S3 before deploying serverless

set -e

STAGE=${1:-dev}
TRAINING_BUCKET="petplantr-training-${STAGE}"
ASL_FILE="stepfunctions/modelFineTune.asl.json"

echo "🚀 Uploading Step Functions definition to S3..."

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI and configure credentials."
    exit 1
fi

# Create training bucket if it doesn't exist
aws s3 mb "s3://${TRAINING_BUCKET}" --region us-east-1 2>/dev/null || echo "Bucket already exists"

# Upload ASL definition
if [ -f "$ASL_FILE" ]; then
    aws s3 cp "$ASL_FILE" "s3://${TRAINING_BUCKET}/stepfunctions/modelFineTune.asl.json"
    echo "✅ Step Functions definition uploaded successfully"
else
    echo "❌ Step Functions definition file not found: $ASL_FILE"
    exit 1
fi

echo "🎯 Deploying serverless stack..."
npm run build
serverless deploy --stage "$STAGE"

echo "✅ Deployment complete!"
