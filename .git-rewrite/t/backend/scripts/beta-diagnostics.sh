#!/bin/bash
# Beta-0 Quick Diagnostics Script
# Usage: ./scripts/beta-diagnostics.sh [scenario]

set -e

echo "🔍 PetPlantr Beta-0 Diagnostics"
echo "==============================="

# Get current timestamp for log filtering (macOS compatible)
THIRTY_MIN_AGO=$(date -v-30M +%s)000
TEN_MIN_AGO=$(date -v-10M +%s)000

case "${1:-all}" in
  "print-done"|"1")
    echo "🖨️  Diagnosing PRINT_DONE Issues..."
    echo "Checking notifyCustomer logs for errors in last 30 minutes:"
    aws logs filter-log-events \
      --log-group-name '/aws/lambda/petplantr-pipeline-dev-notifyCustomer' \
      --filter-pattern 'ERROR' \
      --start-time $THIRTY_MIN_AGO \
      --query 'events[].message' \
      --output text || echo "No errors found or log group doesn't exist"
    
    echo ""
    echo "Testing Slack webhook connectivity:"
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
      curl -s -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d '{"text":"🧪 Diagnostic test from beta-diagnostics.sh", "channel":"#ops-alerts"}' \
        && echo "✅ Slack webhook test successful" \
        || echo "❌ Slack webhook test failed"
    else
      echo "❌ SLACK_WEBHOOK_URL not set in environment"
    fi
    ;;

  "lambda"|"2")
    echo "⚡ Diagnosing Lambda Errors..."
    echo "Checking all Lambda functions for recent errors:"
    for func in createCheckout stripeWebhook presignUpload downloadPhotos generateSTL processSTL notifyCustomer handleError; do
      echo "--- $func ---"
      aws logs filter-log-events \
        --log-group-name "/aws/lambda/petplantr-pipeline-dev-$func" \
        --filter-pattern 'ERROR' \
        --start-time $TEN_MIN_AGO \
        --query 'events[0].message' \
        --output text 2>/dev/null || echo "No recent errors"
    done
    ;;

  "stripe"|"3")
    echo "💳 Diagnosing Stripe Webhook Issues..."
    echo "Checking stripeWebhook for signature errors:"
    aws logs filter-log-events \
      --log-group-name '/aws/lambda/petplantr-pipeline-dev-stripeWebhook' \
      --filter-pattern 'signature' \
      --start-time $TEN_MIN_AGO \
      --query 'events[].message' \
      --output text || echo "No signature errors found"
    
    echo ""
    echo "Checking for any webhook errors:"
    aws logs filter-log-events \
      --log-group-name '/aws/lambda/petplantr-pipeline-dev-stripeWebhook' \
      --filter-pattern 'ERROR' \
      --start-time $TEN_MIN_AGO \
      --query 'events[].message' \
      --output text || echo "No errors found"
    ;;

  "stepfunctions"|"4")
    echo "🔀 Diagnosing Step Functions..."
    echo "Recent executions status:"
    aws stepfunctions list-executions \
      --state-machine-arn "arn:aws:states:us-east-1:$(aws sts get-caller-identity --query Account --output text):stateMachine:ProcessOrderStateMachine-dev" \
      --max-items 5 \
      --query 'executions[].{Name:name,Status:status,StartDate:startDate}' \
      --output table || echo "Unable to list executions"
    
    echo ""
    echo "💡 If executions are FAILED, check AWS Console:"
    echo "   https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines"
    ;;

  "all"|*)
    echo "🔍 Running all diagnostics..."
    ./scripts/beta-diagnostics.sh print-done
    echo ""
    ./scripts/beta-diagnostics.sh lambda  
    echo ""
    ./scripts/beta-diagnostics.sh stripe
    echo ""
    ./scripts/beta-diagnostics.sh stepfunctions
    ;;
esac

echo ""
echo "🎯 Quick Fixes:"
echo "1. PRINT_DONE: Restart OctoFarm or redeploy notifyCustomer"
echo "2. Lambda: Check env vars, redeploy function" 
echo "3. Stripe: Update webhook secret, redeploy stripeWebhook"
echo "4. Step Functions: Check IAM roles and S3 permissions"
echo ""
echo "For detailed fixes, run: ./scripts/beta-quick-fix.sh [scenario]"
