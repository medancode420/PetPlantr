#!/bin/bash

# PetPlantr Slack Alert Test
# Tests the CloudWatch → SNS → Lambda → Slack pipeline

echo "🚨 PetPlantr Slack Alert Test"
echo "=============================="
echo ""

# Get the SNS topic ARN
TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name petplantr-pipeline-dev \
  --query "Stacks[0].Outputs[?OutputKey=='ErrorNotificationTopicArn'].OutputValue" \
  --output text 2>/dev/null)

if [ -z "$TOPIC_ARN" ] || [ "$TOPIC_ARN" = "None" ]; then
  echo "❌ SNS Topic not found. Deploy the backend first:"
  echo "   npm run deploy"
  exit 1
fi

echo "📡 Found SNS Topic: $TOPIC_ARN"

# Test message
TEST_MESSAGE='{
  "AlarmName": "PetPlantr-Test-Alert",
  "AlarmDescription": "Test alert from PetPlantr monitoring system",
  "NewStateValue": "ALARM",
  "NewStateReason": "Manual test triggered by ops team",
  "StateChangeTime": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
  "Region": "us-east-1",
  "AWSAccountId": "'$(aws sts get-caller-identity --query Account --output text)'"
}'

echo ""
echo "📤 Sending test alert to Slack..."

# Send test message
aws sns publish \
  --topic-arn "$TOPIC_ARN" \
  --message "$TEST_MESSAGE" \
  --subject "PetPlantr Test Alert"

if [ $? -eq 0 ]; then
  echo "✅ Test alert sent successfully!"
  echo ""
  echo "📋 Check your Slack channel for the alert."
  echo "   Expected channel: #ops-alerts"
  echo ""
  echo "🔍 Monitor logs:"
  echo "   aws logs tail /aws/lambda/petplantr-pipeline-dev-slackNotifier --follow"
else
  echo "❌ Failed to send test alert"
  exit 1
fi
