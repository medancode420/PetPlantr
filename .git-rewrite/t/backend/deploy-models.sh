#!/bin/bash

# PetPlantr Model Weights Deployment Script
# This script handles the deployment of trained model weights to production

echo "🧠 PetPlantr Model Weights Deployment"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI not configured or credentials invalid${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"

# Function to check if file exists in S3
check_s3_file() {
    local bucket=$1
    local key=$2
    aws s3api head-object --bucket "$bucket" --key "$key" > /dev/null 2>&1
}

# Function to upload model weights
upload_model() {
    local local_path=$1
    local s3_path=$2
    local model_name=$3
    
    if [ ! -f "$local_path" ]; then
        echo -e "${RED}❌ Model file not found: $local_path${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📤 Uploading $model_name...${NC}"
    aws s3 cp "$local_path" "$s3_path"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $model_name uploaded successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to upload $model_name${NC}"
        return 1
    fi
}

# Check current model weights status
echo ""
echo -e "${BLUE}🔍 Checking Model Weights Status...${NC}"

# Shape-MVD weights
if check_s3_file "petplantr-models-prod" "shape-mvd-prod/latest.pth"; then
    echo -e "${GREEN}✅ Shape-MVD weights: DEPLOYED${NC}"
    SHAPE_MVD_STATUS="deployed"
else
    echo -e "${YELLOW}⚠️  Shape-MVD weights: MISSING${NC}"
    SHAPE_MVD_STATUS="missing"
fi

# ViT weights  
if check_s3_file "petplantr-models-prod" "vit-feature-extraction/latest.pth"; then
    echo -e "${GREEN}✅ ViT Feature Extraction weights: DEPLOYED${NC}"
    VIT_STATUS="deployed"
else
    echo -e "${YELLOW}⚠️  ViT Feature Extraction weights: MISSING${NC}"
    VIT_STATUS="missing"
fi

# MiDaS weights
if check_s3_file "petplantr-models-prod" "midas-depth-estimation/latest.pth"; then
    echo -e "${GREEN}✅ MiDaS Depth Estimation weights: DEPLOYED${NC}"
    MIDAS_STATUS="deployed"
else
    echo -e "${YELLOW}⚠️  MiDaS Depth Estimation weights: MISSING${NC}"
    MIDAS_STATUS="missing"
fi

# Check for local model files
echo ""
echo -e "${BLUE}🔍 Checking for Local Model Files...${NC}"

# Expected local paths (adjust as needed)
SHAPE_MVD_LOCAL="./models/shape_mvd_pets_latest.pth"
VIT_LOCAL="./models/vit_pet_features_latest.pth"  
MIDAS_LOCAL="./models/midas_pet_depth_latest.pth"

# Check if any local model files exist
LOCAL_FILES_FOUND=false

if [ -f "$SHAPE_MVD_LOCAL" ]; then
    echo -e "${GREEN}✅ Found local Shape-MVD weights: $SHAPE_MVD_LOCAL${NC}"
    LOCAL_FILES_FOUND=true
fi

if [ -f "$VIT_LOCAL" ]; then
    echo -e "${GREEN}✅ Found local ViT weights: $VIT_LOCAL${NC}"
    LOCAL_FILES_FOUND=true
fi

if [ -f "$MIDAS_LOCAL" ]; then
    echo -e "${GREEN}✅ Found local MiDaS weights: $MIDAS_LOCAL${NC}"
    LOCAL_FILES_FOUND=true
fi

if [ "$LOCAL_FILES_FOUND" = false ]; then
    echo -e "${YELLOW}⚠️  No local model files found in expected locations${NC}"
fi

# Provide deployment guidance
echo ""
echo -e "${BLUE}📋 Deployment Status & Next Steps${NC}"
echo "================================="

CRITICAL_MISSING=false

if [ "$SHAPE_MVD_STATUS" = "missing" ]; then
    CRITICAL_MISSING=true
    echo -e "${RED}🚨 CRITICAL: Shape-MVD weights missing${NC}"
    echo "   This is the core 3D reconstruction model"
    echo "   Without it, AI pipeline will generate stub STLs"
    echo ""
    echo -e "${YELLOW}📋 To Deploy Shape-MVD:${NC}"
    echo "   1. Complete the 120-image dataset"
    echo "   2. Run 20-epoch fine-tune on Modal (~$2)"
    echo "   3. Download trained weights (latest.pth)"
    echo "   4. Upload: aws s3 cp latest.pth s3://petplantr-models-prod/shape-mvd-prod/latest.pth"
    echo ""
fi

if [ "$VIT_STATUS" = "missing" ]; then
    echo -e "${YELLOW}⚠️  ViT Feature Extraction weights missing${NC}"
    echo "   Upload: aws s3 cp vit_weights.pth s3://petplantr-models-prod/vit-feature-extraction/latest.pth"
    echo ""
fi

if [ "$MIDAS_STATUS" = "missing" ]; then
    echo -e "${YELLOW}⚠️  MiDaS Depth Estimation weights missing${NC}" 
    echo "   Upload: aws s3 cp midas_weights.pth s3://petplantr-models-prod/midas-depth-estimation/latest.pth"
    echo ""
fi

# Quick upload option if local files exist
if [ "$LOCAL_FILES_FOUND" = true ]; then
    echo -e "${BLUE}🚀 Quick Deploy Options:${NC}"
    echo ""
    
    if [ -f "$SHAPE_MVD_LOCAL" ] && [ "$SHAPE_MVD_STATUS" = "missing" ]; then
        echo "Deploy Shape-MVD:"
        echo "  ./deploy-models.sh --upload-shape-mvd $SHAPE_MVD_LOCAL"
    fi
    
    if [ -f "$VIT_LOCAL" ] && [ "$VIT_STATUS" = "missing" ]; then
        echo "Deploy ViT:"
        echo "  ./deploy-models.sh --upload-vit $VIT_LOCAL"
    fi
    
    if [ -f "$MIDAS_LOCAL" ] && [ "$MIDAS_STATUS" = "missing" ]; then
        echo "Deploy MiDaS:"
        echo "  ./deploy-models.sh --upload-midas $MIDAS_LOCAL"
    fi
    echo ""
fi

# Handle command line arguments for actual uploads
if [ "$1" = "--upload-shape-mvd" ] && [ -n "$2" ]; then
    upload_model "$2" "s3://petplantr-models-prod/shape-mvd-prod/latest.pth" "Shape-MVD"
    exit $?
elif [ "$1" = "--upload-vit" ] && [ -n "$2" ]; then
    upload_model "$2" "s3://petplantr-models-prod/vit-feature-extraction/latest.pth" "ViT"
    exit $?
elif [ "$1" = "--upload-midas" ] && [ -n "$2" ]; then
    upload_model "$2" "s3://petplantr-models-prod/midas-depth-estimation/latest.pth" "MiDaS"
    exit $?
fi

# Test pipeline readiness
echo -e "${BLUE}🧪 Testing Pipeline Readiness${NC}"
echo "=============================="

if [ "$CRITICAL_MISSING" = true ]; then
    echo -e "${RED}❌ PIPELINE NOT READY: Critical model weights missing${NC}"
    echo -e "${RED}   Shape-MVD weights are required for AI pipeline to work${NC}"
    echo -e "${YELLOW}   Current behavior: AI pipeline will return stub STLs${NC}"
    echo ""
    echo -e "${BLUE}🔄 Fallback: Legacy Beta-0 pipeline still operational${NC}"
    echo "   Set useAIPipeline: false in orders for working 3D prints"
else
    echo -e "${GREEN}✅ PIPELINE READY: All critical models deployed${NC}"
    echo -e "${GREEN}   AI pipeline can generate museum-quality pet planters${NC}"
    echo ""
    echo -e "${BLUE}🚀 Test Command:${NC}"
    echo '   aws stepfunctions start-execution \'
    echo '     --state-machine-arn "arn:aws:states:us-east-1:680604703891:stateMachine:petplantr-process-order-dev" \'
    echo '     --input '"'"'{"orderId":"test-ai-001","userId":"test","useAIPipeline":true,"photoUrls":["s3://petplantr-uploads-dev/test.jpg"]}'"'"
fi

# Summary
echo ""
echo -e "${BLUE}📊 Summary${NC}"
echo "=========="
echo "Shape-MVD (Critical):    $SHAPE_MVD_STATUS"
echo "ViT Feature Extraction:  $VIT_STATUS"  
echo "MiDaS Depth Estimation:  $MIDAS_STATUS"
echo ""

if [ "$CRITICAL_MISSING" = false ]; then
    echo -e "${GREEN}🎉 PetPlantr AI Pipeline: PRODUCTION READY!${NC}"
else
    echo -e "${YELLOW}⏳ PetPlantr AI Pipeline: WAITING FOR MODEL WEIGHTS${NC}"
    echo -e "${BLUE}💡 Next Action: Complete Shape-MVD training and upload weights${NC}"
fi
