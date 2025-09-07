#!/bin/bash
# PetPlantr Quick Status Check
# Run this anytime to verify your setup

echo "🔍 PetPlantr Quick Status Check"
echo "================================"

# Check if we're in the right directory
if [ ! -f ".env.local" ]; then
    echo "❌ Run this from PetPlantr root directory"
    exit 1
fi

echo "📍 Location: $(pwd)"
echo "📋 Checking key components..."

# Check AWS CLI
if aws sts get-caller-identity > /dev/null 2>&1; then
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    echo "✅ AWS CLI: Connected (Account: $ACCOUNT)"
else
    echo "❌ AWS CLI: Not configured"
fi

# Check S3 bucket
if aws s3 ls s3://petplantr-3d-models-prod > /dev/null 2>&1; then
    echo "✅ S3 Bucket: Accessible"
else
    echo "❌ S3 Bucket: Cannot access"
fi

# Check Terraform state
if [ -f "infra/terraform.tfstate" ]; then
    echo "✅ Terraform: Infrastructure deployed"
else
    echo "⚠️  Terraform: No state file found"
fi

# Check environment files
if [ -f ".env.local" ] && [ -f "frontend/.env.local" ]; then
    echo "✅ Environment: Files configured"
else
    echo "❌ Environment: Missing files"
fi

# Check frontend dependencies
if [ -d "frontend/node_modules" ]; then
    echo "✅ Frontend: Dependencies installed"
    if [ -d "frontend/node_modules/cypress" ]; then
        echo "✅ Cypress: Installed"
    else
        echo "⏳ Cypress: Still installing..."
    fi
else
    echo "❌ Frontend: Dependencies missing"
fi

# Check key API tokens
if grep -q "r8_" .env.local; then
    echo "✅ Replicate API: Token configured"
else
    echo "❌ Replicate API: Token missing"
fi

if grep -q "AWS_ACCESS_KEY_ID=" .env.local && [ -n "$(grep AWS_ACCESS_KEY_ID .env.local | cut -d'=' -f2)" ]; then
    echo "✅ AWS Keys: Configured"
else
    echo "❌ AWS Keys: Missing"
fi

echo ""
echo "🚀 Quick Actions:"
echo "  • Health check: python scripts/health_check.py"
echo "  • Start dev server: cd frontend && npm run dev"
echo "  • Deploy: cd frontend && vercel"
echo "  • E2E tests: make e2e-test (when Cypress ready)"
echo ""
echo "📖 Full guide: see DEPLOYMENT_READY.md"
