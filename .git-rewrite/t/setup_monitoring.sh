#!/bin/bash

# Production Monitoring Setup for PetPlantr Breed Detection
# Implements Prometheus, Grafana, W&B, and Sentry monitoring

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BOLD}${BLUE}$1${NC}"; }

echo "📊 PetPlantr Production Monitoring Setup"
echo "==========================================="

# Check requirements
check_requirements() {
    log_step "🔍 Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    log_success "Requirements check passed"
}

# Setup Prometheus monitoring
setup_prometheus() {
    log_step "📈 Setting up Prometheus monitoring..."
    
    mkdir -p monitoring/prometheus
    
    cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

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
    scrape_timeout: 3s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
EOF

    # Alert rules
    cat > monitoring/prometheus/alert_rules.yml << 'EOF'
groups:
  - name: petplantr.rules
    rules:
      - alert: HighInferenceLatency
        expr: histogram_quantile(0.95, rate(inference_latency_seconds_bucket[5m])) > 0.7
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High inference latency detected"
          description: "P95 inference latency is {{ $value }}s"

      - alert: LowConfidenceRate
        expr: rate(confidence_score_bucket{le="0.8"}[5m]) / rate(confidence_score_count[5m]) > 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High rate of low-confidence predictions"
          description: "{{ $value | humanizePercentage }} of predictions have confidence < 80%"

      - alert: HighErrorRate
        expr: rate(breed_detection_requests_total{status="error"}[5m]) / rate(breed_detection_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in breed detection"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighMemoryUsage
        expr: inference_memory_mb > 4096
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage during inference"
          description: "Memory usage is {{ $value }}MB"

      - alert: ServiceDown
        expr: up{job="petplantr-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PetPlantr API is down"
          description: "The PetPlantr API service is not responding"
EOF

    log_success "Prometheus configuration created"
}

# Setup Grafana dashboards
setup_grafana() {
    log_step "📊 Setting up Grafana dashboards..."
    
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/provisioning/dashboards
    mkdir -p monitoring/grafana/provisioning/datasources
    
    # Datasource configuration
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Dashboard provisioning
    cat > monitoring/grafana/provisioning/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'petplantr'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    # Breed Detection Dashboard
    cat > monitoring/grafana/dashboards/breed-detection.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "PetPlantr Breed Detection",
    "tags": ["petplantr", "breed-detection"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Inference Latency (P95)",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(inference_latency_seconds_bucket[5m]))",
            "format": "time_series",
            "legendFormat": "P95 Latency"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.5},
                {"color": "red", "value": 1.0}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(breed_detection_requests_total[5m])",
            "format": "time_series",
            "legendFormat": "Requests/sec"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "Confidence Distribution",
        "type": "histogram",
        "targets": [
          {
            "expr": "rate(confidence_score_bucket[5m])",
            "format": "heatmap",
            "legendFormat": "{{le}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(breed_detection_requests_total{status=\"error\"}[5m]) / rate(breed_detection_requests_total[5m]) * 100",
            "format": "time_series",
            "legendFormat": "Error Rate %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 5}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8}
      },
      {
        "id": 5,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "inference_memory_mb",
            "format": "time_series",
            "legendFormat": "Memory MB"
          }
        ],
        "yAxes": [
          {
            "unit": "bytes",
            "label": "Memory Usage"
          }
        ],
        "gridPos": {"h": 8, "w": 18, "x": 6, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "10s"
  }
}
EOF

    log_success "Grafana configuration created"
}

# Setup Docker Compose for monitoring stack
setup_docker_compose() {
    log_step "🐳 Setting up monitoring Docker Compose..."
    
    cat > monitoring/docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=petplantr2024
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - monitoring

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager:/etc/alertmanager
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
EOF

    log_success "Docker Compose monitoring stack created"
}

# Setup FastAPI Prometheus integration
setup_fastapi_prometheus() {
    log_step "🚀 Setting up FastAPI Prometheus integration..."
    
    cat >> requirements.txt << 'EOF'

# Production monitoring
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
pynvml==11.5.0
EOF

    # Add to api_server.py
    log_info "Adding Prometheus endpoint to FastAPI..."
    log_info "Add this to your api_server.py:"
    
    cat << 'EOF'

# Add to api_server.py imports:
from prometheus_fastapi_instrumentator import Instrumentator

# Add after app creation:
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# The /metrics endpoint will be automatically available
EOF

    log_success "FastAPI Prometheus integration instructions provided"
}

# Setup Weights & Biases integration
setup_wandb() {
    log_step "🏃 Setting up Weights & Biases integration..."
    
    cat > monitoring/wandb_config.py << 'EOF'
"""
Weights & Biases configuration for production monitoring
"""

import wandb
import os
from typing import Dict, Any

class WandBMonitor:
    def __init__(self, project_name: str = "petplantr-production"):
        self.project_name = project_name
        self.run = None
        
    def init_monitoring(self, config: Dict[str, Any] = None):
        """Initialize W&B monitoring for production"""
        self.run = wandb.init(
            project=self.project_name,
            job_type="production-monitoring",
            config=config or {},
            tags=["production", "breed-detection"]
        )
        
    def log_inference_metrics(self, metrics: Dict[str, Any]):
        """Log inference metrics to W&B"""
        if self.run:
            wandb.log({
                "inference/latency": metrics.get("latency", 0),
                "inference/confidence": metrics.get("confidence", 0),
                "inference/memory_mb": metrics.get("memory_mb", 0),
                "inference/gpu_utilization": metrics.get("gpu_util", 0),
                "inference/requests_per_minute": metrics.get("rpm", 0)
            })
    
    def log_model_drift(self, drift_metrics: Dict[str, Any]):
        """Log model drift detection metrics"""
        if self.run:
            wandb.log({
                "drift/accuracy_drop": drift_metrics.get("accuracy_drop", 0),
                "drift/confidence_shift": drift_metrics.get("confidence_shift", 0),
                "drift/breed_distribution_change": drift_metrics.get("distribution_change", 0)
            })
    
    def alert_on_threshold(self, metric_name: str, value: float, threshold: float):
        """Create alert if metric exceeds threshold"""
        if value > threshold:
            wandb.alert(
                title=f"Threshold Exceeded: {metric_name}",
                text=f"Metric {metric_name} = {value} exceeded threshold {threshold}",
                level=wandb.AlertLevel.WARN
            )

# Global monitor instance
monitor = WandBMonitor()
EOF

    log_success "W&B monitoring configuration created"
}

# Setup alerting
setup_alerting() {
    log_step "🚨 Setting up alerting..."
    
    mkdir -p monitoring/alertmanager
    
    cat > monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@petplantr.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/alerts'
    send_resolved: true

- name: 'slack'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#petplantr-alerts'
    title: 'PetPlantr Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

    log_success "Alerting configuration created"
}

# Main setup function
main() {
    case "${1:-all}" in
        "requirements")
            check_requirements
            ;;
        "prometheus")
            setup_prometheus
            ;;
        "grafana")
            setup_grafana
            ;;
        "docker")
            setup_docker_compose
            ;;
        "fastapi")
            setup_fastapi_prometheus
            ;;
        "wandb")
            setup_wandb
            ;;
        "alerts")
            setup_alerting
            ;;
        "start")
            log_info "Starting monitoring stack..."
            cd monitoring
            docker-compose -f docker-compose.monitoring.yml up -d
            log_success "Monitoring stack started!"
            log_info "Grafana: http://localhost:3001 (admin/petplantr2024)"
            log_info "Prometheus: http://localhost:9090"
            ;;
        "stop")
            log_info "Stopping monitoring stack..."
            cd monitoring
            docker-compose -f docker-compose.monitoring.yml down
            ;;
        "all")
            check_requirements
            setup_prometheus
            setup_grafana
            setup_docker_compose
            setup_fastapi_prometheus
            setup_wandb
            setup_alerting
            
            log_success "🎉 Monitoring setup complete!"
            echo ""
            log_info "Next steps:"
            log_info "1. Set SLACK_WEBHOOK_URL in alertmanager.yml"
            log_info "2. Add Prometheus instrumentation to API server"
            log_info "3. Start monitoring: ./setup_monitoring.sh start"
            log_info "4. Configure W&B API key: export WANDB_API_KEY=<your-key>"
            ;;
        *)
            echo "Usage: $0 [requirements|prometheus|grafana|docker|fastapi|wandb|alerts|start|stop|all]"
            exit 1
            ;;
    esac
}

main "$@"
