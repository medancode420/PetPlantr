#!/bin/bash

# PetPlantr Webhook Testing Script
# Tests the deployed webhook endpoint

echo "🧪 PetPlantr Webhook Test"
echo "========================="
echo ""

WEBHOOK_URL="https://mfxyjhg1l6.execute-api.us-east-1.amazonaws.com/dev/api/stripe/webhook"

echo "🔍 Testing webhook endpoint: $WEBHOOK_URL"
echo ""

# Test with a basic POST request
echo "📋 Step 1: Testing basic webhook endpoint availability..."
response=$(curl -s -w "%{http_code}" -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -H "Stripe-Signature: t=fake,v1=fake" \
    -d '{"type":"test"}' \
    -o /tmp/webhook_response.json)

echo "HTTP Status: $response"

if [ "$response" = "400" ] || [ "$response" = "401" ]; then
    echo "✅ Webhook endpoint is responding (400/401 expected for invalid signature)"
    echo ""
    echo "📋 Step 2: Check CloudWatch logs..."
    echo "Go to: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/%2Faws%2Flambda%2Fpetplantr-pipeline-dev-stripeWebhook"
    echo ""
    echo "📋 Step 3: In Stripe Dashboard:"
    echo "1. Go to: https://dashboard.stripe.com/webhooks"
    echo "2. Click on your webhook endpoint"
    echo "3. Click 'Send test webhook'"
    echo "4. Select 'checkout.session.completed'"
    echo "5. Verify the webhook succeeds"
elif [ "$response" = "200" ]; then
    echo "⚠️  Unexpected 200 response - webhook might not be validating signatures properly"
else
    echo "❌ Webhook endpoint error. Status: $response"
    echo "Response body:"
    cat /tmp/webhook_response.json
fi

echo ""
echo "🔍 To monitor webhook failures:"
echo "1. CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups"
echo "2. Stripe Dashboard: https://dashboard.stripe.com/webhooks"
echo "3. AWS X-Ray (if enabled): https://console.aws.amazon.com/xray/home"
