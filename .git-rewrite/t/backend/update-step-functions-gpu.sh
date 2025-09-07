#!/bin/bash

# Update Step Functions to use GPU-powered ECS containers
# This script updates the existing Step Functions state machine

set -e

echo "🔄 Updating Step Functions for GPU Containers"
echo "=============================================="

# Configuration
AWS_REGION="us-east-1"
STATE_MACHINE_NAME="petplantr-process-order-dev"

# Check dependencies
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed"; exit 1; }

# Check AWS authentication
echo "🔐 Checking AWS authentication..."
aws sts get-caller-identity > /dev/null || { echo "❌ AWS authentication failed"; exit 1; }

# Get current state machine ARN
echo "🔍 Finding Step Functions state machine..."
STATE_MACHINE_ARN=$(aws stepfunctions list-state-machines \
    --region $AWS_REGION \
    --query "stateMachines[?name=='$STATE_MACHINE_NAME'].stateMachineArn" \
    --output text)

if [ -z "$STATE_MACHINE_ARN" ]; then
    echo "❌ State machine not found: $STATE_MACHINE_NAME"
    exit 1
fi

echo "✅ Found state machine: $STATE_MACHINE_ARN"

# Check if GPU-enhanced definition exists
GPU_DEFINITION_FILE="config/gpu-enhanced-step-functions.json"
if [ ! -f "$GPU_DEFINITION_FILE" ]; then
    echo "❌ GPU-enhanced Step Functions definition not found: $GPU_DEFINITION_FILE"
    exit 1
fi

echo "📋 GPU-enhanced definition file: $GPU_DEFINITION_FILE"

# Update the state machine
echo "🔄 Updating Step Functions state machine..."
aws stepfunctions update-state-machine \
    --state-machine-arn "$STATE_MACHINE_ARN" \
    --definition file://$GPU_DEFINITION_FILE \
    --region $AWS_REGION

# Wait for update to complete
echo "⏳ Waiting for update to complete..."
sleep 5

# Verify the update
echo "✅ Checking updated state machine..."
aws stepfunctions describe-state-machine \
    --state-machine-arn "$STATE_MACHINE_ARN" \
    --region $AWS_REGION \
    --query '{name: name, status: status, type: type, creationDate: creationDate}' \
    --output table

echo ""
echo "🎉 Step Functions Update Complete!"
echo "=================================="
echo ""
echo "✅ Updated Components:"
echo "   • Feature Extraction: Now uses ECS with GPU containers"
echo "   • Depth Estimation: Now uses ECS with GPU containers"  
echo "   • Shape-MVD: Now uses ECS with GPU containers"
echo "   • Planter Geometry: Still uses Lambda (lightweight)"
echo "   • Mesh Cleanup: Still uses Lambda (lightweight)"
echo "   • Texture Marking: Still uses Lambda (lightweight)"
echo ""
echo "📊 Performance Improvements:"
echo "   • GPU acceleration for AI inference"
echo "   • Dedicated compute resources"
echo "   • Better memory management"
echo "   • Faster model loading"
echo ""
echo "🔧 Step Functions State Machine: $STATE_MACHINE_NAME"
echo "🌐 ARN: $STATE_MACHINE_ARN"
echo ""
echo "💡 To test the updated pipeline:"
echo "aws stepfunctions start-execution \\"
echo "  --state-machine-arn '$STATE_MACHINE_ARN' \\"
echo "  --input '{\"orderId\":\"gpu-test-001\",\"useAIPipeline\":true,\"photoUrls\":[\"s3://petplantr-uploads-dev/test.jpg\"],\"sizeTier\":\"medium\"}'"
echo ""
