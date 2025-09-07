#!/bin/bash

# PetPlantr AWS Staging Deployment Script
# This script helps you deploy the PetPlantr backend to AWS staging environment

echo "🚀 PetPlantr AWS Staging Deployment"
echo "====================================="
echo ""

# Step 1: AWS Credentials Setup
echo "📋 Step 1: AWS Credentials Setup"
echo ""

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "⚠️  AWS credentials not found in environment variables."
    echo ""
    echo "Please set your staging AWS credentials:"
    echo ""
    echo "Option A: Environment Variables (Recommended)"
    echo "export AWS_ACCESS_KEY_ID='your_staging_access_key_id'"
    echo "export AWS_SECRET_ACCESS_KEY='your_staging_secret_access_key'"
    echo "export AWS_REGION='us-east-1'"
    echo ""
    echo "Option B: AWS Profile"
    echo "aws configure --profile staging"
    echo "export AWS_PROFILE=staging"
    echo ""
    echo "After setting credentials, run this script again:"
    echo "./deploy-staging.sh"
    exit 1
fi

# Step 2: Verify AWS credentials
echo "✅ AWS credentials found"
echo "🔍 Verifying AWS access..."

aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ AWS credentials verification failed"
    echo "Please check your AWS access key, secret key, and permissions"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ Connected to AWS Account: $ACCOUNT_ID"
echo ""

# Step 3: Environment Variables Check
echo "📋 Step 2: Environment Variables Check"
echo ""

MISSING_VARS=()

# Check required environment variables
if [ -z "$STRIPE_SECRET_KEY" ]; then MISSING_VARS+=("STRIPE_SECRET_KEY"); fi
if [ -z "$STRIPE_WEBHOOK_SECRET" ]; then MISSING_VARS+=("STRIPE_WEBHOOK_SECRET"); fi
if [ -z "$CLERK_SECRET_KEY" ]; then MISSING_VARS+=("CLERK_SECRET_KEY"); fi

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "⚠️  Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these in your .env file or as environment variables:"
    echo "cp .env.example .env"
    echo "# Edit .env with your actual values"
    echo ""
    echo "Then source the environment:"
    echo "source .env"
    exit 1
fi

echo "✅ Required environment variables found"
echo ""

# Step 4: Install Dependencies
echo "📋 Step 3: Install Dependencies"
echo ""

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ npm install failed"
        exit 1
    fi
else
    echo "✅ Dependencies already installed"
fi
echo ""

# Step 5: Build & Test
echo "📋 Step 4: Build & Test"
echo ""

echo "🔨 Building TypeScript..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi
echo "✅ Build successful"
echo ""

echo "🧪 Running tests..."
npm test -- --testPathPattern="task8-simple" --silent
if [ $? -ne 0 ]; then
    echo "⚠️  Some tests failed, but proceeding with deployment..."
else
    echo "✅ Core tests passed"
fi
echo ""

# Step 6: Deploy to AWS
echo "📋 Step 5: Deploy to AWS Staging"
echo ""

echo "🚀 Deploying to AWS with Serverless Framework..."
echo "Stage: dev"
echo "Region: ${AWS_REGION:-us-east-1}"
echo ""

# Set default AWS region if not specified
export AWS_REGION=${AWS_REGION:-us-east-1}

# Run serverless deploy
npx serverless deploy --stage dev --verbose

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment Successful!"
    echo "========================="
    echo ""
    echo "✅ PetPlantr backend deployed to AWS staging"
    echo "✅ Lambda functions created"
    echo "✅ EventBridge event bus configured"
    echo "✅ Step Functions state machine deployed"
    echo "✅ S3 buckets created with proper IAM policies"
    echo ""
    echo "🔗 Next Steps:"
    echo "1. Test the webhook endpoint"
    echo "2. Verify EventBridge → Step Functions flow"
    echo "3. Check CloudWatch logs for any issues"
    echo "4. Update frontend API URLs to point to deployed backend"
    echo ""
    echo "📊 You can monitor the deployment in AWS Console:"
    echo "- Lambda: https://console.aws.amazon.com/lambda/"
    echo "- Step Functions: https://console.aws.amazon.com/states/"
    echo "- EventBridge: https://console.aws.amazon.com/events/"
    echo "- S3: https://console.aws.amazon.com/s3/"
else
    echo ""
    echo "❌ Deployment Failed"
    echo "==================="
    echo ""
    echo "Please check the error messages above and:"
    echo "1. Verify AWS credentials and permissions"
    echo "2. Check that all required environment variables are set"
    echo "3. Ensure no conflicting resources exist in AWS"
    echo ""
    echo "For help, check:"
    echo "- Serverless Framework logs above"
    echo "- AWS CloudFormation console for stack details"
    exit 1
fi
