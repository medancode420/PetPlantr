#!/bin/bash
# Quick Status Check for PetPlantr Action Plan
# Provides real-time status of all action items

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

status_icon() {
    local status=$1
    case $status in
        "complete") echo "✅" ;;
        "progress") echo "🔄" ;;
        "waiting") echo "⏳" ;;
        "error") echo "❌" ;;
        "ready") echo "🚀" ;;
        *) echo "☐" ;;
    esac
}

log_status() {
    local icon=$1
    local message=$2
    echo -e "$icon $message"
}

clear
echo -e "${BLUE}🎯 PetPlantr Action Plan - Quick Status Check${NC}"
echo -e "${BLUE}==============================================${NC}"
echo ""

# 1. Training Jobs Status
echo -e "${YELLOW}1️⃣  AI Training Jobs${NC}"
if command -v modal &> /dev/null; then
    echo "   Checking Modal jobs..."
    modal app list | grep -E "(petplantr|ap-)" || echo "   No active jobs found"
else
    echo "   ⚠️  Modal CLI not available"
fi

# Check S3 for weights
echo "   Checking S3 weights..."
if aws s3 ls s3://petplantr-models/stage1/ &>/dev/null; then
    STAGE1_WEIGHTS=$(aws s3 ls s3://petplantr-models/stage1/ --recursive | grep ".pth" | wc -l)
    if [ "$STAGE1_WEIGHTS" -gt 0 ]; then
        log_status "$(status_icon complete)" "Stage 1 weights uploaded ($STAGE1_WEIGHTS files)"
    else
        log_status "$(status_icon progress)" "Stage 1 training in progress"
    fi
else
    log_status "$(status_icon error)" "Cannot access S3 bucket"
fi

if aws s3 ls s3://petplantr-models/prod/unet_weights.pth &>/dev/null; then
    log_status "$(status_icon complete)" "Production weights promoted"
else
    log_status "$(status_icon waiting)" "Production weights not yet promoted"
fi

echo ""

# 2. Proprietary Photos
echo -e "${YELLOW}2️⃣  Proprietary Photo Collection${NC}"
if [ -d "data/proprietary_raw" ]; then
    PET_FOLDERS=$(find data/proprietary_raw -name "pet_*" -type d | wc -l)
    TOTAL_PHOTOS=$(find data/proprietary_raw -name "*.jpg" -o -name "*.jpeg" | wc -l)
    
    log_status "$(status_icon ready)" "Pet folders created: $PET_FOLDERS"
    log_status "$(status_icon progress)" "Photos collected: $TOTAL_PHOTOS/20"
    
    if [ "$TOTAL_PHOTOS" -ge 20 ]; then
        log_status "$(status_icon complete)" "Photo collection target reached!"
        
        if [ -d "data/proprietary_processed" ]; then
            log_status "$(status_icon complete)" "Photos preprocessed"
        else
            log_status "$(status_icon ready)" "Ready for preprocessing"
        fi
    else
        NEEDED=$((20 - TOTAL_PHOTOS))
        log_status "$(status_icon waiting)" "Need $NEEDED more photos"
    fi
else
    log_status "$(status_icon error)" "Proprietary data directory not found"
fi

echo ""

# 3. Production Keys
echo -e "${YELLOW}3️⃣  Production Keys${NC}"
if [ -f "frontend/.env.production" ]; then
    if grep -q "pk_live_" frontend/.env.production 2>/dev/null; then
        log_status "$(status_icon complete)" "Stripe live keys configured"
    else
        log_status "$(status_icon waiting)" "Stripe keys still in test mode"
    fi
    
    if grep -q "pk_live_" frontend/.env.production 2>/dev/null; then
        log_status "$(status_icon complete)" "Clerk live keys configured"
    else
        log_status "$(status_icon waiting)" "Clerk keys still in test mode"
    fi
else
    log_status "$(status_icon waiting)" "Production environment not configured"
fi

echo ""

# 4. Infrastructure
echo -e "${YELLOW}4️⃣  Infrastructure${NC}"
if git tag -l "v1.6.0" | grep -q "v1.6.0"; then
    log_status "$(status_icon complete)" "Version v1.6.0 tagged"
else
    log_status "$(status_icon waiting)" "Version freeze pending"
fi

if [ -f ".vscode/settings.json" ]; then
    log_status "$(status_icon complete)" "VSCode optimization configured"
else
    log_status "$(status_icon waiting)" "VSCode settings not optimized"
fi

echo ""

# 5. Production Readiness
echo -e "${YELLOW}5️⃣  Production Readiness${NC}"
if command -v vercel &> /dev/null; then
    log_status "$(status_icon ready)" "Vercel CLI available"
else
    log_status "$(status_icon waiting)" "Vercel CLI not installed"
fi

# Check Lambda function
if aws lambda get-function --function-name petplantr-pipeline-prod-generateSTL &>/dev/null; then
    log_status "$(status_icon complete)" "Production Lambda deployed"
else
    log_status "$(status_icon waiting)" "Production Lambda not found"
fi

echo ""

# 6. Quick Actions
echo -e "${YELLOW}🚀 Quick Actions${NC}"
echo "   Training Monitor:    python monitor_training.py"
echo "   Photo Preprocessing: python scripts/preprocess_proprietary.py"
echo "   Key Rotation:        bash scripts/rotate_production_keys.sh"
echo "   Stage 2 Training:    modal run train_unet_stage2.py --env BATCH=1,GRAD_ACCUM=8,EPOCHS=5"
echo "   Performance Test:    node performance-test.js"
echo ""

# Overall status
COMPLETED_TASKS=0
TOTAL_TASKS=10

# Count completed tasks
[ "$STAGE1_WEIGHTS" -gt 0 ] && ((COMPLETED_TASKS++))
[ "$TOTAL_PHOTOS" -ge 20 ] && ((COMPLETED_TASKS++))
[ -f "frontend/.env.production" ] && ((COMPLETED_TASKS++))
[ -f ".vscode/settings.json" ] && ((COMPLETED_TASKS++))
[ -d "data/proprietary_raw" ] && ((COMPLETED_TASKS++))
[ -f "scripts/preprocess_proprietary.py" ] && ((COMPLETED_TASKS++))
[ -f "scripts/process_and_upload.sh" ] && ((COMPLETED_TASKS++))
[ -f "train_unet_stage2.py" ] && ((COMPLETED_TASKS++))
[ -f "scripts/rotate_production_keys.sh" ] && ((COMPLETED_TASKS++))
[ -f "ACTION_PLAN_STATUS.md" ] && ((COMPLETED_TASKS++))

COMPLETION_PERCENT=$((COMPLETED_TASKS * 100 / TOTAL_TASKS))

echo -e "${BLUE}📊 Overall Progress: $COMPLETED_TASKS/$TOTAL_TASKS tasks ($COMPLETION_PERCENT%)${NC}"

if [ "$COMPLETION_PERCENT" -ge 80 ]; then
    echo -e "${GREEN}🎉 Ready for production launch!${NC}"
elif [ "$COMPLETION_PERCENT" -ge 60 ]; then
    echo -e "${YELLOW}⚡ Almost ready - few items remaining${NC}"
else
    echo -e "${RED}🔧 More setup needed${NC}"
fi

echo ""
echo -e "${BLUE}Last updated: $(date)${NC}"
