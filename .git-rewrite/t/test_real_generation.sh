#!/bin/bash

echo "🎯 Testing REAL AI Model Generation"
echo "=================================="

# Test the production API with real model generation
echo "🚀 Generating 3D model with real AI..."

RESPONSE=$(curl -s -X POST https://petplantr.vercel.app/api/replicate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "cute geometric dog planter, terracotta style, minimalist design"
  }')

echo "📋 API Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

echo ""
echo "✅ SUCCESS INDICATORS:"
echo "• Status: 'processing'"
echo "• Used Model: 'cjwbw/shap-e' or 'cjwbw/point-e'"
echo "• Prediction ID: Present"
echo "• No demo fallback mentioned"
