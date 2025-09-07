#!/bin/bash
# 🚀 Process and Upload Proprietary Photos for Tier A Training
set -e

echo "🚀 PROPRIETARY PHOTO PROCESSING & UPLOAD PIPELINE"
echo "================================================="

# Directories
RAW_DIR="/Users/medan/Desktop/PetPlantr_Dataset/proprietary_raw"
PROCESSED_DIR="/Users/medan/Desktop/PetPlantr_Dataset/processed/proprietary"
S3_BUCKET="petplantr-dataset"
S3_PREFIX="proprietary/multiview"

echo "📁 Raw photos: $RAW_DIR"
echo "📁 Processed: $PROCESSED_DIR"
echo "☁️  S3 target: s3://$S3_BUCKET/$S3_PREFIX/"
echo ""

# Check if raw directory exists
if [ ! -d "$RAW_DIR" ]; then
    echo "❌ Raw photo directory not found: $RAW_DIR"
    echo "🔧 Run setup first: ./setup_tier_a_photos.sh"
    exit 1
fi

# Check if any pet directories exist
PET_COUNT=$(find "$RAW_DIR" -name "pet_*" -type d | wc -l)
if [ "$PET_COUNT" -eq 0 ]; then
    echo "❌ No pet directories found in $RAW_DIR"
    echo "📸 Add photos to pet_XXX_name/ directories first"
    exit 1
fi

echo "📊 Found $PET_COUNT pet directories"

# Check for photos in pet directories
PHOTO_COUNT=$(find "$RAW_DIR" -name "*.jpg" | wc -l)
echo "📸 Found $PHOTO_COUNT photos total"

if [ "$PHOTO_COUNT" -eq 0 ]; then
    echo "❌ No photos found!"
    echo "📸 Add front.jpg, left.jpg, right.jpg, back.jpg to each pet directory"
    exit 1
fi

echo ""

# Step 1: Process photos
echo "🔄 STEP 1: Processing photos..."
echo "------------------------------"

cd /Users/medan/Downloads/PetPlantr/backend/datasets

python3 preprocess_proprietary.py \
    --input-dir "$RAW_DIR" \
    --output-dir "$PROCESSED_DIR" \
    --resize 512

if [ $? -ne 0 ]; then
    echo "❌ Photo processing failed!"
    exit 1
fi

echo ""

# Step 2: Verify processed photos
echo "📊 STEP 2: Verifying processed photos..."
echo "--------------------------------------"

if [ ! -d "$PROCESSED_DIR" ]; then
    echo "❌ Processed directory not created"
    exit 1
fi

PROCESSED_COUNT=$(find "$PROCESSED_DIR" -name "*.jpg" | wc -l)
echo "✅ Processed $PROCESSED_COUNT images"

# Check metadata
METADATA_FILE="$PROCESSED_DIR/proprietary_metadata.json"
if [ -f "$METADATA_FILE" ]; then
    echo "✅ Metadata file created: $(basename $METADATA_FILE)"
    
    # Extract success count from metadata (simple grep)
    COMPLETE_PETS=$(grep -o '"complete": true' "$METADATA_FILE" | wc -l)
    echo "✅ Complete pets: $COMPLETE_PETS"
    
    if [ "$COMPLETE_PETS" -ge 5 ]; then
        echo "🚀 READY FOR DEMO TRAINING!"
    elif [ "$COMPLETE_PETS" -ge 1 ]; then
        echo "🔄 Partial ready - collect more for better results"
    fi
else
    echo "⚠️  Metadata file not found"
fi

echo ""

# Step 3: Upload to S3
echo "☁️  STEP 3: Uploading to S3..."
echo "-----------------------------"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    echo "🔧 Run: aws configure"
    exit 1
fi

echo "🔄 Uploading processed photos to S3..."

aws s3 sync "$PROCESSED_DIR/" "s3://$S3_BUCKET/$S3_PREFIX/" \
    --acl private \
    --exclude "*.DS_Store" \
    --delete

if [ $? -eq 0 ]; then
    echo "✅ Upload complete!"
    echo "📍 Location: s3://$S3_BUCKET/$S3_PREFIX/"
else
    echo "❌ Upload failed!"
    exit 1
fi

echo ""

# Step 4: Verify S3 upload
echo "✅ STEP 4: Verifying S3 upload..."
echo "--------------------------------"

S3_COUNT=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" --recursive | grep '\.jpg' | wc -l)
echo "☁️  S3 image count: $S3_COUNT"

if [ "$S3_COUNT" -eq "$PROCESSED_COUNT" ]; then
    echo "✅ All images uploaded successfully!"
else
    echo "⚠️  Upload count mismatch (local: $PROCESSED_COUNT, S3: $S3_COUNT)"
fi

echo ""

# Final summary and next steps
echo "🎉 PROPRIETARY PHOTO PIPELINE COMPLETE!"
echo "======================================="
echo "📊 Processed: $PROCESSED_COUNT images"
echo "☁️  Uploaded: $S3_COUNT images to S3"
echo "✅ Complete pets: $COMPLETE_PETS"
echo ""

echo "🚀 NEXT STEPS:"
if [ "$COMPLETE_PETS" -ge 5 ]; then
    echo "   1. Launch demo training:"
    echo "      modal run train_shape_mvd.py --demo"
    echo ""
    echo "   2. Or wait for Oxford backbone to complete, then:"
    echo "      modal run train_shape_mvd.py --tier-a-fast"
elif [ "$COMPLETE_PETS" -ge 1 ]; then
    echo "   1. Collect more pets (target: 5+ for demo, 10+ for Tier A)"
    echo "   2. Re-run this script: ./process_and_upload.sh"
    echo "   3. Launch training when ready"
else
    echo "   1. ⚡ URGENT: Collect pet photos!"
    echo "   2. Place 4 views per pet in proprietary_raw/pet_XXX_name/"
    echo "   3. Re-run this script"
fi

echo ""
echo "📊 Training readiness:"
echo "   • Oxford backbone: Running in background (~45 min)"
echo "   • Proprietary data: $COMPLETE_PETS complete pets"
echo "   • Animal3D: Download from https://xujiacong.github.io/AnimalNeRF/"
echo ""
echo "🎯 Goal: Get to Tier A training in <60 minutes!"
