#!/bin/bash
# Comprehensive health monitoring for PetPlantr

API_URL="http://localhost:8000"
HEALTH_ENDPOINT="$API_URL/api/v1/health"
SYNTHETIC_ENDPOINT="$API_URL/api/v1/ops/synthetic/live"

echo "🔍 PetPlantr Health Check - $(date)"
echo "================================="

# API Health Check
echo -n "API Health: "
if curl -f -s "$HEALTH_ENDPOINT" >/dev/null 2>&1; then
    response=$(curl -s "$HEALTH_ENDPOINT")
    status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")
    if [[ "$status" == "healthy" ]]; then
        echo "✅ HEALTHY"
    else
        echo "⚠️ RESPONDING (status: $status)"
    fi
else
    echo "❌ DOWN"
fi

# Synthetic Monitor Check
echo -n "Synthetic Monitor: "
if curl -f -s "$SYNTHETIC_ENDPOINT" >/dev/null 2>&1; then
    echo "✅ ACTIVE"
else
    echo "⚠️ INACTIVE"
fi

# Response Time Check
echo -n "Response Time: "
start_time=$(date +%s%N)
if curl -f -s "$HEALTH_ENDPOINT" >/dev/null 2>&1; then
    end_time=$(date +%s%N)
    response_time=$(( (end_time - start_time) / 1000000 ))
    if [[ $response_time -lt 5000 ]]; then
        echo "✅ ${response_time}ms (< 5s SLA)"
    else
        echo "⚠️ ${response_time}ms (> 5s SLA)"
    fi
else
    echo "❌ N/A"
fi

# SSL Certificate Check
echo -n "SSL Certificate: "
if [[ -f "./security/ssl/certs/selfsigned.crt" ]]; then
    expiry=$(openssl x509 -in ./security/ssl/certs/selfsigned.crt -enddate -noout | cut -d= -f2)
    expiry_epoch=$(date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry" +%s 2>/dev/null || date -d "$expiry" +%s)
    now_epoch=$(date +%s)
    days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
    if [[ $days_left -gt 30 ]]; then
        echo "✅ Valid (${days_left} days left)"
    else
        echo "⚠️ Expires soon (${days_left} days left)"
    fi
else
    echo "❌ Not configured"
fi

# Docker Monitoring Check
echo -n "Docker Monitoring: "
if docker ps | grep -q petplantr; then
    echo "✅ ACTIVE"
else
    echo "⚠️ NOT RUNNING"
fi

echo ""
echo "📊 System Resources:"
echo -n "Memory Usage: "
memory_usage=$(ps aux | grep python | grep -v grep | awk '{print $4}' | head -1)
if [[ -n "$memory_usage" ]]; then
    echo "${memory_usage}%"
else
    echo "N/A"
fi

echo -n "CPU Usage: "
cpu_usage=$(ps aux | grep python | grep -v grep | awk '{print $3}' | head -1)
if [[ -n "$cpu_usage" ]]; then
    echo "${cpu_usage}%"
else
    echo "N/A"
fi

echo ""
echo "🔗 Service URLs:"
echo "API: $API_URL"
echo "Health: $HEALTH_ENDPOINT"
echo "Synthetic Monitor: $SYNTHETIC_ENDPOINT"
if [[ -f "./enable-monitoring.sh" ]]; then
    echo "Grafana: http://localhost:3000 (admin/admin)"
    echo "Prometheus: http://localhost:9090"
fi
