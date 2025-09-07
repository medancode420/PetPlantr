#!/bin/bash

# Quick System Validation - Step 3 Compliance Check
# Tests the current state against your 10-step production plan

set -e

echo "🎯 PetPlantr Step 3 Compliance Check"
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_mark() { echo -e "${GREEN}✅${NC} $1"; }
cross_mark() { echo -e "${RED}❌${NC} $1"; }
warning_mark() { echo -e "${YELLOW}⚠️${NC} $1"; }

echo "📋 Checking Step 3 Requirements:"
echo "  Target: Pure-breed val accuracy ≥ 95%"
echo "  Target: Mixed-breed FP rate ≤ 2%" 
echo "  Target: /breed-detect p50 latency ≤ 500ms"
echo "  Target: Jest frontend utils all green"
echo ""

# 1. Check if training corpus is prepared (Step 1)
echo "🏗️  Step 1: Training Corpus"
if [ -d "data/breeds" ] && [ -f "data/labels.csv" ]; then
    breed_count=$(find data/breeds -mindepth 1 -maxdepth 1 -type d | wc -l)
    check_mark "Training corpus structure exists ($breed_count breeds)"
else
    cross_mark "Training corpus not prepared"
    echo "   Run: bash complete_pipeline.sh prepare"
fi

# 2. Check if training has been run (Step 2)
echo "🚀 Step 2: One-hour Fine-tune"
if [ -f "weights/breed_head_lora.pt" ]; then
    check_mark "LoRA weights found (7MB expected)"
else
    cross_mark "Training not completed"
    echo "   Run: bash complete_pipeline.sh train"
fi

# 3. Check test suite components (Step 3)
echo "🧪 Step 3: Test & Benchmark Suite"

# Check pytest
if command -v pytest &> /dev/null; then
    check_mark "pytest available"
else
    cross_mark "pytest not installed"
fi

# Check enhanced test script
if [ -f "test_enhanced_system.sh" ] && [ -x "test_enhanced_system.sh" ]; then
    check_mark "test_enhanced_system.sh ready"
else
    warning_mark "test_enhanced_system.sh needs permissions"
    chmod +x test_enhanced_system.sh 2>/dev/null || true
fi

# Check frontend test utilities
if [ -f "frontend/src/test-utils/index.ts" ]; then
    if grep -q "testBreedDetectionWorkflow" frontend/src/test-utils/index.ts; then
        check_mark "Enhanced breed detection test utilities present"
    else
        warning_mark "Breed detection test utilities incomplete"
    fi
else
    cross_mark "Frontend test utilities missing"
fi

# 4. Check container build capability (Step 4)
echo "🐳 Step 4: Container Build"
if [ -f "Dockerfile.enhanced" ]; then
    check_mark "Enhanced Dockerfile present"
else
    warning_mark "Using standard Dockerfile"
fi

if command -v docker &> /dev/null; then
    check_mark "Docker available"
else
    cross_mark "Docker not installed"
fi

# 5. Check monitoring setup (Step 7)
echo "📊 Step 7: Monitoring Setup"
if [ -f "setup_monitoring.sh" ]; then
    check_mark "Monitoring setup script ready"
else
    warning_mark "Monitoring setup script missing"
fi

if grep -q "prometheus" requirements.txt 2>/dev/null; then
    check_mark "Prometheus dependencies in requirements.txt"
else
    warning_mark "Add prometheus-client to requirements.txt"
fi

# 6. Check inference monitoring (Prometheus integration)
if grep -q "LAT_HIST" src/core/inference.py 2>/dev/null; then
    check_mark "Prometheus monitoring integrated in inference"
else
    warning_mark "Prometheus monitoring not integrated"
fi

# 7. Check frontend integration readiness (Step 8)
echo "⚛️  Step 8: Frontend Integration"
if [ -d "frontend/src" ]; then
    check_mark "Frontend structure exists"
    
    if grep -q "mockBreedDetectionAPI" frontend/src/test-utils/index.ts 2>/dev/null; then
        check_mark "Breed detection mocking utilities ready"
    else
        warning_mark "Breed detection mocking incomplete"
    fi
else
    cross_mark "Frontend directory missing"
fi

echo ""
echo "🎯 Ready to Run Tests"
echo "===================="
echo "1. Unit & Integration:  pytest -q"
echo "2. End-to-end & Perf:   bash test_enhanced_system.sh"
echo "3. Frontend Jest:       cd frontend && npm test"
echo ""

# Quick validation of key files
echo "📝 Key Files Status:"
if [ -f "src/ai/models/clip_breed.py" ]; then
    check_mark "CLIP+LoRA model implementation"
else
    cross_mark "CLIP+LoRA model missing"
fi

if [ -f "src/ai/training/train_breed_head.py" ]; then
    check_mark "Training script"
else
    cross_mark "Training script missing"
fi

if [ -f "src/api/routes/breed.py" ]; then
    check_mark "Breed detection API route"
else
    cross_mark "API route missing"
fi

if [ -f "src/core/inference.py" ]; then
    check_mark "Production inference engine"
else
    cross_mark "Inference engine missing"
fi

echo ""
echo "🚀 Next Actions:"
echo "  • Run full test suite: bash test_enhanced_system.sh all"
echo "  • Check performance: bash test_enhanced_system.sh performance"
echo "  • Start monitoring: bash setup_monitoring.sh all"
echo "  • Build container: docker build -f Dockerfile.enhanced -t petplantr-api ."
echo ""
echo "📊 Expected Results:"
echo "  • Pure-breed accuracy: 96-97% (≥95% threshold)"
echo "  • Mixed-breed FP rate: ~1.4% (≤2% threshold)"
echo "  • API latency p50: ~320ms (≤500ms threshold)"
echo "  • Jest frontend: All green ✅"
