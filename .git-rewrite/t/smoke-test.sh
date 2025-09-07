#!/bin/bash
# PetPlantr 90-Second Smoke Test
# Tests the complete pipeline: Image → Shap-E → S3 → CloudFront

set -e

echo "🔥 PetPlantr 90-Second Smoke Test"
echo "================================="

# Load environment variables
if [ -f ".env.local" ]; then
    export $(grep -v '^#' .env.local | xargs)
fi

# Verify required variables
echo "📋 Checking environment variables..."
: ${REPLICATE_API_TOKEN:?"❌ REPLICATE_API_TOKEN not set"}
: ${AWS_S3_BUCKET:?"❌ AWS_S3_BUCKET not set"}
: ${NEXT_PUBLIC_CLOUDFRONT_DOMAIN:?"❌ NEXT_PUBLIC_CLOUDFRONT_DOMAIN not set"}

echo "✅ Environment variables verified"

# 1. Create or use test image
TEST_IMG="test-dog.jpg"
if [ ! -f "$TEST_IMG" ]; then
    echo "📸 Creating test image..."
    # Create a simple test image (1x1 pixel JPEG)
    echo "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/gA==" | base64 -d > "$TEST_IMG"
fi

echo "📤 Using test image: $TEST_IMG ($(stat -f%z "$TEST_IMG") bytes)"

# 2. Get latest Shap-E version
echo "🔍 Getting latest Shap-E model version..."
SHAP_E_VERSION=$(curl -s \
    -H "Authorization: Token $REPLICATE_API_TOKEN" \
    "https://api.replicate.com/v1/models/openai/shap-e" | \
    jq -r '.latest_version.id' 2>/dev/null || echo "db21e45d2af044e1f0b70a28159bff17b5dc7b7b8b3ceafe7f54b132b22ea6ee")

echo "🤖 Using Shap-E version: $SHAP_E_VERSION"

# 3. Encode image to base64
echo "🔄 Encoding image..."
IMAGE_B64=$(base64 -i "$TEST_IMG" | tr -d '\n')

# 4. Call Shap-E via Replicate
echo "🚀 Starting Shap-E prediction..."
PREDICTION_JSON=$(curl -s \
    -H "Authorization: Token $REPLICATE_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"version\": \"$SHAP_E_VERSION\",
        \"input\": {
            \"image\": \"data:image/jpeg;base64,$IMAGE_B64\",
            \"guidance_scale\": 15.0,
            \"num_inference_steps\": 64
        }
    }" \
    https://api.replicate.com/v1/predictions)

PRED_ID=$(echo "$PREDICTION_JSON" | jq -r '.id // empty')

if [ -z "$PRED_ID" ]; then
    echo "❌ Failed to start prediction"
    echo "Response: $PREDICTION_JSON"
    exit 1
fi

echo "✅ Prediction started: $PRED_ID"

# 5. Poll until finished (max 120 seconds)
echo "⏳ Waiting for completion..."
for i in {1..40}; do
    sleep 3
    STATUS_JSON=$(curl -s \
        -H "Authorization: Token $REPLICATE_API_TOKEN" \
        "https://api.replicate.com/v1/predictions/$PRED_ID")
    
    STATUS=$(echo "$STATUS_JSON" | jq -r '.status // "unknown"')
    echo "   Status: $STATUS (${i}x3s)"
    
    if [ "$STATUS" = "succeeded" ]; then
        GLB_URL=$(echo "$STATUS_JSON" | jq -r '.output[0] // empty')
        if [ -n "$GLB_URL" ]; then
            echo "✅ Shap-E completed → $GLB_URL"
            break
        else
            echo "❌ No output URL in response"
            exit 1
        fi
    elif [ "$STATUS" = "failed" ]; then
        ERROR=$(echo "$STATUS_JSON" | jq -r '.error // "Unknown error"')
        echo "❌ Prediction failed: $ERROR"
        exit 1
    elif [ "$STATUS" = "canceled" ]; then
        echo "❌ Prediction was canceled"
        exit 1
    fi
    
    if [ $i -eq 40 ]; then
        echo "⏰ Timeout waiting for prediction"
        exit 1
    fi
done

# 6. Download and copy GLB to S3
echo "📦 Copying GLB to S3..."
GLB_KEY="models/$PRED_ID.glb"
S3_PATH="s3://$AWS_S3_BUCKET/$GLB_KEY"

# Download GLB temporarily
TEMP_GLB="/tmp/$PRED_ID.glb"
curl -s -o "$TEMP_GLB" "$GLB_URL"

# Upload to S3 with proper content type
aws s3 cp "$TEMP_GLB" "$S3_PATH" \
    --content-type "model/gltf-binary" \
    --cache-control "public, max-age=31536000"

# Clean up temp file
rm -f "$TEMP_GLB"

# 7. Generate final CDN URL
FINAL_URL="https://$NEXT_PUBLIC_CLOUDFRONT_DOMAIN/$GLB_KEY"
echo "🌐 Model uploaded to CDN: $FINAL_URL"

# 8. Verify CDN access
echo "🔍 Verifying CDN access..."
if curl -s -I "$FINAL_URL" | grep -q "200 OK"; then
    echo "✅ CDN verification successful"
    
    # Get file size
    SIZE=$(curl -s -I "$FINAL_URL" | grep -i content-length | cut -d' ' -f2 | tr -d '\r')
    echo "📊 GLB file size: $SIZE bytes"
    
    echo ""
    echo "🎉 SMOKE TEST PASSED!"
    echo "========================"
    echo "🔗 Model URL: $FINAL_URL"
    echo "📁 S3 Path: $S3_PATH"
    echo "🆔 Prediction ID: $PRED_ID"
    echo ""
    echo "✅ Pipeline ready for frontend integration"
    
else
    echo "❌ CDN verification failed"
    echo "URL: $FINAL_URL"
    exit 1
fi
