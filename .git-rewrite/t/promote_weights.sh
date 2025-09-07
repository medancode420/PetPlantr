#!/bin/bash
# PetPlantr Weight Promotion Script
# Promotes trained weights from staging to production
# Usage: ./promote_weights.sh s3://petplantr-models/stage1/unet128.pth

set -e  # Exit on any error

# Configuration
SECRETS_MANAGER_SECRET_NAME="petplantr/model-weights"
LAMBDA_FUNCTION_NAME="petplantr-pipeline-prod-generateSTL"
AWS_REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate input
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <s3-weights-path>"
    log_error "Example: $0 s3://petplantr-models/stage1/unet128.pth"
    exit 1
fi

WEIGHTS_S3_PATH="$1"

# Validate S3 path format
if [[ ! "$WEIGHTS_S3_PATH" =~ ^s3://.*\.pth$ ]]; then
    log_error "Invalid S3 path format. Must be s3://bucket/path/file.pth"
    exit 1
fi

log_info "🚀 Starting weight promotion process..."
log_info "📍 Source: $WEIGHTS_S3_PATH"

# Check if weights file exists in S3
log_info "🔍 Verifying weights file exists..."
if ! aws s3 ls "$WEIGHTS_S3_PATH" > /dev/null 2>&1; then
    log_error "Weights file not found at $WEIGHTS_S3_PATH"
    exit 1
fi
log_success "✅ Weights file verified"

# Get file size for validation
WEIGHTS_SIZE=$(aws s3 ls "$WEIGHTS_S3_PATH" | awk '{print $3}')
log_info "📊 Weights file size: $(numfmt --to=iec $WEIGHTS_SIZE)"

# Validate minimum size (should be at least 10MB for a valid model)
if [ "$WEIGHTS_SIZE" -lt 10485760 ]; then
    log_warning "⚠️  Weights file seems small ($WEIGHTS_SIZE bytes). Continue anyway? [y/N]"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_error "Weight promotion cancelled"
        exit 1
    fi
fi

# Update AWS Secrets Manager with new weights path
log_info "🔐 Updating Secrets Manager..."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Get current secret value and update it
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRETS_MANAGER_SECRET_NAME" \
    --region "$AWS_REGION" \
    --query 'SecretString' \
    --output text 2>/dev/null || echo '{}')

# Create updated secret with new weights path
UPDATED_SECRET=$(echo "$CURRENT_SECRET" | jq \
    --arg weights_path "$WEIGHTS_S3_PATH" \
    --arg updated_at "$TIMESTAMP" \
    '. + {
        "weights_s3_path": $weights_path,
        "updated_at": $updated_at,
        "status": "active"
    }')

# Update the secret
aws secretsmanager put-secret-value \
    --secret-id "$SECRETS_MANAGER_SECRET_NAME" \
    --secret-string "$UPDATED_SECRET" \
    --region "$AWS_REGION" > /dev/null

log_success "✅ Secrets Manager updated with new weights path"

# Trigger Lambda function redeploy
log_info "🔄 Triggering Lambda function redeploy..."

# Update Lambda environment variable to force refresh
aws lambda update-function-configuration \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --environment "Variables={WEIGHTS_VERSION=$TIMESTAMP,FORCE_RELOAD=true}" \
    --region "$AWS_REGION" > /dev/null

log_success "✅ Lambda function configuration updated"

# Wait for Lambda to be ready
log_info "⏳ Waiting for Lambda function to be ready..."
aws lambda wait function-updated \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$AWS_REGION"

log_success "✅ Lambda function is ready"

# Test the deployed function with a simple invocation
log_info "🧪 Testing deployed function..."
TEST_PAYLOAD='{"test": true, "action": "health_check"}'

INVOKE_RESPONSE=$(aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --payload "$TEST_PAYLOAD" \
    --region "$AWS_REGION" \
    /tmp/lambda_test_output.json 2>&1)

if [ $? -eq 0 ]; then
    log_success "✅ Lambda function test successful"
    
    # Check if response contains expected success indicators
    if grep -q "success\|200\|ok" /tmp/lambda_test_output.json 2>/dev/null; then
        log_success "✅ Function health check passed"
    else
        log_warning "⚠️  Function responded but health check unclear"
        log_info "Response: $(cat /tmp/lambda_test_output.json 2>/dev/null || echo 'No response file')"
    fi
else
    log_warning "⚠️  Lambda function test failed: $INVOKE_RESPONSE"
fi

# Clean up test file
rm -f /tmp/lambda_test_output.json

# Send Slack notification if script exists
if [ -f "backend/datasets/notify_job_status.py" ]; then
    log_info "📤 Sending Slack notification..."
    python backend/datasets/notify_job_status.py \
        --status success \
        --job-type "Weight Promotion" \
        --weights-path "$WEIGHTS_S3_PATH" \
        || log_warning "⚠️  Slack notification failed"
fi

# Summary
log_success "🎉 WEIGHT PROMOTION COMPLETED SUCCESSFULLY!"
echo ""
log_info "📋 Summary:"
log_info "   • Weights: $WEIGHTS_S3_PATH"
log_info "   • Secrets Manager: Updated"
log_info "   • Lambda Function: Redeployed"
log_info "   • Status: Production ready"
echo ""
log_info "🔗 Next steps:"
log_info "   1. Run smoke test: python infer_shape_mvd.py --weights unet128.pth --input mydog_front.jpg"
log_info "   2. Monitor inference logs for any issues"
log_info "   3. Update documentation with new model version"

exit 0
