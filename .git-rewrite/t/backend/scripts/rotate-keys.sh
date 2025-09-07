#!/bin/bash

# PetPlantr Security Update Script
# Updates AWS Secrets Manager with new rotated keys

echo "🔐 PetPlantr Security Key Rotation Script"
echo "=========================================="
echo ""

# Check if keys are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "❌ Usage: $0 <NEW_STRIPE_SECRET_KEY> <NEW_STRIPE_PUBLISHABLE_KEY>"
    echo ""
    echo "📋 Steps to get new keys:"
    echo "1. Go to https://dashboard.stripe.com/apikeys"
    echo "2. Click 'Roll key' for both Secret and Publishable test keys"
    echo "3. Copy the new keys and run this script"
    echo ""
    echo "Example:"
    echo "$0 sk_test_NEW_SECRET_KEY pk_test_NEW_PUBLISHABLE_KEY"
    exit 1
fi

NEW_STRIPE_SECRET_KEY="$1"
NEW_STRIPE_PUBLISHABLE_KEY="$2"

echo "🔄 Updating Stripe Secret Key in AWS Secrets Manager..."
aws secretsmanager update-secret \
    --secret-id "petplantr/stripe/secret-key" \
    --secret-string "$NEW_STRIPE_SECRET_KEY"

if [ $? -eq 0 ]; then
    echo "✅ Stripe Secret Key updated successfully"
else
    echo "❌ Failed to update Stripe Secret Key"
    exit 1
fi

echo ""
echo "🔄 Updating Stripe Publishable Key in AWS Secrets Manager..."
aws secretsmanager update-secret \
    --secret-id "petplantr/stripe/publishable-key" \
    --secret-string "$NEW_STRIPE_PUBLISHABLE_KEY"

if [ $? -eq 0 ]; then
    echo "✅ Stripe Publishable Key updated successfully"
else
    echo "❌ Failed to update Stripe Publishable Key"
    exit 1
fi

echo ""
echo "🚀 Redeploying backend with new secrets..."
npm run deploy

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Security update complete!"
    echo "✅ Keys rotated and stored in AWS Secrets Manager"
    echo "✅ Backend redeployed with new secure configuration"
    echo ""
    echo "🔍 Next steps:"
    echo "1. Update frontend .env with new publishable key"
    echo "2. Test the smoke test to verify everything works"
    echo "3. Update any local development .env files"
else
    echo "❌ Deployment failed. Check the error above."
    exit 1
fi
