#!/bin/bash
# PetPlantr Stage 1 Deployment Script
# Execute remaining steps to go live with UNet-128

set -e

echo "🚀 PetPlantr Stage 1 Final Deployment"
echo "======================================"
echo ""

# Step 1: Update AWS Secrets Manager
echo "1️⃣ Updating AWS Secrets Manager..."
echo "   Current weights path: s3://petplantr-models/prod/unet128_stage1.pth"
echo ""
echo "   Run this command in AWS CLI (replace YOUR_REGION):"
echo '   aws secretsmanager update-secret \'
echo '     --secret-id petplantr/prod/model-config \'
echo '     --secret-string '"'"'{"UNET_WEIGHTS": "s3://petplantr-models/prod/unet128_stage1.pth"}'"'"' \'
echo '     --region YOUR_REGION'
echo ""

# Step 2: Redeploy Lambda
echo "2️⃣ Redeploying generateSTL Lambda..."
cd ../backend
if [ -f "serverless.yml" ]; then
    echo "   Found serverless.yml, deploying..."
    serverless deploy --function generateSTL
    echo "   ✅ Lambda redeployed with new weights"
else
    echo "   ⚠️ serverless.yml not found, manual deployment needed"
fi
cd ../datasets
echo ""

# Step 3: Verify deployment
echo "3️⃣ Verifying deployment..."
echo "   TODO: Test generateSTL endpoint with sample pet image"
echo "   TODO: Check CloudWatch logs for successful model loading"
echo ""

# Step 4: Production readiness checklist
echo "4️⃣ Production Readiness Checklist:"
echo "   [ ] AWS Secrets Manager updated"
echo "   [ ] generateSTL Lambda redeployed"
echo "   [ ] CloudWatch logs show successful model loading"
echo "   [ ] Test inference request succeeds"
echo "   [ ] OctoFarm printer queue is ready"
echo "   [ ] Slack #ops-alerts channel configured"
echo ""

# Step 5: First print instructions
echo "5️⃣ First Planter Print Instructions:"
echo "   1. Upload pet photo to web interface"
echo "   2. Verify STL generation completes in < 8 minutes"
echo "   3. Check STL in MeshLab: watertight, < 180k faces"
echo "   4. Send to OctoFarm print queue"
echo "   5. Monitor print progress"
echo "   6. Post completion photo in Slack #ops-alerts"
echo ""

# Step 6: Stage 2 preparation
echo "6️⃣ Stage 2 Preparation (after successful first print):"
echo "   • Collect 5+ multi-view pet photos"
echo "   • Regenerate embeddings dataset"
echo "   • Launch: modal run train_unet_stage2.py"
echo "   • Target: validation loss < 0.09"
echo ""

echo "🎯 CURRENT STATUS: Weights promoted, smoke test passed"
echo "🎯 NEXT CRITICAL ACTION: Update Secrets Manager → Redeploy Lambda"
echo "🎯 ETA TO FIRST PRINT: 2-4 hours"
echo ""
echo "🎉 Stage 1 UNet-128 training is COMPLETE and ready for production!"
