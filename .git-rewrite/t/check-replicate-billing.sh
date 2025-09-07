#!/bin/bash

# Replicate Billing Status Checker
# Checks when billing becomes active after setup

source .env.local

echo "🔍 Checking Replicate Billing Status"
echo "====================================="

# Test a small, quick model to check billing status
echo "Testing billing status with FLUX Schnell..."

RESPONSE=$(curl -s -H "Authorization: Token ${REPLICATE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "c846a69991daf4c0e5d016514849d14ee5b2e6846ce6b9d6f21369e564cfe51e",
    "input": {
      "prompt": "test",
      "num_outputs": 1,
      "aspect_ratio": "1:1",
      "output_format": "jpg"
    }
  }' \
  "https://api.replicate.com/v1/predictions")

# Check response
if echo "$RESPONSE" | grep -q '"id"'; then
  echo "✅ SUCCESS: Billing is active!"
  echo "🎉 Replicate API is ready for real AI processing"
  PREDICTION_ID=$(echo "$RESPONSE" | jq -r '.id')
  echo "📄 Test prediction ID: $PREDICTION_ID"
  
  echo ""
  echo "🚀 Ready to use real AI in PetPlantr!"
  echo "   • Upload images will use real FLUX AI"
  echo "   • Test at: http://localhost:3000/upload"
  
elif echo "$RESPONSE" | grep -q "402"; then
  echo "⚠️  PENDING: Billing setup is still propagating"
  echo "💡 This can take 2-10 minutes after adding billing"
  echo "🔄 You can run this script again to check status"
  
  echo ""
  echo "📝 In the meantime:"
  echo "   • Demo mode will continue working"
  echo "   • Upload workflow is fully functional"
  echo "   • System will automatically switch when ready"
  
elif echo "$RESPONSE" | grep -q "422"; then
  echo "❌ ERROR: Model version issue"
  echo "💡 The FLUX model might not be available"
  echo "🔧 Using demo mode as fallback"
  
else
  echo "❓ UNKNOWN: Unexpected response"
  echo "Response: $RESPONSE"
fi

echo ""
echo "📊 Current Status Summary:"
echo "  • API Token: ${REPLICATE_API_TOKEN:0:8}..."
echo "  • Billing: $(echo "$RESPONSE" | grep -q '"id"' && echo "Active" || echo "Pending")"
echo "  • Demo Mode: Always available"
echo "  • Real AI Mode: $(echo "$RESPONSE" | grep -q '"id"' && echo "Ready" || echo "Pending billing")"
