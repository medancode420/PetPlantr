#!/bin/bash
# Promote Stage 1 UNet-128 weights to production bucket
# Usage: ./promote_weights.sh s3://petplantr-models/models/unet128_stage1_best.pth

set -e

SOURCE_WEIGHTS="$1"
PROD_BUCKET="s3://petplantr-models/prod"
PROD_PATH="${PROD_BUCKET}/unet128_stage1.pth"

echo "🚀 Promoting Stage 1 UNet-128 weights to production..."
echo "Source: ${SOURCE_WEIGHTS}"
echo "Destination: ${PROD_PATH}"
echo ""

# Verify source exists
echo "📋 Verifying source weights exist..."
aws s3 ls "${SOURCE_WEIGHTS}"
if [ $? -ne 0 ]; then
    echo "❌ Source weights not found: ${SOURCE_WEIGHTS}"
    exit 1
fi

# Create prod directory if not exists
echo "📁 Ensuring production directory exists..."
aws s3 ls "${PROD_BUCKET}/" || aws s3 mb "${PROD_BUCKET}"

# Copy weights to production
echo "📦 Copying weights to production bucket..."
aws s3 cp "${SOURCE_WEIGHTS}" "${PROD_PATH}"

# Verify copy succeeded
echo "✅ Verifying production weights..."
aws s3 ls "${PROD_PATH}"

# Set metadata for tracking
echo "🏷️  Adding metadata..."
aws s3 cp "${PROD_PATH}" "${PROD_PATH}" \
    --metadata "stage=1,architecture=unet128,training_date=$(date -u +%Y-%m-%d),promoted_date=$(date -u +%Y-%m-%d)"

echo ""
echo "🎉 SUCCESS! Weights promoted to production:"
echo "   ${PROD_PATH}"
echo ""
echo "📋 Next steps:"
echo "   1. Update Secrets Manager: UNET_WEIGHTS = ${PROD_PATH}"
echo "   2. Redeploy generateSTL Lambda"
echo "   3. Run smoke test"
echo ""
