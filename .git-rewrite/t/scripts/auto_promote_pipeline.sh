#!/bin/bash
# Automated Weight Promotion Pipeline
# Watches for training completion and executes promotion + smoke test

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"
}

# Function to check for weight upload completion
check_weights_uploaded() {
    # Check for Stage 1 weights
    if aws s3 ls s3://petplantr-models/stage1/unet128_stage1_best.pth &>/dev/null; then
        return 0  # Weights found
    fi
    return 1  # Weights not found
}

# Function to check training logs for completion
check_training_completion() {
    # Check Modal apps status
    modal app list 2>/dev/null | grep -q "petplantr" || return 1
    
    # TODO: Parse actual Modal logs for "Checkpoint saved" or "Upload to S3 complete"
    # For now, rely on S3 weight detection
    return 1
}

# Main monitoring loop
monitor_and_promote() {
    log_info "🔍 Starting automated weight promotion pipeline..."
    log_info "   Watching for: 'Checkpoint saved / Upload to S3 complete'"
    log_info "   Will execute: ./promote_weights.sh && npm run smoke:e2e"
    log_info "   Press Ctrl+C to stop monitoring"
    
    while true; do
        log_info "Checking training status..."
        
        # Check if weights have been uploaded
        if check_weights_uploaded; then
            log_success "✅ WEIGHTS DETECTED: Stage 1 weights uploaded to S3!"
            log_success "🚀 Starting automatic promotion pipeline..."
            
            # Step 1: Promote weights
            log_info "1️⃣  Promoting weights to production..."
            if ./promote_weights.sh s3://petplantr-models/stage1/unet128_stage1_best.pth; then
                log_success "✅ Weight promotion completed!"
            else
                log_error "❌ Weight promotion failed!"
                exit 1
            fi
            
            # Step 2: Run smoke test
            log_info "2️⃣  Running end-to-end smoke test..."
            cd backend
            if npm run smoke:e2e; then
                log_success "✅ Smoke test PASSED!"
                log_success "🎉 READY FOR PUBLIC BETA!"
                
                # Notify completion
                log_success ""
                log_success "🚀🚀🚀 PROMOTION PIPELINE COMPLETE 🚀🚀🚀"
                log_success ""
                log_success "✅ Training: Complete"
                log_success "✅ Weights: Promoted to production"
                log_success "✅ Smoke test: PASSED"
                log_success ""
                log_success "🎯 Status: 2 checkmarks away from public Beta ACHIEVED!"
                log_success ""
                
                # Optional: Send notification (if configured)
                if command -v osascript &> /dev/null; then
                    osascript -e 'display notification "PetPlantr ready for public beta!" with title "Training Complete"' 2>/dev/null || true
                fi
                
                break
            else
                log_error "❌ Smoke test FAILED!"
                log_error "   Check CloudWatch logs for Lambda stack traces"
                log_error "   Check backend logs for errors"
                exit 1
            fi
        else
            log_info "⏳ Weights not yet uploaded, continuing to monitor..."
        fi
        
        # Wait 30 seconds before next check
        sleep 30
    done
}

# Handle interruption
trap 'log_warning "Monitoring stopped by user"; exit 0' INT

# Check dependencies
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install and configure AWS CLI"
    exit 1
fi

if ! command -v modal &> /dev/null; then
    log_error "Modal CLI not found. Please install Modal CLI"
    exit 1
fi

if [ ! -f "./promote_weights.sh" ]; then
    log_error "promote_weights.sh not found in current directory"
    exit 1
fi

if [ ! -f "backend/package.json" ]; then
    log_error "Backend directory not found. Run from PetPlantr root"
    exit 1
fi

# Start monitoring
monitor_and_promote
