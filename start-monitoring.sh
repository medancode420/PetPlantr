#!/bin/bash
# Start PetPlantr monitoring stack

echo "📊 Starting PetPlantr Monitoring Stack..."

# Start monitoring services
docker compose -f monitoring/docker-compose.monitoring.yml up -d

# Wait for services to start
echo "⏳ Waiting for monitoring services to start..."
sleep 30

# Check service health
echo "🔍 Checking monitoring services..."

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is running on http://localhost:9090"
else
    echo "❌ Prometheus is not responding"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is running on http://localhost:3000 (admin/admin)"
else
    echo "❌ Grafana is not responding"
fi

# Check Alertmanager
if curl -f http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "✅ Alertmanager is running on http://localhost:9093"
else
    echo "❌ Alertmanager is not responding"
fi

# Check Node Exporter
if curl -f http://localhost:9100/metrics > /dev/null 2>&1; then
    echo "✅ Node Exporter is running on http://localhost:9100"
else
    echo "❌ Node Exporter is not responding"
fi

# Check cAdvisor
if curl -f http://localhost:8080/containers/ > /dev/null 2>&1; then
    echo "✅ cAdvisor is running on http://localhost:8080"
else
    echo "❌ cAdvisor is not responding"
fi

echo ""
echo "🎯 Monitoring Stack URLs:"
echo "  📊 Grafana Dashboard: http://localhost:3000 (admin/admin)"
echo "  📈 Prometheus: http://localhost:9090"
echo "  🚨 Alertmanager: http://localhost:9093"
echo "  📋 cAdvisor: http://localhost:8080"
echo ""
echo "📊 Streamlit Dashboard: streamlit run monitoring-dashboard.py"
echo ""
echo "✅ Monitoring stack startup complete!"
