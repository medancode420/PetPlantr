#!/bin/bash
# Beta-0 Quick Fix Script
# Usage: ./scripts/beta-quick-fix.sh [scenario]

set -e

echo "🔧 PetPlantr Beta-0 Quick Fixes"
echo "==============================="

case "${1:-menu}" in
  "print-done"|"1")
    echo "🖨️  Fixing PRINT_DONE Issues..."
    
    echo "1. Testing Slack webhook first..."
    if curl -s -X POST "$SLACK_WEBHOOK_URL" \
      -H 'Content-Type: application/json' \
      -d '{"text":"🔧 Testing webhook during fix", "channel":"#ops-alerts"}'; then
      echo "✅ Slack webhook working"
    else
      echo "❌ Slack webhook failed - check SLACK_WEBHOOK_URL in .env"
      echo "Current value: ${SLACK_WEBHOOK_URL:-'NOT SET'}"
      exit 1
    fi
    
    echo "2. Redeploying notifyCustomer function..."
    npx dotenv-cli -e .env -- npx serverless deploy --function notifyCustomer
    
    echo "3. Testing notifyCustomer directly..."
    aws lambda invoke \
      --function-name petplantr-pipeline-dev-notifyCustomer \
      --payload '{"orderId":"fix-test-'$(date +%s)'","userId":"test_user","readyStlKey":"test.stl","status":"READY"}' \
      fix-test-output.json
    cat fix-test-output.json
    rm fix-test-output.json
    ;;

  "lambda"|"2")
    echo "⚡ Fixing Lambda Function Issues..."
    
    if [ -z "$2" ]; then
      echo "Please specify function name:"
      echo "  ./scripts/beta-quick-fix.sh lambda createCheckout"
      echo "  ./scripts/beta-quick-fix.sh lambda stripeWebhook"
      echo "  ./scripts/beta-quick-fix.sh lambda [function-name]"
      exit 1
    fi
    
    FUNCTION_NAME="$2"
    echo "1. Checking current environment variables for $FUNCTION_NAME..."
    aws lambda get-function-configuration \
      --function-name "petplantr-pipeline-dev-$FUNCTION_NAME" \
      --query 'Environment.Variables' \
      --output table
    
    echo "2. Redeploying function with fresh environment..."
    npx dotenv-cli -e .env -- npx serverless deploy --function "$FUNCTION_NAME"
    
    echo "3. Function redeployed successfully ✅"
    ;;

  "stripe"|"3")
    echo "💳 Fixing Stripe Webhook Issues..."
    
    echo "1. Current webhook secret in .env:"
    grep STRIPE_WEBHOOK_SECRET .env || echo "❌ STRIPE_WEBHOOK_SECRET not found in .env"
    
    echo ""
    echo "2. To fix signature mismatch:"
    echo "   a. Go to Stripe Dashboard > Webhooks"
    echo "   b. Click your webhook endpoint"
    echo "   c. Click 'Reveal' next to Signing secret"
    echo "   d. Copy the whsec_... value"
    echo "   e. Update .env: STRIPE_WEBHOOK_SECRET=whsec_NEW_VALUE"
    echo ""
    read -p "Have you updated STRIPE_WEBHOOK_SECRET in .env? (y/N): " confirm
    
    if [[ $confirm == [yY] ]]; then
      echo "3. Redeploying stripeWebhook function..."
      npx dotenv-cli -e .env -- npx serverless deploy --function stripeWebhook
      echo "✅ Stripe webhook function redeployed"
    else
      echo "❌ Please update .env first, then re-run this script"
    fi
    ;;

  "stepfunctions"|"4")
    echo "🔀 Fixing Step Functions Issues..."
    
    echo "1. Checking IAM roles and policies..."
    aws iam get-role \
      --role-name "PetPlantr-StepFunctionRole-dev" \
      --query 'Role.RoleName' \
      --output text || echo "❌ Step Function role not found"
    
    echo "2. Checking S3 bucket permissions..."
    aws s3api get-bucket-policy \
      --bucket petplantr-uploads-dev \
      --query 'Policy' \
      --output text 2>/dev/null || echo "⚠️  No bucket policy found"
    
    echo "3. Redeploying entire stack to fix permissions..."
    read -p "Redeploy entire serverless stack? This may take 2-3 minutes (y/N): " confirm
    
    if [[ $confirm == [yY] ]]; then
      npx dotenv-cli -e .env -- npx serverless deploy
      echo "✅ Full stack redeployed"
    else
      echo "💡 Manual fix: Check Step Function execution in AWS Console"
      echo "   https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines"
    fi
    ;;

  "menu"|*)
    echo "Choose a fix scenario:"
    echo "1. print-done    - Fix PRINT_DONE notifications"
    echo "2. lambda        - Fix Lambda function errors"  
    echo "3. stripe        - Fix Stripe webhook issues"
    echo "4. stepfunctions - Fix Step Functions failures"
    echo ""
    echo "Usage examples:"
    echo "  ./scripts/beta-quick-fix.sh print-done"
    echo "  ./scripts/beta-quick-fix.sh lambda stripeWebhook"
    echo "  ./scripts/beta-quick-fix.sh stripe"
    ;;
esac

echo ""
echo "🎯 Fix complete! Run diagnostics to verify:"
echo "   ./scripts/beta-diagnostics.sh"
