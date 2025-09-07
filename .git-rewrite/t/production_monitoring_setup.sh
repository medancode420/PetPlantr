#!/bin/bash

# PetPlantr Production Monitoring Setup
# Configures Prometheus, Grafana, and alerting for production deployment

set -e

MONITORING_DIR="monitoring"
GRAFANA_CONFIG_DIR="$MONITORING_DIR/grafana"
PROMETHEUS_CONFIG_DIR="$MONITORING_DIR/prometheus"
ALERTMANAGER_CONFIG_DIR="$MONITORING_DIR/alertmanager"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

echo "========================================"
echo "   PetPlantr Monitoring Setup"
echo "========================================"

# Create monitoring directory structure
log_info "Creating monitoring directory structure..."
mkdir -p "$GRAFANA_CONFIG_DIR/dashboards" "$GRAFANA_CONFIG_DIR/provisioning/dashboards" "$GRAFANA_CONFIG_DIR/provisioning/datasources"
mkdir -p "$PROMETHEUS_CONFIG_DIR" "$ALERTMANAGER_CONFIG_DIR"

# Prometheus configuration
log_info "Creating Prometheus configuration..."
cat > "$PROMETHEUS_CONFIG_DIR/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'petplantr-api'
    static_configs:
      - targets: ['petplantr-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
      
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
      
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
EOF

# Prometheus alerting rules
log_info "Creating Prometheus alerting rules..."
cat > "$PROMETHEUS_CONFIG_DIR/alerts.yml" << 'EOF'
groups:
  - name: petplantr-api
    rules:
      # High latency alert
      - alert: HighInferenceLatency
        expr: histogram_quantile(0.95, inference_latency_seconds_bucket) > 0.6
        for: 2m
        labels:
          severity: warning
          service: petplantr-api
        annotations:
          summary: "High inference latency detected"
          description: "P95 inference latency is {{ $value }}s, above 0.6s threshold"
          
      # High error rate alert  
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 1m
        labels:
          severity: critical
          service: petplantr-api
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}, above 5% threshold"
          
      # Low accuracy alert
      - alert: LowAccuracy
        expr: model_accuracy_percent < 85
        for: 5m
        labels:
          severity: warning
          service: petplantr-api
        annotations:
          summary: "Model accuracy below threshold"
          description: "Model accuracy is {{ $value }}%, below 85% threshold"
          
      # High memory usage alert
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name="petplantr-api"} / container_spec_memory_limit_bytes{name="petplantr-api"} > 0.8
        for: 3m
        labels:
          severity: warning
          service: petplantr-api
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }} of limit"
          
      # API down alert
      - alert: APIDown
        expr: up{job="petplantr-api"} == 0
        for: 1m
        labels:
          severity: critical
          service: petplantr-api
        annotations:
          summary: "PetPlantr API is down"
          description: "PetPlantr API has been down for more than 1 minute"
          
      # Model drift alert
      - alert: ModelDrift
        expr: increase(drift_detected_total[1h]) > 0
        for: 0m
        labels:
          severity: warning
          service: petplantr-api
        annotations:
          summary: "Model drift detected"
          description: "Data drift has been detected in the model"
          
      # High GPU VRAM usage alert
      - alert: HighGPUVRAMUsage
        expr: gpu_vram_mb > 5120
        for: 2m
        labels:
          severity: critical
          service: petplantr-api
        annotations:
          summary: "High GPU VRAM usage detected"
          description: "GPU VRAM usage is {{ $value }}MB, above 5120MB (5GB) threshold"
          
  - name: infrastructure
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"
          
      # High disk usage
      - alert: HighDiskUsage
        expr: (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value }}% on {{ $labels.instance }}"
EOF

# Docker Compose for monitoring stack
log_info "Creating Docker Compose for monitoring stack..."
cat > "$MONITORING_DIR/docker-compose.monitoring.yml" << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    restart: unless-stopped
    
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:

networks:
  default:
    name: petplantr-monitoring
EOF

log_success "Monitoring setup complete!"
echo ""
echo "📁 Created monitoring configuration in: $MONITORING_DIR/"
echo ""
echo "Configuration includes:"
echo "  ✅ Prometheus with alerting rules"
echo "  ✅ Grafana with configuration"
echo "  ✅ Docker Compose for easy deployment"
