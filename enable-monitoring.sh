#!/usr/bin/env bash
# enable-monitoring.sh - Enable Docker monitoring stack for PetPlantr
# Sets up Prometheus, Grafana, and monitoring dashboards

set -euo pipefail

# Configuration
MONITORING_DIR="${MONITORING_DIR:-./monitoring}"
PROMETHEUS_PORT="${PROMETHEUS_PORT:-9090}"
GRAFANA_PORT="${GRAFANA_PORT:-3000}"
FORCE="${FORCE:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }

# Check Docker availability
check_docker() {
    log_info "Checking Docker availability..."

    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed or not in PATH"
        log_error "Please install Docker Desktop or Docker Engine"
        return 1
    fi

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        log_error "Please start Docker Desktop or Docker daemon"
        return 1
    fi

    log_success "Docker is available"
    return 0
}

# Check Docker Compose availability
check_docker_compose() {
    log_info "Checking Docker Compose availability..."

    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not available"
        log_error "Please install Docker Compose v2 or use Docker Desktop"
        exit 1
    fi

    log_success "Docker Compose is available"
}

# Create monitoring directories
create_monitoring_dirs() {
    log_info "Creating monitoring directories..."

    mkdir -p "$MONITORING_DIR/prometheus"
    mkdir -p "$MONITORING_DIR/grafana/provisioning/datasources"
    mkdir -p "$MONITORING_DIR/grafana/provisioning/dashboards"
    mkdir -p "$MONITORING_DIR/grafana/dashboards"
    mkdir -p "$MONITORING_DIR/alertmanager"

    log_success "Monitoring directories created"
}

# Generate Prometheus configuration
generate_prometheus_config() {
    log_info "Generating Prometheus configuration..."

    local prometheus_config="$MONITORING_DIR/prometheus/prometheus.yml"

    cat > "$prometheus_config" << EOF
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
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  - job_name: 'petplantr-health'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/api/v1/health'
    scrape_interval: 30s
    params:
      format: ['prometheus']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:8080']
    scrape_interval: 15s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s
    metrics_path: '/metrics'
EOF

    log_success "Prometheus configuration generated: $prometheus_config"
}

# Generate Prometheus alert rules
generate_alert_rules() {
    log_info "Generating Prometheus alert rules..."

    local alert_rules="$MONITORING_DIR/prometheus/alert_rules.yml"

    cat > "$alert_rules" << EOF
groups:
  - name: petplantr
    rules:
    - alert: PetPlantrApiDown
      expr: up{job="petplantr-api"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "PetPlantr API is down"
        description: "PetPlantr API has been down for more than 1 minute."

    - alert: PetPlantrHighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="petplantr-api"}[5m])) > 5
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "PetPlantr API high response time"
        description: "95th percentile response time is above 5 seconds for 2 minutes."

    - alert: PetPlantrHighErrorRate
      expr: rate(http_requests_total{status=~"5..", job="petplantr-api"}[5m]) / rate(http_requests_total{job="petplantr-api"}[5m]) > 0.05
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "PetPlantr API high error rate"
        description: "Error rate is above 5% for 2 minutes."

    - alert: PetPlantrLowConfidence
      expr: petplantr_breed_confidence < 0.7
      for: 5m
      labels:
        severity: info
      annotations:
        summary: "PetPlantr low breed detection confidence"
        description: "Breed detection confidence is below 70% for 5 minutes."

    - alert: PetPlantrMemoryUsage
      expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage"
        description: "Memory usage is above 85% for 5 minutes."

    - alert: PetPlantrDiskUsage
      expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 90
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High disk usage"
        description: "Disk usage is above 90% for 5 minutes."
EOF

    log_success "Alert rules generated: $alert_rules"
}

# Generate Alertmanager configuration
generate_alertmanager_config() {
    log_info "Generating Alertmanager configuration..."

    local alertmanager_config="$MONITORING_DIR/alertmanager/alertmanager.yml"

    cat > "$alertmanager_config" << EOF
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@petplantr.com'
  smtp_auth_username: 'alerts@petplantr.com'
  smtp_auth_password: 'your-smtp-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email'
  routes:
  - match:
      severity: critical
    receiver: 'email'

receivers:
- name: 'email'
  email_configs:
  - to: 'admin@petplantr.com'
    send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
EOF

    log_success "Alertmanager configuration generated: $alertmanager_config"
}

# Generate Grafana datasource configuration
generate_grafana_datasource() {
    log_info "Generating Grafana datasource configuration..."

    local datasource_config="$MONITORING_DIR/grafana/provisioning/datasources/prometheus.yml"

    cat > "$datasource_config" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    log_success "Grafana datasource configuration generated: $datasource_config"
}

# Generate Grafana dashboard configuration
generate_grafana_dashboard_config() {
    log_info "Generating Grafana dashboard configuration..."

    local dashboard_config="$MONITORING_DIR/grafana/provisioning/dashboards/dashboards.yml"

    cat > "$dashboard_config" << EOF
apiVersion: 1

providers:
  - name: 'PetPlantr'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Grafana dashboard configuration generated: $dashboard_config"
}

# Generate PetPlantr dashboard
generate_petplantr_dashboard() {
    log_info "Generating PetPlantr monitoring dashboard..."

    local dashboard_file="$MONITORING_DIR/grafana/dashboards/petplantr-dashboard.json"

    cat > "$dashboard_file" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "PetPlantr Production Monitoring",
    "tags": ["petplantr", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"petplantr-api\"}[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job=\"petplantr-api\"}[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "unit": "seconds"
          }
        ]
      },
      {
        "id": 2,
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"petplantr-api\"}[5m])",
            "legendFormat": "Requests per second"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\", job=\"petplantr-api\"}[5m]) / rate(http_requests_total{job=\"petplantr-api\"}[5m]) * 100",
            "legendFormat": "Error rate %"
          }
        ],
        "yAxes": [
          {
            "unit": "percent"
          }
        ]
      },
      {
        "id": 4,
        "title": "Breed Detection Confidence",
        "type": "graph",
        "targets": [
          {
            "expr": "petplantr_breed_confidence",
            "legendFormat": "Confidence score"
          }
        ],
        "yAxes": [
          {
            "max": 1,
            "min": 0
          }
        ]
      },
      {
        "id": 5,
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
            "legendFormat": "Memory usage %"
          },
          {
            "expr": "(node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100",
            "legendFormat": "Disk usage %"
          }
        ],
        "yAxes": [
          {
            "unit": "percent"
          }
        ]
      },
      {
        "id": 6,
        "title": "Active Alerts",
        "type": "table",
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\"}",
            "legendFormat": "{{alertname}}"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "timepicker": {},
    "templating": {
      "list": []
    },
    "annotations": {
      "list": []
    },
    "refresh": "30s",
    "schemaVersion": 16,
    "version": 0,
    "links": []
  }
}
EOF

    log_success "PetPlantr dashboard generated: $dashboard_file"
}

# Generate Docker Compose for monitoring stack
generate_docker_compose() {
    log_info "Generating Docker Compose configuration for monitoring stack..."

    local docker_compose_file="$MONITORING_DIR/docker-compose.monitoring.yml"

    cat > "$docker_compose_file" << EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: petplantr-prometheus
    ports:
      - "$PROMETHEUS_PORT:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: petplantr-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - monitoring
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: petplantr-grafana
    ports:
      - "$GRAFANA_PORT:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - grafana_data:/var/lib/grafana
    networks:
      - monitoring
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: petplantr-node-exporter
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
    networks:
      - monitoring
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: petplantr-cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    devices:
      - /dev/kmsg
    networks:
      - monitoring
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
EOF

    log_success "Docker Compose configuration generated: $docker_compose_file"
}

# Update main docker-compose.yml to include monitoring
update_main_docker_compose() {
    log_info "Updating main Docker Compose configuration..."

    local main_compose="./docker-compose.yml"

    if [[ ! -f "$main_compose" ]]; then
        log_warn "Main docker-compose.yml not found, skipping update"
        return 0
    fi

    # Add monitoring network to main compose
    if ! grep -q "monitoring" "$main_compose"; then
        sed -i.bak '/networks:/a\
  monitoring:\
    external: true' "$main_compose"
    fi

    # Add monitoring network to petplantr service
    if grep -q "petplantr:" "$main_compose"; then
        sed -i.bak '/petplantr:/,/^[[:space:]]*[^[:space:]]/ {
            /networks:/a\
      - monitoring
        }' "$main_compose"
    fi

    log_success "Main Docker Compose updated to include monitoring network"
}

# Start monitoring stack
start_monitoring() {
    log_info "Starting monitoring stack..."

    cd "$MONITORING_DIR"

    if docker compose version >/dev/null 2>&1; then
        docker compose -f docker-compose.monitoring.yml up -d
    else
        docker-compose -f docker-compose.monitoring.yml up -d
    fi

    cd - >/dev/null

    log_success "Monitoring stack started"
}

# Test monitoring setup
test_monitoring() {
    log_info "Testing monitoring setup..."

    # Wait for services to start
    sleep 10

    # Test Prometheus
    if curl -f "http://localhost:$PROMETHEUS_PORT/-/healthy" >/dev/null 2>&1; then
        log_success "Prometheus is healthy"
    else
        log_error "Prometheus health check failed"
        return 1
    fi

    # Test Grafana
    if curl -f "http://localhost:$GRAFANA_PORT/api/health" >/dev/null 2>&1; then
        log_success "Grafana is healthy"
    else
        log_error "Grafana health check failed"
        return 1
    fi

    # Test Node Exporter
    if curl -f "http://localhost:9100/metrics" >/dev/null 2>&1; then
        log_success "Node Exporter is healthy"
    else
        log_error "Node Exporter health check failed"
        return 1
    fi

    log_success "All monitoring services are healthy"
}

# Generate monitoring documentation
generate_documentation() {
    log_info "Generating monitoring documentation..."

    local docs_file="$MONITORING_DIR/README.md"

    cat > "$docs_file" << EOF
# PetPlantr Monitoring Stack

This directory contains the monitoring stack configuration for PetPlantr production deployment.

## Services

- **Prometheus** (Port $PROMETHEUS_PORT): Metrics collection and alerting
- **Grafana** (Port $GRAFANA_PORT): Dashboards and visualization
- **Alertmanager** (Port 9093): Alert management and notifications
- **Node Exporter** (Port 9100): System metrics collection
- **cAdvisor** (Port 8080): Container metrics collection

## Access URLs

- Prometheus: http://localhost:$PROMETHEUS_PORT
- Grafana: http://localhost:$GRAFANA_PORT (admin/admin)
- Alertmanager: http://localhost:9093

## Dashboards

The PetPlantr dashboard includes:
- API Response Time (95th and 50th percentiles)
- API Request Rate
- Error Rate
- Breed Detection Confidence
- System Resources (Memory/Disk usage)
- Active Alerts

## Alerting

Configured alerts:
- API Down
- High Response Time (>5s)
- High Error Rate (>5%)
- Low Confidence (<70%)
- High Memory Usage (>85%)
- High Disk Usage (>90%)

## Configuration Files

- \`prometheus/prometheus.yml\`: Prometheus configuration
- \`prometheus/alert_rules.yml\`: Alert rules
- \`alertmanager/alertmanager.yml\`: Alertmanager configuration
- \`grafana/provisioning/datasources/prometheus.yml\`: Grafana datasource
- \`grafana/dashboards/petplantr-dashboard.json\`: PetPlantr dashboard

## Usage

Start monitoring stack:
\`\`\`bash
cd monitoring
docker compose -f docker-compose.monitoring.yml up -d
\`\`\`

Stop monitoring stack:
\`\`\`bash
cd monitoring
docker compose -f docker-compose.monitoring.yml down
\`\`\`

View logs:
\`\`\`bash
cd monitoring
docker compose -f docker-compose.monitoring.yml logs -f
\`\`\`

## Integration

The monitoring stack is integrated with the main PetPlantr deployment through:
- Shared Docker network for service discovery
- Metrics endpoints exposed by the API server
- Automatic service registration in Prometheus

## Security

- Grafana admin password should be changed from default
- Alertmanager SMTP credentials need to be configured
- Consider enabling authentication for production deployment
EOF

    log_success "Monitoring documentation generated: $docs_file"
}

# Main monitoring setup function
main() {
    log_info "Starting PetPlantr monitoring stack setup..."

    check_docker
    check_docker_compose
    create_monitoring_dirs
    generate_prometheus_config
    generate_alert_rules
    generate_alertmanager_config
    generate_grafana_datasource
    generate_grafana_dashboard_config
    generate_petplantr_dashboard
    generate_docker_compose
    update_main_docker_compose
    generate_documentation

    if [[ "${START_SERVICES:-true}" == "true" ]]; then
        start_monitoring
        test_monitoring
    fi

    log_success "🎉 Monitoring stack setup completed successfully!"
    log_info ""
    log_info "📊 Monitoring URLs:"
    log_info "  Prometheus: http://localhost:$PROMETHEUS_PORT"
    log_info "  Grafana: http://localhost:$GRAFANA_PORT (admin/admin)"
    log_info "  Alertmanager: http://localhost:9093"
    log_info ""
    log_info "📋 Next steps:"
    log_info "  1. Change Grafana admin password"
    log_info "  2. Configure Alertmanager SMTP settings"
    log_info "  3. Review and customize alert rules"
    log_info "  4. Set up additional dashboards as needed"
    log_info ""
    log_info "📁 Configuration files generated in: $MONITORING_DIR"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --monitoring-dir)
            MONITORING_DIR="$2"
            shift 2
            ;;
        --prometheus-port)
            PROMETHEUS_PORT="$2"
            shift 2
            ;;
        --grafana-port)
            GRAFANA_PORT="$2"
            shift 2
            ;;
        --no-start)
            START_SERVICES=false
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --monitoring-dir DIR     Monitoring directory (default: ./monitoring)"
            echo "  --prometheus-port PORT   Prometheus port (default: 9090)"
            echo "  --grafana-port PORT      Grafana port (default: 3000)"
            echo "  --no-start              Don't start services after setup"
            echo "  --force                 Force regeneration of configuration"
            echo "  --help                  Show this help"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main setup
main
EOF

    log_success "Monitoring setup script created"
}

# Make scripts executable
chmod +x setup-ssl.sh enable-monitoring.sh

log_success "🎉 Production enhancement scripts created successfully!"
log_info ""
log_info "📋 Available scripts:"
log_info "  ./setup-ssl.sh --help          - SSL/TLS certificate setup"
log_info "  ./enable-monitoring.sh --help  - Docker monitoring stack setup"
log_info ""
log_info "🚀 Quick start:"
log_info "  ./setup-ssl.sh --type self-signed"
log_info "  ./enable-monitoring.sh"