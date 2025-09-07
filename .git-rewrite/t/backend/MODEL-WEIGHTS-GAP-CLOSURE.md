# 🚨 PetPlantr AI Pipeline - Model Weights Gap Closure Plan

## Current Status: ✅ INFRASTRUCTURE READY, ⚠️ MODELS MISSING

The production-grade AI infrastructure has been successfully deployed, but **critical model weights are missing**. Here's the fastest path to close this gap and enable museum-quality pet planters.

---

## 🎯 **CRITICAL GAP: Shape-MVD Model Weights**

### Why It Matters
- **Shape-MVD is the core 3D reconstruction model** 
- Without fine-tuned weights, every AI stage returns **stub STLs**
- Prints will **NOT resemble the pet** - just generic shapes
- This is the **single blocking issue** for AI pipeline activation

### Current Impact
```bash
# AI Pipeline Status Check
./deploy-models.sh
# Result: ❌ PIPELINE NOT READY: Critical model weights missing
```

---

## ⚡ **FASTEST WAY TO CLOSE THE GAP**

### 1. **Complete Dataset (TOP PRIORITY)** 
- **Target**: 120-image dataset for Shape-MVD training
- **Current**: Need to finish dataset collection
- **Action**: Prioritize dataset completion immediately

### 2. **Run Fine-Tuning on Modal**
- **Platform**: Modal (cost-effective GPU training)
- **Cost**: ≈ $2 for 20-epoch fine-tune
- **Duration**: 2-4 hours training time
- **Output**: `latest.pth` trained weights file

### 3. **Deploy Model Weights**
```bash
# Once training completes, upload the weights:
aws s3 cp shape_mvd_pets_latest.pth s3://petplantr-models-prod/shape-mvd-prod/latest.pth

# Update Secrets Manager (automated):
aws secretsmanager update-secret \
  --secret-id "petplantr/models/shape-mvd-weights" \
  --secret-string "s3://petplantr-models-prod/shape-mvd-prod/latest.pth"
```

### 4. **Smoke Test One Photo**
```bash
# Test the complete AI pipeline:
curl -X POST https://mfxyjhg1l6.execute-api.us-east-1.amazonaws.com/dev/api/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "useAIPipeline": true,
    "photoUrls": ["s3://petplantr-uploads-dev/test-pet.jpg"],
    "sizeTier": "medium"
  }'
```

---

## 📊 **CURRENT INFRASTRUCTURE STATUS**

### ✅ **What's Already Deployed**
- **9 Lambda Functions**: All deployed (10MB each)
- **Step Functions**: Enhanced with AI pipeline support
- **S3 Buckets**: Production storage configured
- **Secrets Manager**: Model weight paths configured
- **IAM Roles**: Full permissions for AI operations
- **Configuration**: Production pipeline settings loaded

### ✅ **Ready for Model Integration**
```bash
# Infrastructure verification
./verify-deployment.sh
# Result: ✅ SUCCESS: PetPlantr AI pipeline is PRODUCTION-READY!
```

### ⚠️ **Missing Components**
1. **Shape-MVD weights** (CRITICAL)
2. **ViT feature extraction weights** (Secondary)  
3. **MiDaS depth estimation weights** (Secondary)

---

## 🔄 **CURRENT FALLBACK STRATEGY**

### Legacy Beta-0 Pipeline Still Works
```json
{
  "useAIPipeline": false,
  "photoKeys": ["uploads/user/photo.jpg"],
  "sizeTier": "medium"
}
```
- **Status**: ✅ Operational for immediate customer orders
- **Quality**: Basic 3D prints (existing quality level)
- **Use Case**: Production orders while AI models train

---

## 📅 **ESTIMATED TIMELINE**

| Task | Duration | Blocker |
|------|----------|---------|
| Complete 120-image dataset | 1-3 days | Dataset collection |
| Shape-MVD training on Modal | 2-4 hours | Dataset completion |
| Deploy weights to S3 | 5 minutes | Training completion |
| End-to-end smoke test | 10 minutes | Weight deployment |
| **TOTAL TO AI READY** | **1-3 days** | **Dataset only** |

---

## 🚀 **DEPLOYMENT SCRIPT READY**

The infrastructure includes automated deployment scripts:

```bash
# Check current status
./deploy-models.sh

# Upload Shape-MVD weights (when ready)
./deploy-models.sh --upload-shape-mvd /path/to/shape_mvd_latest.pth

# Upload ViT weights (optional)
./deploy-models.sh --upload-vit /path/to/vit_latest.pth

# Upload MiDaS weights (optional)  
./deploy-models.sh --upload-midas /path/to/midas_latest.pth
```

---

## 🎯 **SUCCESS CRITERIA**

### When Gap is Closed:
```bash
./deploy-models.sh
# Expected Result: ✅ PIPELINE READY: All critical models deployed
```

### AI Pipeline Test:
```bash
# End-to-end test command ready:
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:us-east-1:680604703891:stateMachine:petplantr-process-order-dev" \
  --input '{"orderId":"ai-test-001","useAIPipeline":true,"photoUrls":["s3://uploads/test.jpg"]}'
```

---

## 💡 **KEY INSIGHT**

**The AI pipeline infrastructure is 100% production-ready.** The only blocking factor is completing the Shape-MVD model training. Once the 120-image dataset is finished and the model trained on Modal (~$2, 2-4 hours), the AI pipeline can immediately start generating museum-quality pet planters.

**Bottom line**: We're 1-3 days away from production-ready AI, blocked only on dataset completion.

---

## 📞 **Next Actions**

1. ✅ **Infrastructure**: Complete (this task)
2. 🎯 **Dataset**: Finish 120-image collection (TOP PRIORITY)
3. 🚀 **Training**: Run Modal fine-tune (2-4 hours)
4. 📤 **Deploy**: Upload weights via deployment script (5 min)
5. 🧪 **Test**: Smoke test via /api/checkout (10 min)

**Ready for Shape-MVD model weights deployment!** 🎉
