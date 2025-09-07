#!/bin/bash
# Simplified Real-Time Performance Test for PetPlantr

echo "🧪 PetPlantr Real Performance Test"
echo "=================================="

API_BASE="https://petplantr.vercel.app"

echo ""
echo "🔍 Health Check Test"
start_time=$(date +%s.%N)
health_response=$(curl -s "$API_BASE/api/health")
end_time=$(date +%s.%N)
health_duration=$(echo "($end_time - $start_time) * 1000" | bc | cut -d. -f1)

echo "Health check: ${health_duration}ms"
echo "Pipeline status: $(echo $health_response | jq -r '.pipeline // "unknown"')"

echo ""
echo "🤖 Breed Detection Performance Test"
echo "Test 1: Using form upload endpoint..."

# Create a simple test image
temp_image="/tmp/test_dog.jpg"
curl -s "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400" -o "$temp_image"

if [ -f "$temp_image" ]; then
    echo "Downloaded test image: $(ls -lh $temp_image | awk '{print $5}')"
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST \
        -F "file=@$temp_image" \
        -F "use_tta=false" \
        -F "confidence_threshold=0.7" \
        "$API_BASE/api/v1/breed/detect")
    end_time=$(date +%s.%N)
    
    duration=$(echo "($end_time - $start_time) * 1000" | bc | cut -d. -f1)
    
    echo "API Response time: ${duration}ms"
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        predicted_breed=$(echo "$response" | jq -r '.predicted_breed // "error"')
        confidence=$(echo "$response" | jq -r '.confidence // 0')
        echo "Predicted breed: $predicted_breed"
        echo "Confidence: $confidence"
        echo "Status: ✅ SUCCESS"
    else
        echo "Response: $response"
        echo "Status: ❌ API ERROR"
    fi
    
    rm -f "$temp_image"
else
    echo "❌ Failed to download test image"
fi

echo ""
echo "📊 Performance Summary"
echo "===================="
echo "Health endpoint: ${health_duration}ms"
echo "Breed detection: ${duration:-N/A}ms"

# Check thresholds
if [ "${duration:-9999}" -lt 500 ]; then
    echo "✅ Performance: PASS (under 500ms threshold)"
    exit 0
else
    echo "⚠️  Performance: REVIEW (over 500ms threshold)"
    exit 1
fi
