#!/bin/bash
# PetPlantr Stripe + EventBridge Production Deployment
# Story 3.4: Stripe + EventBridge prod toggle

set -e

echo "💳 Deploying PetPlantr Stripe + EventBridge Production Setup"
echo "==========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_ROOT/infrastructure"
ENV_FILE="$PROJECT_ROOT/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ .env file not found at $ENV_FILE${NC}"
    echo "Please create the .env file with production variables"
    exit 1
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Check required environment variables
check_env_var() {
    local var_name=$1
    local var_value=${!var_name}

    if [ -z "$var_value" ] || [ "$var_value" = "your_${var_name,,}_here" ]; then
        echo -e "${RED}❌ $var_name is not set or is placeholder${NC}"
        return 1
    fi
    return 0
}

echo "🔍 Checking environment variables..."
REQUIRED_VARS=(
    "STRIPE_PROD_SECRET_KEY"
    "STRIPE_PROD_PUBLISHABLE_KEY"
    "AWS_REGION"
    "AWS_ACCOUNT_ID"
)

missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
    if ! check_env_var "$var"; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing or invalid environment variables:${NC}"
    printf '   - %s\n' "${missing_vars[@]}"
    echo ""
    echo "Please update your .env file with the correct values"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables validated${NC}"

# Check AWS CLI configuration
echo "🔍 Checking AWS CLI configuration..."
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS CLI not configured or invalid credentials${NC}"
    echo "Please run: aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"

# Navigate to infrastructure directory
cd "$INFRA_DIR"

# Initialize Terraform if not already initialized
if [ ! -d ".terraform" ]; then
    echo "🏗️  Initializing Terraform..."
    terraform init
fi

# Validate Terraform configuration
echo "🔍 Validating Terraform configuration..."
terraform validate

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Terraform validation failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Terraform configuration valid${NC}"

# Plan Terraform changes
echo "📋 Planning Terraform changes..."
terraform plan -out=tfplan

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Terraform plan failed${NC}"
    exit 1
fi

# Ask for confirmation
echo ""
echo -e "${YELLOW}⚠️  This will deploy production Stripe + EventBridge infrastructure${NC}"
read -p "Do you want to continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Apply Terraform changes
echo "🚀 Applying Terraform changes..."
terraform apply tfplan

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Terraform apply failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"

# Get outputs
echo "📋 Getting deployment outputs..."
WEBHOOK_ENDPOINT=$(terraform output -raw webhook_endpoint)
EVENTBRIDGE_BUS_ARN=$(terraform output -raw eventbridge_bus_arn)
LAMBDA_ARN=$(terraform output -raw lambda_function_arn)

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "📋 Deployment Summary:"
echo "   Webhook Endpoint: $WEBHOOK_ENDPOINT"
echo "   EventBridge Bus: $EVENTBRIDGE_BUS_ARN"
echo "   Lambda Function: $LAMBDA_ARN"
echo ""

# Instructions for Stripe configuration
echo "📋 Next Steps - Stripe Configuration:"
echo "   1. Go to Stripe Dashboard → Webhooks"
echo "   2. Add endpoint: $WEBHOOK_ENDPOINT"
echo "   3. Select events:"
echo "      - payment_intent.succeeded"
echo "      - payment_intent.payment_failed"
echo "      - customer.subscription.created"
echo "      - customer.subscription.updated"
echo "      - customer.subscription.deleted"
echo "      - invoice.payment_succeeded"
echo "      - invoice.payment_failed"
echo "   4. Copy the webhook signing secret"
echo "   5. Update STRIPE_WEBHOOK_SECRET in .env"
echo ""

# Test the webhook endpoint
echo "🧪 Testing webhook endpoint..."
curl -X POST "$WEBHOOK_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}' \
  --max-time 10 \
  --silent \
  --output /dev/null \
  --write-out "HTTP Status: %{http_code}\n"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Webhook endpoint is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Webhook endpoint test failed - this is normal before Stripe configuration${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Stripe + EventBridge setup complete!${NC}"
echo ""
echo "💡 Remember to:"
echo "   • Update your frontend with production Stripe publishable key"
echo "   • Test payments with small amounts first"
echo "   • Monitor CloudWatch logs for webhook processing"
echo "   • Set up alerts for payment failures"

# Save deployment information
DEPLOYMENT_INFO="$PROJECT_ROOT/stripe_deployment_$(date +%Y%m%d_%H%M%S).json"
cat > "$DEPLOYMENT_INFO" << EOF
{
  "deployment_date": "$(date -Iseconds)",
  "webhook_endpoint": "$WEBHOOK_ENDPOINT",
  "eventbridge_bus_arn": "$EVENTBRIDGE_BUS_ARN",
  "lambda_function_arn": "$LAMBDA_ARN",
  "environment": "production",
  "status": "deployed"
}
EOF

echo ""
echo "💾 Deployment information saved to: $DEPLOYMENT_INFO"
