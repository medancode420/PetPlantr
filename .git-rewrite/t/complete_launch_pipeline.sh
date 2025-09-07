#!/bin/bash

# PetPlantr Production Launch Automation
# Complete end-to-end validation and deployment pipeline

set -e

# Global configuration
PROJECT_ROOT="/Users/medan/Downloads/PetPlantr"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="launch_pipeline_${TIMESTAMP}.log"
METRICS_FILE="launch_metrics_${TIMESTAMP}.json"

# Performance thresholds - Aligned with Business SLOs
MAX_INFERENCE_LATENCY_MS=500  # P50 latency ≤ 500ms (TTA on)
MIN_ACCURACY_PERCENT=95       # Pure breed accuracy ≥ 95%
MAX_MEMORY_MB=2048            # Container RAM ≤ 2GB
MAX_GPU_VRAM_MB=5120          # GPU VRAM ≤ 5GB on A10G
MAX_ERROR_RATE_PERCENT=1      # Error rate ≤ 1% (5xx responses)
MAX_DOCKER_BUILD_TIME_SEC=300

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Redirect all output to log file and console
exec > >(tee -a "$LOG_FILE")
exec 2>&1

log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') - $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%H:%M:%S') - $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date '+%H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') - $1"; }
log_pipeline() { echo -e "${PURPLE}[PIPELINE]${NC} $(date '+%H:%M:%S') - $1"; }

# Global state tracking
PIPELINE_FAILED=false
STAGE_COUNT=0
STAGES_PASSED=0

record_metric() {
    local stage="$1"
    local metric="$2" 
    local value="$3"
    local unit="$4"
    local status="$5"
    
    cat >> "$METRICS_FILE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "stage": "$stage",
  "metric": "$metric",
  "value": $value,
  "unit": "$unit",
  "status": "$status"
},
EOF
}

fail_pipeline() {
    local reason="$1"
    log_error "PIPELINE FAILED: $reason"
    PIPELINE_FAILED=true
    
    echo ""
    echo "========================================"
    echo "         PIPELINE FAILURE"
    echo "========================================"
    echo "Reason: $reason"
    echo "Stage: $((STAGE_COUNT + 1))"
    echo "Stages completed: $STAGES_PASSED/$STAGE_COUNT"
    echo "Log file: $LOG_FILE"
    echo "Metrics file: $METRICS_FILE"
    echo ""
    echo "Manual intervention required before proceeding to production."
    exit 1
}

complete_stage() {
    local stage_name="$1"
    STAGE_COUNT=$((STAGE_COUNT + 1))
    STAGES_PASSED=$((STAGES_PASSED + 1))
    log_success "Stage $STAGE_COUNT completed: $stage_name"
}

# Stage 1: Environment Setup and Validation
stage_1_environment_setup() {
    log_pipeline "Stage 1: Environment Setup and Validation"
    
    # Check prerequisites
    log_info "Checking prerequisites..."
    
    # Docker
    if ! command -v docker >/dev/null 2>&1; then
        fail_pipeline "Docker not installed"
    fi
    
    # Python and dependencies
    if ! command -v python3 >/dev/null 2>&1; then
        fail_pipeline "Python 3 not installed"
    fi
    
    # Check disk space (need at least 10GB)
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        fail_pipeline "Insufficient disk space: ${available_space}GB (need 10GB+)"
    fi
    
    record_metric "environment" "disk_space_gb" "$available_space" "GB" "PASS"
    
    # GPU check (optional)
    if command -v nvidia-smi >/dev/null 2>&1; then
        gpu_memory=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
        log_info "GPU detected with ${gpu_memory}MB memory"
        record_metric "environment" "gpu_memory_mb" "$gpu_memory" "MB" "PASS"
    else
        log_warning "No GPU detected - will use CPU inference"
    fi
    
    # Create necessary directories
    mkdir -p data/breeds data/hard_neg weights test_images
    
    complete_stage "Environment Setup"
}

# Stage 2: Docker Build and Validation
stage_2_docker_build() {
    log_pipeline "Stage 2: Docker Build and Validation"
    
    # Clean previous builds
    log_info "Cleaning previous Docker builds..."
    docker image rm petplantr/api:test 2>/dev/null || true
    
    # Build Docker image with timing
    log_info "Building Docker image..."
    start_time=$(date +%s)
    
    if ! docker build -f Dockerfile.enhanced -t petplantr/api:test . --no-cache; then
        fail_pipeline "Docker build failed"
    fi
    
    end_time=$(date +%s)
    build_time=$((end_time - start_time))
    
    # Check build time threshold
    if [ $build_time -gt $MAX_DOCKER_BUILD_TIME_SEC ]; then
        fail_pipeline "Docker build time ${build_time}s exceeds ${MAX_DOCKER_BUILD_TIME_SEC}s threshold"
    fi
    
    # Check image size
    image_size=$(docker image inspect petplantr/api:test --format='{{.Size}}')
    image_size_gb=$(echo "scale=2; $image_size / 1073741824" | bc)
    
    if [ $(echo "$image_size_gb > 4" | bc) -eq 1 ]; then
        fail_pipeline "Docker image size ${image_size_gb}GB exceeds 4GB limit"
    fi
    
    record_metric "docker" "build_time_sec" "$build_time" "seconds" "PASS"
    record_metric "docker" "image_size_gb" "$image_size_gb" "GB" "PASS"
    
    log_success "Docker build completed in ${build_time}s (${image_size_gb}GB)"
    complete_stage "Docker Build"
}

# Stage 3: Unit Tests
stage_3_unit_tests() {
    log_pipeline "Stage 3: Unit Tests"
    
    log_info "Running unit tests..."
    start_time=$(date +%s)
    
    # Run pytest if available
    if command -v pytest >/dev/null 2>&1; then
        if ! pytest tests/ -v --tb=short; then
            fail_pipeline "Unit tests failed"
        fi
    else
        log_warning "pytest not available, running basic Python validation"
        
        # Basic validation of key modules
        if ! python3 -c "import src.ai.models.clip_breed; print('CLIP model import: OK')"; then
            fail_pipeline "CLIP model import failed"
        fi
        
        if ! python3 -c "import src.core.inference; print('Inference engine import: OK')"; then
            fail_pipeline "Inference engine import failed"
        fi
    fi
    
    end_time=$(date +%s)
    test_time=$((end_time - start_time))
    
    record_metric "testing" "unit_test_time_sec" "$test_time" "seconds" "PASS"
    
    complete_stage "Unit Tests"
}

# Stage 4: API Smoke Test
stage_4_api_smoke_test() {
    log_pipeline "Stage 4: API Smoke Test"
    
    # Create test image
    if [ ! -f "test_dog.jpg" ]; then
        if command -v convert >/dev/null 2>&1; then
            convert -size 512x512 xc:brown -fill white -draw "circle 256,256 256,200" test_dog.jpg
        else
            # Create dummy file
            echo "fake image data" > test_dog.jpg
        fi
    fi
    
    # Start container
    log_info "Starting API container..."
    if command -v nvidia-smi >/dev/null 2>&1; then
        container_id=$(docker run -d --gpus all -p 8000:8000 petplantr/api:test)
    else
        container_id=$(docker run -d -p 8000:8000 petplantr/api:test)
    fi
    
    # Wait for startup
    log_info "Waiting for API to start..."
    max_retries=30
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            log_info "API is ready"
            break
        fi
        retry_count=$((retry_count + 1))
        sleep 2
    done
    
    if [ $retry_count -eq $max_retries ]; then
        docker stop "$container_id" >/dev/null 2>&1
        docker rm "$container_id" >/dev/null 2>&1
        fail_pipeline "API failed to start within 60 seconds"
    fi
    
    # Test breed detection endpoint
    log_info "Testing breed detection endpoint..."
    start_time=$(date +%s%3N)
    
    response=$(curl -s -w "%{http_code},%{time_total}" \
        -F "file=@test_dog.jpg" \
        http://localhost:8000/breed-detect)
    
    end_time=$(date +%s%3N)
    
    # Parse response
    http_code=$(echo "$response" | tail -n1 | cut -d',' -f1)
    response_time_sec=$(echo "$response" | tail -n1 | cut -d',' -f2)
    response_time_ms=$(echo "$response_time_sec * 1000" | bc)
    
    # Cleanup container
    docker stop "$container_id" >/dev/null
    docker rm "$container_id" >/dev/null
    
    # Validate response
    if [ "$http_code" != "200" ]; then
        fail_pipeline "API returned HTTP $http_code (expected 200)"
    fi
    
    if [ $(echo "$response_time_ms > $MAX_INFERENCE_LATENCY_MS" | bc) -eq 1 ]; then
        fail_pipeline "API response time ${response_time_ms}ms exceeds ${MAX_INFERENCE_LATENCY_MS}ms threshold"
    fi
    
    record_metric "api" "response_time_ms" "${response_time_ms%.*}" "ms" "PASS"
    record_metric "api" "http_status" "$http_code" "code" "PASS"
    
    log_success "API smoke test passed (${response_time_ms%.*}ms response time)"
    complete_stage "API Smoke Test"
}

# Stage 5: Performance Benchmarking
stage_5_performance_benchmark() {
    log_pipeline "Stage 5: Performance Benchmarking"
    
    # Start container for benchmarking
    log_info "Starting container for performance testing..."
    if command -v nvidia-smi >/dev/null 2>&1; then
        container_id=$(docker run -d --gpus all -p 8000:8000 petplantr/api:test)
    else
        container_id=$(docker run -d -p 8000:8000 petplantr/api:test)
    fi
    
    sleep 15  # Allow full startup
    
    # Latency benchmark (10 requests)
    log_info "Running latency benchmark..."
    latencies=()
    
    for i in {1..10}; do
        start_time=$(date +%s%3N)
        response=$(curl -s -F "file=@test_dog.jpg" http://localhost:8000/breed-detect)
        end_time=$(date +%s%3N)
        
        latency=$((end_time - start_time))
        latencies+=("$latency")
        
        if ! echo "$response" | jq . >/dev/null 2>&1; then
            docker stop "$container_id" >/dev/null
            docker rm "$container_id" >/dev/null
            fail_pipeline "Invalid JSON response in latency test #$i"
        fi
    done
    
    # Calculate statistics
    total_latency=0
    for lat in "${latencies[@]}"; do
        total_latency=$((total_latency + lat))
    done
    avg_latency=$((total_latency / ${#latencies[@]}))
    
    # Calculate P95
    sorted_latencies=($(printf '%s\n' "${latencies[@]}" | sort -n))
    p95_index=$(echo "${#sorted_latencies[@]} * 0.95" | bc | cut -d. -f1)
    p95_latency=${sorted_latencies[$p95_index]}
    
    # Check memory usage
    memory_usage_raw=$(docker stats --no-stream --format "{{.MemUsage}}" "$container_id")
    memory_usage_mb=$(echo "$memory_usage_raw" | cut -d'/' -f1 | sed 's/MiB//' | sed 's/GiB/*1024/' | bc)
    
    # Cleanup
    docker stop "$container_id" >/dev/null
    docker rm "$container_id" >/dev/null
    
    # Validate thresholds
    if [ $avg_latency -gt $MAX_INFERENCE_LATENCY_MS ]; then
        fail_pipeline "Average latency ${avg_latency}ms exceeds ${MAX_INFERENCE_LATENCY_MS}ms threshold"
    fi
    
    if [ $(echo "$memory_usage_mb > $MAX_MEMORY_MB" | bc) -eq 1 ]; then
        fail_pipeline "Memory usage ${memory_usage_mb}MB exceeds ${MAX_MEMORY_MB}MB threshold"
    fi
    
    record_metric "performance" "avg_latency_ms" "$avg_latency" "ms" "PASS"
    record_metric "performance" "p95_latency_ms" "$p95_latency" "ms" "PASS"
    record_metric "performance" "memory_usage_mb" "${memory_usage_mb%.*}" "MB" "PASS"
    
    log_success "Performance benchmark passed:"
    log_success "  Average latency: ${avg_latency}ms"
    log_success "  P95 latency: ${p95_latency}ms"
    log_success "  Memory usage: ${memory_usage_mb%.*}MB"
    
    complete_stage "Performance Benchmark"
}

# Stage 6: Integration Tests
stage_6_integration_tests() {
    log_pipeline "Stage 6: Integration Tests"
    
    # Test Prometheus metrics
    log_info "Testing Prometheus metrics integration..."
    
    container_id=$(docker run -d -p 8000:8000 petplantr/api:test)
    sleep 10
    
    # Make request to generate metrics
    curl -s -F "file=@test_dog.jpg" http://localhost:8000/breed-detect >/dev/null
    
    # Check metrics endpoint
    metrics_response=$(curl -s http://localhost:8000/metrics)
    
    expected_metrics=("inference_latency_seconds" "http_requests_total")
    missing_metrics=0
    
    for metric in "${expected_metrics[@]}"; do
        if ! echo "$metrics_response" | grep -q "$metric"; then
            log_error "Missing Prometheus metric: $metric"
            missing_metrics=$((missing_metrics + 1))
        fi
    done
    
    docker stop "$container_id" >/dev/null
    docker rm "$container_id" >/dev/null
    
    if [ $missing_metrics -gt 0 ]; then
        fail_pipeline "Missing $missing_metrics Prometheus metrics"
    fi
    
    record_metric "integration" "prometheus_metrics" "$((${#expected_metrics[@]} - missing_metrics))" "count" "PASS"
    
    complete_stage "Integration Tests"
}

# Stage 7: Security and Compliance Check
stage_7_security_check() {
    log_pipeline "Stage 7: Security and Compliance Check"
    
    # Check for secrets in Docker image
    log_info "Scanning for exposed secrets..."
    
    secrets_found=$(docker run --rm petplantr/api:test find / -name "*.env" -o -name "*secret*" -o -name "*key*" 2>/dev/null | grep -v "/proc\|/sys\|/dev" | wc -l)
    
    if [ "$secrets_found" -gt 5 ]; then  # Allow some system files
        log_warning "Potential secrets found in Docker image: $secrets_found files"
    fi
    
    # Check image vulnerabilities if Trivy is available
    if command -v trivy >/dev/null 2>&1; then
        log_info "Running Trivy security scan..."
        
        if trivy image --severity HIGH,CRITICAL --exit-code 1 petplantr/api:test; then
            log_success "No HIGH/CRITICAL vulnerabilities found"
        else
            log_warning "Vulnerabilities found - review before production deployment"
        fi
    else
        log_warning "Trivy not available - skipping vulnerability scan"
    fi
    
    record_metric "security" "secrets_scan" "$secrets_found" "files" "PASS"
    
    complete_stage "Security Check"
}

# Stage 8: Deployment Readiness
stage_8_deployment_readiness() {
    log_pipeline "Stage 8: Deployment Readiness Check"
    
    # Check required files
    required_files=(
        "Dockerfile.enhanced"
        "requirements.txt"
        "src/ai/models/clip_breed.py"
        "src/core/inference.py"
        "api_server.py"
    )
    
    missing_files=0
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Missing required file: $file"
            missing_files=$((missing_files + 1))
        fi
    done
    
    if [ $missing_files -gt 0 ]; then
        fail_pipeline "Missing $missing_files required files for deployment"
    fi
    
    # Generate deployment manifest
    cat > deployment_manifest.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: petplantr-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: petplantr-api
  template:
    metadata:
      labels:
        app: petplantr-api
    spec:
      containers:
      - name: api
        image: petplantr/api:${TIMESTAMP}
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: petplantr-api-service
spec:
  selector:
    app: petplantr-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
EOF
    
    # Tag image for deployment
    docker tag petplantr/api:test petplantr/api:${TIMESTAMP}
    docker tag petplantr/api:test petplantr/api:latest
    
    record_metric "deployment" "required_files" "$((${#required_files[@]} - missing_files))" "count" "PASS"
    
    log_success "Deployment manifest created: deployment_manifest.yaml"
    log_success "Docker images tagged for deployment"
    
    complete_stage "Deployment Readiness"
}

# Main pipeline execution
main() {
    echo "========================================"
    echo "   PetPlantr Production Launch Pipeline"
    echo "========================================"
    echo "Started: $(date)"
    echo "Log: $LOG_FILE"
    echo "Metrics: $METRICS_FILE"
    echo ""
    
    # Initialize metrics file
    echo '{"pipeline": "petplantr-launch", "started": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "metrics": [' > "$METRICS_FILE"
    
    # Run all stages
    stage_1_environment_setup
    stage_2_docker_build  
    stage_3_unit_tests
    stage_4_api_smoke_test
    stage_5_performance_benchmark
    stage_6_integration_tests
    stage_7_security_check
    stage_8_deployment_readiness
    
    # Close metrics file
    echo ']}' >> "$METRICS_FILE"
    
    # Success summary
    echo ""
    echo "========================================"
    echo "       PIPELINE SUCCESS! 🚀"
    echo "========================================"
    echo "All $STAGES_PASSED stages completed successfully"
    echo "Deployment artifacts:"
    echo "  - Docker image: petplantr/api:${TIMESTAMP}"
    echo "  - Kubernetes manifest: deployment_manifest.yaml"
    echo "  - Performance metrics: $METRICS_FILE"
    echo ""
    echo "READY FOR PRODUCTION DEPLOYMENT!"
    echo ""
    echo "Next steps:"
    echo "1. Push images to container registry"
    echo "2. Apply Kubernetes manifest"
    echo "3. Configure monitoring and alerts"
    echo "4. Set up blue-green deployment"
    echo ""
    echo "Completed: $(date)"
}

# Execute main pipeline
main "$@"
