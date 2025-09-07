#!/bin/bash
# PetPlantr Deployment Dashboard

clear
echo "🚀 PetPlantr Production Deployment Dashboard"
echo "==========================================="
echo "Date: $(date)"
echo ""

# System Status
echo "🖥️  System Status:"
echo -n "  API Server: "
if curl -f -s "http://localhost:8000/api/v1/health" >/dev/null 2>&1; then
    echo "🟢 RUNNING"
else
    echo "🔴 DOWN"
fi

echo -n "  SSL/TLS: "
if [[ -f "./security/ssl/certs/petplantr.crt" ]]; then
    echo "🟢 CONFIGURED"
else
    echo "🟡 NOT CONFIGURED"
fi

echo -n "  Monitoring: "
if docker ps | grep -q petplantr.*prometheus; then
    echo "🟢 ACTIVE"
else
    echo "🟡 LIMITED"
fi

echo ""

# Performance Metrics
echo "📊 Performance Metrics:"
response_time=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:8000/api/v1/health" 2>/dev/null || echo "N/A")
if [[ "$response_time" != "N/A" ]]; then
    response_ms=$(echo "$response_time * 1000" | bc 2>/dev/null | xargs printf "%.0f")
    echo "  Response Time: ${response_ms}ms"
else
    echo "  Response Time: N/A"
fi

memory_usage=$(ps aux | grep python | grep -v grep | awk '{print $4}' | head -1)
if [[ -n "$memory_usage" ]]; then
    echo "  Memory Usage: ${memory_usage}%"
else
    echo "  Memory Usage: N/A"
fi

echo ""

# Service URLs
echo "🔗 Service URLs:"
echo "  API: http://localhost:8000"
echo "  Health: http://localhost:8000/api/v1/health"
echo "  Synthetic Monitor: http://localhost:8000/api/v1/ops/synthetic/live"
if [[ -f "./enable-monitoring.sh" ]]; then
    echo "  Grafana: http://localhost:3000"
    echo "  Prometheus: http://localhost:9090"
fi

echo ""

# Recent Backups
echo "💾 Recent Backups:"
if [[ -d "./backups/daily" ]]; then
    recent_backup=$(ls -t ./backups/daily/*.tar.gz 2>/dev/null | head -1)
    if [[ -n "$recent_backup" ]]; then
        backup_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$recent_backup")
        echo "  Latest: $backup_date"
    else
        echo "  Latest: None"
    fi
else
    echo "  Latest: None"
fi

echo ""

# Quick Actions
echo "⚡ Quick Actions:"
echo "  1. Run health check: ./health-monitor.sh"
echo "  2. Create backup: ./backup.sh"
echo "  3. View logs: tail -f logs/petplantr.log"
echo "  4. Restart services: docker compose restart"
echo "  5. Update SSL: ./setup-ssl.sh --force"
echo ""

# Canary Status
echo "🚦 Canary Deployment Status:"
canary_config="./nginx/local-canary.conf"
if [[ -f "$canary_config" ]]; then
    canary_percent=$(grep -o "[0-9]*%" "$canary_config" | head -1)
    if [[ -n "$canary_percent" ]]; then
        echo "  Traffic Split: $canary_percent canary"
    else
        echo "  Traffic Split: Not configured"
    fi
else
    echo "  Traffic Split: Not configured"
fi

echo ""
echo "Press Ctrl+C to exit, runs every 30 seconds..."
