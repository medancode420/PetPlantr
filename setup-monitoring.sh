#!/usr/bin/env bash
# setup-monitoring.sh - Setup monitoring stack for PetPlantr production

set -euo pipefail

# Configuration
PROJECT_NAME="petplantr"
MONITORING_DIR="monitoring"
PROMETHEUS_VERSION="2.45.0"
GRAFANA_VERSION="10.1.0"
NODE_EXPORTER_VERSION="1.6.1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }

# Create monitoring directory structure
create_monitoring_dirs() {
    log_info "Creating monitoring directory structure..."

    mkdir -p "$MONITORING_DIR"/{prometheus,grafana,node-exporter,alertmanager}
    mkdir -p "$MONITORING_DIR"/prometheus/{data,rules}
    mkdir -p "$MONITORING_DIR"/grafana/{data,logs,plugins}
    mkdir -p "$MONITORING_DIR"/alertmanager/{data,config}

    log_success "Monitoring directories created"
}

# Create Prometheus configuration
create_prometheus_config() {
    log_info "Creating Prometheus configuration..."

    cat > "$MONITORING_DIR/prometheus/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'petplantr-api'
    static_configs:
      - targets: ['petplantr:8000']
    metrics_path: '/api/v1/metrics'
    scrape_interval: 10s

  - job_name: 'petplantr-health'
    static_configs:
      - targets: ['petplantr:8000']
    metrics_path: '/api/v1/health'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
EOF

    log_success "Prometheus configuration created"
}

# Create Prometheus rules
create_prometheus_rules() {
    log_info "Creating Prometheus alerting rules..."

    cat > "$MONITORING_DIR/prometheus/rules/petplantr.yml" << EOF
groups:
  - name: petplantr
    rules:
    - alert: PetPlantrDown
      expr: up{job="petplantr-api"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "PetPlantr API is down"
        description: "PetPlantr API has been down for more than 5 minutes."

    - alert: HighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="petplantr-api"}[5m])) > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is above 2 seconds for 5 minutes."

    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5..", job="petplantr-api"}[5m]) / rate(http_requests_total{job="petplantr-api"}[5m]) > 0.05
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected"
        description: "Error rate is above 5% for 5 minutes."

    - alert: LowDiskSpace
      expr: (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Low disk space"
        description: "Disk usage is above 85%."

    - alert: HighMemoryUsage
      expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 90
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage"
        description: "Memory usage is above 90%."
EOF

    log_success "Prometheus rules created"
}

# Create Alertmanager configuration
create_alertmanager_config() {
    log_info "Creating Alertmanager configuration..."

    cat > "$MONITORING_DIR/alertmanager/alertmanager.yml" << EOF
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourdomain.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email-notifications'
  routes:
  - match:
      severity: critical
    receiver: 'critical-notifications'

receivers:
- name: 'email-notifications'
  email_configs:
  - to: 'admin@yourdomain.com'
    send_resolved: true

- name: 'critical-notifications'
  email_configs:
  - to: 'admin@yourdomain.com'
    send_resolved: true
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts'
    send_resolved: true
EOF

    log_success "Alertmanager configuration created"
}

# Create Grafana configuration
create_grafana_config() {
    log_info "Creating Grafana configuration..."

    cat > "$MONITORING_DIR/grafana/grafana.ini" << EOF
[server]
http_port = 3000
domain = localhost

[security]
admin_user = admin
admin_password = petplantr_admin_2024

[users]
allow_sign_up = false

[auth.anonymous]
enabled = false

[log]
mode = console
level = info

[metrics]
enabled = true
EOF

    log_success "Grafana configuration created"
}

# Create docker-compose for monitoring
create_monitoring_compose() {
    log_info "Creating monitoring docker-compose file..."

    cat > "docker-compose.monitoring.yml" << EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v${PROMETHEUS_VERSION}
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus/rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:${GRAFANA_VERSION}
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana/grafana.ini:/etc/grafana/grafana.ini:ro
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=petplantr_admin_2024
    depends_on:
      - prometheus
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:v${NODE_EXPORTER_VERSION}
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:v0.25.0
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
EOF

    log_success "Monitoring docker-compose created"
}

# Setup Grafana dashboards
setup_grafana_dashboards() {
    log_info "Setting up Grafana dashboards..."

    mkdir -p "$MONITORING_DIR/grafana/dashboards"
    mkdir -p "$MONITORING_DIR/grafana/provisioning/dashboards"
    mkdir -p "$MONITORING_DIR/grafana/provisioning/datasources"

    # Create datasource configuration
    cat > "$MONITORING_DIR/grafana/provisioning/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Create dashboard provisioning
    cat > "$MONITORING_DIR/grafana/provisioning/dashboards/dashboard.yml" << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Grafana provisioning setup complete"
}

# Main setup function
main() {
    log_info "Setting up PetPlantr monitoring stack..."

    create_monitoring_dirs
    create_prometheus_config
    create_prometheus_rules
    create_alertmanager_config
    create_grafana_config
    create_monitoring_compose
    setup_grafana_dashboards

    log_success "🎉 Monitoring setup complete!"
    log_info ""
    log_info "📋 Next steps:"
    log_info "1. Update email and Slack configurations in alertmanager.yml"
    log_info "2. Run: docker compose -f docker-compose.monitoring.yml up -d"
    log_info "3. Access Grafana at http://localhost:3000 (admin/petplantr_admin_2024)"
    log_info "4. Access Prometheus at http://localhost:9090"
    log_info "5. Import dashboards from grafana/dashboards/"
}

# Run main setup
main
