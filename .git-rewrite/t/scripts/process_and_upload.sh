#!/bin/bash
# PetPlantr Proprietary Photo Upload Script
# Uploads processed photos to S3 for Stage 2 training

set -e

# Configuration
S3_BUCKET="petplantr-models"
S3_PREFIX="datasets/proprietary_multiview"
PROCESSED_DIR="data/proprietary_processed"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if processed directory exists
if [ ! -d "$PROCESSED_DIR" ]; then
    log_error "Processed directory not found: $PROCESSED_DIR"
    log_info "Run: python scripts/preprocess_proprietary.py first"
    exit 1
fi

# Check if training manifest exists
MANIFEST_FILE="$PROCESSED_DIR/training_manifest.json"
if [ ! -f "$MANIFEST_FILE" ]; then
    log_error "Training manifest not found: $MANIFEST_FILE"
    log_info "Run: python scripts/preprocess_proprietary.py first"
    exit 1
fi

log_info "🚀 Starting proprietary photo upload to S3..."

# Read manifest to get pet count
PET_COUNT=$(cat "$MANIFEST_FILE" | jq -r '.total_pets')
PHOTO_COUNT=$(cat "$MANIFEST_FILE" | jq -r '.total_photos')
READY_FOR_STAGE2=$(cat "$MANIFEST_FILE" | jq -r '.ready_for_stage2')

log_info "📊 Dataset summary:"
log_info "   Pets: $PET_COUNT"
log_info "   Photos: $PHOTO_COUNT"
log_info "   Ready for Stage 2: $READY_FOR_STAGE2"

if [ "$READY_FOR_STAGE2" != "true" ]; then
    log_warning "Dataset not ready for Stage 2 training"
    log_info "Need at least 5 pets with 4 views each"
    exit 1
fi

# Upload manifest first
log_info "📋 Uploading training manifest..."
aws s3 cp "$MANIFEST_FILE" "s3://$S3_BUCKET/$S3_PREFIX/training_manifest.json"

# Upload all processed photos
log_info "📸 Uploading processed photos..."
for pet_dir in "$PROCESSED_DIR"/pet_*; do
    if [ -d "$pet_dir" ]; then
        pet_id=$(basename "$pet_dir")
        log_info "   Uploading $pet_id..."
        
        # Upload all photos in the pet directory
        aws s3 sync "$pet_dir" "s3://$S3_BUCKET/$S3_PREFIX/$pet_id/" \
            --exclude "*" \
            --include "*.jpg" \
            --include "*.jpeg" \
            --include "metadata.json"
        
        # Verify upload
        UPLOADED_COUNT=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/$pet_id/" --recursive | grep -E '\.(jpg|jpeg)$' | wc -l)
        log_success "     $pet_id: $UPLOADED_COUNT photos uploaded"
    fi
done

# Verify total upload
log_info "🔍 Verifying upload..."
TOTAL_UPLOADED=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" --recursive | grep -E '\.(jpg|jpeg)$' | wc -l)
log_success "✅ Upload complete: $TOTAL_UPLOADED photos in S3"

# Generate S3 dataset summary
log_info "📊 Generating S3 dataset summary..."
aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" --recursive --human-readable --summarize > upload_summary.txt

log_success "🎉 Proprietary dataset upload complete!"
log_info "📁 S3 Location: s3://$S3_BUCKET/$S3_PREFIX/"
log_info "📋 Summary saved to: upload_summary.txt"
log_info ""
log_info "🚀 Ready for Stage 2 UNet-256 Training!"
log_info "   Command: modal run train_unet_stage2.py --env BATCH=1,GRAD_ACCUM=8,EPOCHS=5"
log_info "   Target: Validation loss < 0.09"
