#!/bin/bash

# PetPlantr Launch & Harden - Complete Operational Validation
# Moves from "implemented" to "operational" with full stack verification

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

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
STAGING_TAG="petplantr/api:test-${TIMESTAMP}"
SAMPLE_IMAGE="test_images/sample_golden_retriever.jpg"
RESULTS_DIR="launch_results_${TIMESTAMP}"

# Performance thresholds
MAX_BUILD_TIME=300        # 5 minutes
MAX_IMAGE_SIZE=3          # 3 GB
MAX_LOCAL_LATENCY=600     # 600ms
MAX_STAGING_LATENCY=500   # 500ms
MAX_GPU_MEM=5             # 5GB
MAX_CPU=1.0               # 1 vCPU

echo "🚀 PetPlantr Launch & Harden - Operational Validation"
echo "====================================================="

mkdir -p "$RESULTS_DIR"

# Step 1: Dry-run the entire pipeline locally
step1_local_dryrun() {
    log_step "🔧 STEP 1: Dry-run entire pipeline locally"
    
    # Create sample image if missing
    if [ ! -f "$SAMPLE_IMAGE" ]; then
        log_info "Creating sample test image..."
        mkdir -p "$(dirname "$SAMPLE_IMAGE")"
        python3 -c "
from PIL import Image
import numpy as np
img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
img.save('$SAMPLE_IMAGE')
"
        log_success "Sample image created: $SAMPLE_IMAGE"
    fi
    
    # 1.1 Build image with timing
    log_info "Building Docker image (target: <5 min)..."
    start_time=$(date +%s)
    
    if docker build -f Dockerfile.enhanced -t "$STAGING_TAG" . > "$RESULTS_DIR/docker_build.log" 2>&1; then
        build_time=$(($(date +%s) - start_time))
        
        if [ $build_time -lt $MAX_BUILD_TIME ]; then
            log_success "✅ Image built in ${build_time}s (< ${MAX_BUILD_TIME}s target)"
        else
            log_warning "⚠️ Build took ${build_time}s (exceeds ${MAX_BUILD_TIME}s)"
        fi
        
        # Check image size
        image_size=$(docker images "$STAGING_TAG" --format "table {{.Size}}" | tail -n 1)
        image_size_gb=$(docker inspect "$STAGING_TAG" --format='{{.Size}}' | awk '{print $1/1024/1024/1024}')
        
        if (( $(echo "$image_size_gb < $MAX_IMAGE_SIZE" | bc -l) )); then
            log_success "✅ Image size: ${image_size} (< ${MAX_IMAGE_SIZE}GB)"
        else
            log_warning "⚠️ Image size: ${image_size} (exceeds ${MAX_IMAGE_SIZE}GB)"
        fi
    else
        log_error "❌ Docker build failed"
        cat "$RESULTS_DIR/docker_build.log"
        return 1
    fi
    
    # 1.2 Unit tests
    log_info "Running unit tests..."
    if pytest -q --tb=short > "$RESULTS_DIR/pytest.log" 2>&1; then
        log_success "✅ All unit tests passed"
    else
        log_error "❌ Unit tests failed"
        cat "$RESULTS_DIR/pytest.log"
        return 1
    fi
    
    # 1.3 API smoke test
    log_info "Running API smoke test..."
    docker run -d --name petplantr-test -p 8000:8000 "$STAGING_TAG" > /dev/null
    
    # Wait for container to start
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "✅ Health endpoint responding"
    else
        log_error "❌ Health endpoint failed"
        docker logs petplantr-test
        docker stop petplantr-test && docker rm petplantr-test
        return 1
    fi
    
    # Test breed detection with timing
    start_time=$(date +%s%3N)
    if curl -X POST -F "file=@$SAMPLE_IMAGE" \
            http://localhost:8000/api/breed-detect \
            -o "$RESULTS_DIR/breed_response.json" \
            -w "%{http_code}" 2>/dev/null | grep -q "200"; then
        
        end_time=$(date +%s%3N)
        latency=$((end_time - start_time))
        
        if [ $latency -lt $MAX_LOCAL_LATENCY ]; then
            log_success "✅ Breed detection: ${latency}ms (< ${MAX_LOCAL_LATENCY}ms)"
        else
            log_warning "⚠️ Breed detection: ${latency}ms (exceeds ${MAX_LOCAL_LATENCY}ms)"
            log_info "Consider disabling TTA or reducing model complexity"
        fi
        
        # Validate response format
        if jq -e '.predicted_breed and .confidence' "$RESULTS_DIR/breed_response.json" > /dev/null; then
            predicted_breed=$(jq -r '.predicted_breed' "$RESULTS_DIR/breed_response.json")
            confidence=$(jq -r '.confidence' "$RESULTS_DIR/breed_response.json")
            log_success "✅ Valid response: $predicted_breed ($confidence confidence)"
        else
            log_error "❌ Invalid response format"
            cat "$RESULTS_DIR/breed_response.json"
        fi
    else
        log_error "❌ Breed detection API failed"
        docker logs petplantr-test
    fi
    
    # 1.4 Prometheus metrics
    log_info "Checking Prometheus metrics..."
    if curl -s http://localhost:8000/metrics | grep -q "inference_latency_seconds"; then
        log_success "✅ Prometheus metrics available"
        curl -s http://localhost:8000/metrics | grep "inference_latency_seconds" > "$RESULTS_DIR/metrics.txt"
    else
        log_warning "⚠️ Prometheus metrics not found"
    fi
    
    # Cleanup
    docker stop petplantr-test && docker rm petplantr-test > /dev/null 2>&1
    
    # 1.5 Quick validation
    log_info "Running quick validation..."
    if [ -f "quick_validation.sh" ]; then
        if bash quick_validation.sh > "$RESULTS_DIR/validation.log" 2>&1; then
            log_success "✅ Quick validation passed"
        else
            log_warning "⚠️ Quick validation had issues"
            tail -n 10 "$RESULTS_DIR/validation.log"
        fi
    else
        log_warning "⚠️ quick_validation.sh not found"
    fi
}

# Step 2: GPU staging run (one-hour fine-tune)
step2_gpu_staging() {
    log_step "🎯 STEP 2: GPU staging run (one-hour fine-tune)"
    
    # Check if data directory exists
    if [ ! -d "data/breeds" ]; then
        log_warning "⚠️ Training data not found. Run: bash complete_pipeline.sh prepare"
        return 1
    fi
    
    # Check GPU availability
    if command -v nvidia-smi >/dev/null 2>&1; then
        gpu_count=$(nvidia-smi -L | wc -l)
        log_info "GPU(s) available: $gpu_count"
        
        # Run training with staging tag
        log_info "Starting one-hour fine-tune with W&B staging tag..."
        export WANDB_PROJECT=petplantr-breed-head
        export WANDB_TAGS="staging-$(date +%F),operational-validation"
        
        if bash one_hour_finetune.sh > "$RESULTS_DIR/training.log" 2>&1; then
            log_success "✅ Training completed successfully"
            
            # Check LoRA checkpoint
            if [ -f "weights/breed_head_lora.pt" ]; then
                ckpt_size=$(du -h weights/breed_head_lora.pt | cut -f1)
                ckpt_size_mb=$(du -m weights/breed_head_lora.pt | cut -f1)
                
                if [ "$ckpt_size_mb" -le 8 ]; then
                    log_success "✅ LoRA checkpoint: $ckpt_size (≤ 8MB)"
                else
                    log_warning "⚠️ LoRA checkpoint: $ckpt_size (exceeds 8MB)"
                fi
            else
                log_error "❌ LoRA checkpoint not found"
                return 1
            fi
            
            # Check GPU utilization from logs
            if grep -q "GPU utilization" "$RESULTS_DIR/training.log"; then
                gpu_util=$(grep "GPU utilization" "$RESULTS_DIR/training.log" | tail -n 1 | awk '{print $3}')
                log_info "Peak GPU utilization: $gpu_util"
            fi
        else
            log_error "❌ Training failed"
            tail -n 20 "$RESULTS_DIR/training.log"
            return 1
        fi
    else
        log_warning "⚠️ No GPU available, skipping GPU staging run"
    fi
}

# Step 3: End-to-end benchmark on staging container
step3_e2e_benchmark() {
    log_step "⚡ STEP 3: End-to-end benchmark on staging container"
    
    # Start container with GPU support if available
    if command -v nvidia-smi >/dev/null 2>&1; then
        docker run -d --gpus all \
                   -e MODEL_WEIGHTS=weights/breed_head_lora.pt \
                   -p 8001:8000 \
                   --name petplantr-staging \
                   "$STAGING_TAG" > /dev/null
        port=8001
    else
        docker run -d \
                   -e MODEL_WEIGHTS=weights/breed_head_lora.pt \
                   -p 8001:8000 \
                   --name petplantr-staging \
                   "$STAGING_TAG" > /dev/null
        port=8001
    fi
    
    # Wait for startup
    sleep 15
    
    # Run performance benchmark
    log_info "Running performance benchmark..."
    
    # Create performance test script
    cat > "$RESULTS_DIR/perf_test.py" << 'EOF'
import time
import requests
import statistics
import json
from pathlib import Path

def benchmark_api(url, image_path, iterations=10):
    """Benchmark the breed detection API"""
    latencies = []
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    print(f"Running {iterations} requests to {url}")
    
    for i in range(iterations):
        start = time.time()
        
        try:
            response = requests.post(
                url,
                files={'file': ('test.jpg', image_data, 'image/jpeg')},
                timeout=10
            )
            
            if response.status_code == 200:
                latency_ms = (time.time() - start) * 1000
                latencies.append(latency_ms)
                print(f"Request {i+1}: {latency_ms:.1f}ms")
            else:
                print(f"Request {i+1}: Failed ({response.status_code})")
        
        except Exception as e:
            print(f"Request {i+1}: Error - {e}")
    
    if latencies:
        results = {
            'mean': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'p95': sorted(latencies)[int(len(latencies) * 0.95)],
            'min': min(latencies),
            'max': max(latencies),
            'count': len(latencies)
        }
        
        print(f"\nResults:")
        print(f"  Mean latency: {results['mean']:.1f}ms")
        print(f"  P50 latency: {results['median']:.1f}ms") 
        print(f"  P95 latency: {results['p95']:.1f}ms")
        print(f"  Min latency: {results['min']:.1f}ms")
        print(f"  Max latency: {results['max']:.1f}ms")
        
        return results
    else:
        return None

if __name__ == "__main__":
    import sys
    
    url = f"http://localhost:{sys.argv[1]}/api/breed-detect"
    image_path = sys.argv[2]
    
    results = benchmark_api(url, image_path)
    
    if results:
        with open('perf_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Check thresholds
        if results['p95'] <= 500:
            print(f"✅ P95 latency: {results['p95']:.1f}ms (≤ 500ms)")
            sys.exit(0)
        else:
            print(f"❌ P95 latency: {results['p95']:.1f}ms (exceeds 500ms)")
            sys.exit(1)
    else:
        print("❌ No successful requests")
        sys.exit(1)
EOF
    
    cd "$RESULTS_DIR"
    if python3 perf_test.py "$port" "../$SAMPLE_IMAGE"; then
        log_success "✅ Performance benchmark passed"
        
        # Check resource usage
        container_stats=$(docker stats petplantr-staging --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}")
        log_info "Container resource usage:"
        echo "$container_stats"
        
    else
        log_error "❌ Performance benchmark failed"
        docker logs petplantr-staging
    fi
    
    cd "$PROJECT_ROOT"
    
    # Cleanup
    docker stop petplantr-staging && docker rm petplantr-staging > /dev/null 2>&1
}

# Step 4: CI/CD smoke test
step4_cicd_smoke() {
    log_step "🔄 STEP 4: CI/CD smoke test"
    
    # Check if we're in a git repository
    if [ -d ".git" ]; then
        log_info "Checking GitHub Actions workflow..."
        
        if [ -f ".github/workflows/deploy.yml" ]; then
            log_success "✅ GitHub Actions workflow found"
            
            # Check workflow validity
            if grep -q "build" ".github/workflows/deploy.yml" && \
               grep -q "test" ".github/workflows/deploy.yml" && \
               grep -q "deploy" ".github/workflows/deploy.yml"; then
                log_success "✅ Workflow includes build, test, and deploy steps"
            else
                log_warning "⚠️ Workflow missing required steps"
            fi
        else
            log_warning "⚠️ GitHub Actions workflow not found"
        fi
        
        # Check for secrets requirements
        log_info "Required secrets for CI/CD:"
        echo "  - GHCR_PAT (GitHub Container Registry token)"
        echo "  - WANDB_API_KEY (Weights & Biases API key)"
        echo "  - AWS_ACCESS_KEY_ID (if using AWS)"
        echo "  - AWS_SECRET_ACCESS_KEY (if using AWS)"
        
    else
        log_warning "⚠️ Not in a git repository"
    fi
}

# Step 5: Blue-green canary setup
step5_canary_setup() {
    log_step "🚦 STEP 5: Blue-green canary setup"
    
    # Create canary deployment script
    cat > "$RESULTS_DIR/canary_deploy.sh" << 'EOF'
#!/bin/bash

# Blue-Green Canary Deployment Script
# Deploys new version at 5% traffic for 30 minutes

NEW_TAG="$1"
NAMESPACE="petplantr"

if [ -z "$NEW_TAG" ]; then
    echo "Usage: $0 <new-image-tag>"
    exit 1
fi

echo "🚦 Starting canary deployment for $NEW_TAG"

# Update deployment with new image
kubectl -n "$NAMESPACE" set image deploy/breed-api \
    breed-api="ghcr.io/org/petplantr-api:$NEW_TAG" --record

# Wait for rollout
kubectl -n "$NAMESPACE" rollout status deploy/breed-api --timeout=300s

# Configure traffic split (5% to new version)
kubectl apply -f - << YAML
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: breed-api-canary
  namespace: $NAMESPACE
spec:
  hosts:
  - breed-api
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: breed-api
        subset: v2
      weight: 100
  - route:
    - destination:
        host: breed-api
        subset: v1
      weight: 95
    - destination:
        host: breed-api
        subset: v2
      weight: 5
YAML

echo "✅ Canary deployment active (5% traffic)"
echo "Monitor for 30 minutes, then promote to 100% if metrics are green"

# Monitor script
cat > monitor_canary.sh << 'MONITOR'
#!/bin/bash

echo "🔍 Monitoring canary deployment..."

# Check error rate
ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])" | jq -r '.data.result[0].value[1] // 0')

# Check latency
P95_LATENCY=$(curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(inference_latency_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1] // 0')

echo "Error rate: $ERROR_RATE"
echo "P95 latency: ${P95_LATENCY}s"

# Alert thresholds
if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
    echo "🚨 ALERT: Error rate exceeds 1%"
    exit 1
fi

if (( $(echo "$P95_LATENCY > 0.7" | bc -l) )); then
    echo "🚨 ALERT: P95 latency exceeds 0.7s"
    exit 1
fi

echo "✅ Metrics within acceptable range"
MONITOR

chmod +x monitor_canary.sh

echo "📊 Use ./monitor_canary.sh to check metrics"
echo "🔄 Use 'kubectl rollout undo deploy/breed-api' to rollback if needed"
EOF
    
    chmod +x "$RESULTS_DIR/canary_deploy.sh"
    log_success "✅ Canary deployment script created: $RESULTS_DIR/canary_deploy.sh"
}

# Step 6: Data drift guardrails
step6_drift_guardrails() {
    log_step "📊 STEP 6: Data drift guardrails"
    
    # Create drift monitoring script
    cat > "$RESULTS_DIR/drift_monitor.py" << 'EOF'
#!/usr/bin/env python3
"""
Data and concept drift monitoring for breed detection
Runs nightly to detect distribution changes
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from scipy import stats
import wandb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DriftMonitor:
    def __init__(self, baseline_path: str = "baseline_distribution.json"):
        self.baseline_path = baseline_path
        self.baseline_data = self.load_baseline()
        
    def load_baseline(self) -> Dict[str, Any]:
        """Load baseline distribution from training data"""
        if Path(self.baseline_path).exists():
            with open(self.baseline_path) as f:
                return json.load(f)
        return {}
    
    def save_baseline(self, data: Dict[str, Any]):
        """Save baseline distribution"""
        with open(self.baseline_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def sample_recent_uploads(self, n_samples: int = 100) -> List[Dict[str, Any]]:
        """Sample recent uploads for drift analysis"""
        # This would integrate with your actual data pipeline
        # For now, return mock data
        
        logger.info(f"Sampling {n_samples} recent uploads...")
        
        # Mock sampling - replace with actual implementation
        samples = []
        for i in range(n_samples):
            samples.append({
                'confidence': np.random.beta(8, 2),  # High confidence distribution
                'predicted_breed': np.random.choice(['golden_retriever', 'labrador_retriever', 'mixed_breed']),
                'entropy': -np.sum(np.random.dirichlet([1, 1, 1]) * np.log(np.random.dirichlet([1, 1, 1]) + 1e-8)),
                'timestamp': time.time() - i * 3600
            })
        
        return samples
    
    def calculate_kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """Calculate KL divergence between two distributions"""
        # Add small epsilon to avoid log(0)
        epsilon = 1e-8
        p = p + epsilon
        q = q + epsilon
        
        # Normalize
        p = p / np.sum(p)
        q = q / np.sum(q)
        
        return np.sum(p * np.log(p / q))
    
    def analyze_confidence_drift(self, samples: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze confidence score drift"""
        confidences = [s['confidence'] for s in samples]
        
        if not self.baseline_data.get('confidence_stats'):
            # Establish baseline
            baseline_stats = {
                'mean': np.mean(confidences),
                'std': np.std(confidences),
                'median': np.median(confidences)
            }
            return {'drift_score': 0.0, 'baseline_stats': baseline_stats}
        
        baseline_mean = self.baseline_data['confidence_stats']['mean']
        current_mean = np.mean(confidences)
        
        # Calculate drift as normalized difference
        drift_score = abs(current_mean - baseline_mean) / baseline_mean
        
        return {
            'drift_score': drift_score,
            'baseline_mean': baseline_mean,
            'current_mean': current_mean,
            'threshold': 0.1  # 10% change threshold
        }
    
    def analyze_breed_distribution_drift(self, samples: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze breed distribution drift"""
        breeds = [s['predicted_breed'] for s in samples]
        breed_counts = {}
        
        for breed in breeds:
            breed_counts[breed] = breed_counts.get(breed, 0) + 1
        
        # Convert to probability distribution
        total = len(breeds)
        current_dist = np.array([breed_counts.get(b, 0) / total for b in 
                                ['golden_retriever', 'labrador_retriever', 'mixed_breed']])
        
        if not self.baseline_data.get('breed_distribution'):
            return {'kl_divergence': 0.0, 'baseline_dist': current_dist.tolist()}
        
        baseline_dist = np.array(self.baseline_data['breed_distribution'])
        kl_div = self.calculate_kl_divergence(current_dist, baseline_dist)
        
        return {
            'kl_divergence': kl_div,
            'baseline_dist': baseline_dist.tolist(),
            'current_dist': current_dist.tolist(),
            'threshold': 0.05  # KL divergence threshold
        }
    
    async def run_drift_analysis(self) -> Dict[str, Any]:
        """Run complete drift analysis"""
        logger.info("Starting drift analysis...")
        
        # Sample recent data
        samples = await self.sample_recent_uploads()
        
        # Analyze different types of drift
        confidence_drift = self.analyze_confidence_drift(samples)
        distribution_drift = self.analyze_breed_distribution_drift(samples)
        
        # Overall drift assessment
        drift_detected = (
            confidence_drift['drift_score'] > confidence_drift.get('threshold', 0.1) or
            distribution_drift['kl_divergence'] > distribution_drift.get('threshold', 0.05)
        )
        
        results = {
            'timestamp': time.time(),
            'samples_analyzed': len(samples),
            'confidence_drift': confidence_drift,
            'distribution_drift': distribution_drift,
            'drift_detected': drift_detected,
            'retrain_recommended': drift_detected
        }
        
        # Log to W&B
        if 'WANDB_API_KEY' in os.environ:
            wandb.init(project='petplantr-drift-monitoring', job_type='drift-analysis')
            wandb.log(results)
            wandb.finish()
        
        # Save results
        with open(f'drift_analysis_{int(time.time())}.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

async def main():
    monitor = DriftMonitor()
    results = await monitor.run_drift_analysis()
    
    print(f"🔍 Drift Analysis Results:")
    print(f"  Samples analyzed: {results['samples_analyzed']}")
    print(f"  Confidence drift: {results['confidence_drift']['drift_score']:.3f}")
    print(f"  Distribution KL divergence: {results['distribution_drift']['kl_divergence']:.3f}")
    print(f"  Drift detected: {results['drift_detected']}")
    print(f"  Retrain recommended: {results['retrain_recommended']}")
    
    if results['drift_detected']:
        print("🚨 DRIFT DETECTED: Consider retraining the model")
        return 1
    else:
        print("✅ No significant drift detected")
        return 0

if __name__ == "__main__":
    import os
    exit_code = asyncio.run(main())
    exit(exit_code)
EOF
    
    chmod +x "$RESULTS_DIR/drift_monitor.py"
    
    # Create cron job script
    cat > "$RESULTS_DIR/setup_drift_cron.sh" << 'EOF'
#!/bin/bash

# Setup nightly drift monitoring cron job
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add to crontab (runs at 2 AM daily)
(crontab -l 2>/dev/null; echo "0 2 * * * cd $SCRIPT_DIR && python3 drift_monitor.py >> drift_monitor.log 2>&1") | crontab -

echo "✅ Drift monitoring cron job installed"
echo "   Runs daily at 2 AM"
echo "   Logs to: $SCRIPT_DIR/drift_monitor.log"
EOF
    
    chmod +x "$RESULTS_DIR/setup_drift_cron.sh"
    
    log_success "✅ Drift monitoring setup created"
    log_info "  Monitor script: $RESULTS_DIR/drift_monitor.py"
    log_info "  Cron setup: $RESULTS_DIR/setup_drift_cron.sh"
}

# Generate launch gate checklist
generate_launch_gate() {
    log_step "🚦 LAUNCH GATE CHECKLIST"
    
    cat > "$RESULTS_DIR/launch_gate_checklist.md" << 'EOF'
# 🚀 PetPlantr Launch Gate Checklist

## Validation Results

| Gate | Owner | Status | Details |
|------|--------|--------|---------|
| Dataset checksum committed | Dev | ⬜ | Verify data/breeds/ structure and labels.csv |
| breed_head_lora.pt in S3 with version pin | CI | ⬜ | Model weights uploaded and versioned |
| Local dry-run complete | Dev | ⬜ | All Step 1 validations passed |
| GPU staging run green | Dev | ⬜ | Training completed, val_acc ≥ 95% |
| Performance benchmark passed | Dev | ⬜ | P95 latency ≤ 500ms, resource usage normal |
| CI/CD pipeline validated | DevOps | ⬜ | GitHub Actions workflow tested |
| Canary deployment ready | SRE | ⬜ | Blue-green scripts prepared |
| Monitoring dashboards live | SRE | ⬜ | Grafana/Prometheus operational |
| Drift monitoring enabled | ML | ⬜ | Nightly analysis cron job active |
| Security scan passed | Security | ⬜ | No HIGH/CRITICAL CVEs |
| Rollback plan tested | SRE | ⬜ | `kubectl rollout undo` verified |

## Performance Targets Met

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Build time | < 5 min | ___ min | ⬜ |
| Image size | ≤ 3 GB | ___ GB | ⬜ |
| Local API latency | < 600ms | ___ ms | ⬜ |
| Staging P95 latency | ≤ 500ms | ___ ms | ⬜ |
| GPU memory usage | ≤ 5 GB | ___ GB | ⬜ |
| CPU usage | ≤ 1 vCPU | ___ vCPU | ⬜ |

## Security Checklist

- [ ] CVE scan shows no HIGH/CRITICAL issues
- [ ] No secrets baked into container image
- [ ] Upload size limit (3MB) enforced
- [ ] API rate limiting configured
- [ ] HTTPS/TLS certificates valid

## Monitoring Checklist

- [ ] Prometheus metrics endpoint active
- [ ] Grafana dashboards accessible
- [ ] W&B logging functional
- [ ] Alert rules configured:
  - [ ] inference_latency_seconds_p95 > 0.7s for 5min
  - [ ] http_requests_total{status=~"5.."} > 1 for 1min
  - [ ] Drift detection KL divergence > 0.05

## 🎯 LAUNCH APPROVAL

When all boxes are checked ✅, you are CLEAR TO LAUNCH! 🚀

**Final Steps:**
1. Deploy canary at 5% traffic
2. Monitor for 30 minutes
3. Promote to 100% if green
4. Enable production monitoring
5. Celebrate! 🎉
EOF
    
    log_success "✅ Launch gate checklist created: $RESULTS_DIR/launch_gate_checklist.md"
}

# Main execution
main() {
    case "${1:-all}" in
        "1"|"local")
            step1_local_dryrun
            ;;
        "2"|"training")
            step2_gpu_staging
            ;;
        "3"|"benchmark")
            step3_e2e_benchmark
            ;;
        "4"|"cicd")
            step4_cicd_smoke
            ;;
        "5"|"canary")
            step5_canary_setup
            ;;
        "6"|"drift")
            step6_drift_guardrails
            ;;
        "checklist")
            generate_launch_gate
            ;;
        "all")
            echo "🚀 Running complete launch & harden validation..."
            echo ""
            
            step1_local_dryrun || { log_error "Step 1 failed"; exit 1; }
            step2_gpu_staging || { log_warning "Step 2 had issues (GPU training)"; }
            step3_e2e_benchmark || { log_error "Step 3 failed"; exit 1; }
            step4_cicd_smoke
            step5_canary_setup
            step6_drift_guardrails
            generate_launch_gate
            
            echo ""
            log_success "🎉 Launch & Harden validation complete!"
            echo ""
            log_info "📊 Results saved to: $RESULTS_DIR/"
            log_info "📋 Next: Review launch gate checklist"
            log_info "🚀 When all gates are ✅, you're CLEAR TO LAUNCH!"
            ;;
        *)
            echo "Usage: $0 [1|local|2|training|3|benchmark|4|cicd|5|canary|6|drift|checklist|all]"
            echo ""
            echo "Steps:"
            echo "  1|local     - Dry-run entire pipeline locally"
            echo "  2|training  - GPU staging run (one-hour fine-tune)"
            echo "  3|benchmark - End-to-end benchmark on staging container"
            echo "  4|cicd      - CI/CD smoke test"
            echo "  5|canary    - Blue-green canary setup"
            echo "  6|drift     - Data drift guardrails"
            echo "  checklist   - Generate launch gate checklist"
            echo "  all         - Run complete validation (recommended)"
            exit 1
            ;;
    esac
}

# Check dependencies
if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    log_error "jq not found. Install with: brew install jq"
    exit 1
fi

main "$@"
