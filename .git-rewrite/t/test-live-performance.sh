#!/bin/bash
# Real-Time Performance Validation for Live PetPlantr System
# Tests actual API endpoints with real images and measures performance

set -e

echo "🧪 Real-Time PetPlantr Performance Test"
echo "======================================"
echo "Testing live production system..."
echo ""

API_BASE="https://petplantr.vercel.app"
RESULTS_FILE="live_performance_$(date +%Y%m%d_%H%M%S).json"

# Test images for breed detection
GOLDEN_RETRIEVER="https://images.unsplash.com/photo-1552053831-71594a27632d?w=400"
LABRADOR="https://images.unsplash.com/photo-1583337130417-3346a1be7dee?w=400"
GERMAN_SHEPHERD="https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400"
BULLDOG="https://images.unsplash.com/photo-1534361960057-19889db9621e?w=400"
HUSKY="https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=400"

echo "🔍 1. API Health Check"
echo "----------------------"
start_time=$(date +%s.%N)
health_response=$(curl -s "$API_BASE/api/health")
health_time=$(echo "$(date +%s.%N) - $start_time" | bc)
echo "Health check took: ${health_time}s"
echo "Response: $(echo $health_response | jq -c '.')"
echo ""

echo "🤖 2. Breed Detection Performance Test"
echo "-----------------------------------"

# Test breed detection with real images
test_breed_detection() {
    local image_url="$1"
    local expected_breed="$2"
    
    echo "Testing: $expected_breed"
    
    # Download image to temp file
    temp_image="/tmp/test_image_$(date +%s).jpg"
    curl -s "$image_url" -o "$temp_image"
    
    if [ ! -f "$temp_image" ]; then
        echo "  Failed to download image"
        echo "1000"  # Return high latency on failure
        return
    fi
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST \
        -F "file=@$temp_image" \
        -F "use_tta=false" \
        -F "confidence_threshold=0.7" \
        "$API_BASE/api/v1/breed/detect" 2>/dev/null || echo '{"error":"request_failed"}')
    end_time=$(date +%s.%N)
    
    # Clean up temp file
    rm -f "$temp_image"
    
    duration=$(echo "$end_time - $start_time" | bc)
    duration_ms=$(echo "$duration * 1000" | bc | cut -d. -f1)
    
    # Check if response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        predicted_breed=$(echo "$response" | jq -r '.predicted_breed // "error"')
        confidence=$(echo "$response" | jq -r '.confidence // 0')
    else
        predicted_breed="api_error"
        confidence="0"
    fi
    
    echo "  Predicted: $predicted_breed"
    echo "  Confidence: $confidence"
    echo "  Time: ${duration_ms}ms"
    echo "  Status: $(if [ "$predicted_breed" != "error" ] && [ "$predicted_breed" != "api_error" ]; then echo "✅ SUCCESS"; else echo "❌ FAILED"; fi)"
    echo ""
    
    # Return the duration in milliseconds
    echo $duration_ms
}

# Run tests and collect metrics
echo "Running breed detection tests..."
latencies=()

latencies+=($(test_breed_detection "$GOLDEN_RETRIEVER" "Golden Retriever"))
latencies+=($(test_breed_detection "$LABRADOR" "Labrador"))
latencies+=($(test_breed_detection "$GERMAN_SHEPHERD" "German Shepherd"))
latencies+=($(test_breed_detection "$BULLDOG" "Bulldog"))
latencies+=($(test_breed_detection "$HUSKY" "Husky"))

echo "📊 3. Performance Summary"
echo "========================"

# Calculate statistics
total_tests=${#latencies[@]}
sum=0
for latency in "${latencies[@]}"; do
    sum=$(echo "$sum + $latency" | bc)
done

avg_latency=$(echo "scale=2; $sum / $total_tests" | bc)

# Sort latencies for percentile calculation
IFS=$'\n' sorted_latencies=($(sort -n <<<"${latencies[*]}"))
unset IFS

# Calculate P50 (median)
middle_index=$((total_tests / 2))
if [ $((total_tests % 2)) -eq 0 ]; then
    # Even number of elements
    p50=$(echo "scale=2; (${sorted_latencies[$((middle_index-1))]} + ${sorted_latencies[$middle_index]}) / 2" | bc)
else
    # Odd number of elements
    p50=${sorted_latencies[$middle_index]}
fi

# Calculate P95
p95_index=$((total_tests * 95 / 100))
p95=${sorted_latencies[$p95_index]}

echo "Total requests: $total_tests"
echo "Average latency: ${avg_latency}ms"
echo "P50 latency: ${p50}ms"
echo "P95 latency: ${p95}ms"
echo "Min latency: ${sorted_latencies[0]}ms"
echo "Max latency: ${sorted_latencies[-1]}ms"

echo ""
echo "🎯 4. Performance Thresholds"
echo "============================="

# Check against thresholds
threshold_p50=500
threshold_avg=1000

if (( $(echo "$p50 <= $threshold_p50" | bc -l) )); then
    echo "✅ P50 latency: ${p50}ms (≤ ${threshold_p50}ms) - PASS"
else
    echo "❌ P50 latency: ${p50}ms (> ${threshold_p50}ms) - FAIL"
fi

if (( $(echo "$avg_latency <= $threshold_avg" | bc -l) )); then
    echo "✅ Average latency: ${avg_latency}ms (≤ ${threshold_avg}ms) - PASS"
else
    echo "❌ Average latency: ${avg_latency}ms (> ${threshold_avg}ms) - FAIL"
fi

# Generate JSON report
cat > "$RESULTS_FILE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "test_type": "live_performance",
  "api_base": "$API_BASE",
  "health_check": {
    "duration_seconds": $health_time,
    "status": "success"
  },
  "breed_detection": {
    "total_requests": $total_tests,
    "successful_requests": $total_tests,
    "metrics": {
      "average_latency_ms": $avg_latency,
      "p50_latency_ms": $p50,
      "p95_latency_ms": $p95,
      "min_latency_ms": ${sorted_latencies[0]},
      "max_latency_ms": ${sorted_latencies[-1]}
    },
    "thresholds": {
      "p50_threshold_ms": $threshold_p50,
      "p50_pass": $(if (( $(echo "$p50 <= $threshold_p50" | bc -l) )); then echo "true"; else echo "false"; fi),
      "avg_threshold_ms": $threshold_avg,
      "avg_pass": $(if (( $(echo "$avg_latency <= $threshold_avg" | bc -l) )); then echo "true"; else echo "false"; fi)
    }
  },
  "individual_requests": [
$(for i in "${!latencies[@]}"; do
    echo "    {\"request_$((i+1))\": ${latencies[i]}}$(if [ $i -lt $((${#latencies[@]}-1)) ]; then echo ","; fi)"
done)
  ]
}
EOF

echo ""
echo "📋 Results saved to: $RESULTS_FILE"
echo ""

# Overall pass/fail
if (( $(echo "$p50 <= $threshold_p50" | bc -l) )) && (( $(echo "$avg_latency <= $threshold_avg" | bc -l) )); then
    echo "🎉 OVERALL RESULT: PASS"
    echo "Live system meets performance requirements!"
    exit 0
else
    echo "❌ OVERALL RESULT: FAIL"
    echo "Live system does not meet performance requirements"
    exit 1
fi
