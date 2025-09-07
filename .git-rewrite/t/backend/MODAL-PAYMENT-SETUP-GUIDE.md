# Modal Payment Setup and Training Guide

## 🎯 Current Status
- ✅ Modal CLI authenticated successfully
- ✅ Enhanced dataset ready (20MB, 150 images, 37 breeds)
- ✅ Training script ready (`enhanced_shape_mvd_training.py`)
- 💳 **NEXT:** Add payment method to unlock full credits

## 💰 Credit Information
- **Current:** $5 free credits (without payment method)
- **With Payment:** $30 total credits ($5 free + $25 unlocked)
- **Training Cost:** ~$2.50 for full Shape-MVD training
- **Remaining Budget:** ~$27.50 for additional training/inference

## 🚀 Steps to Add Payment Method

### 1. Open Billing Page
The billing page is already open in your browser, or visit:
```
https://modal.com/settings/billing
```

### 2. Add Payment Method
- Click "Add Payment Method" or "Add Card"
- Enter your credit/debit card details
- This unlocks the additional $25 credits immediately
- No charge until you exceed $30 total usage

### 3. Verify Credits
After adding payment method, verify your credits:
```bash
cd /Users/medan/Downloads/PetPlantr
/Users/medan/Downloads/PetPlantr/.venv/bin/python backend/datasets/check_modal_credits.py
```

## 🏃 Run Training
Once payment method is added:
```bash
cd /Users/medan/Downloads/PetPlantr
/Users/medan/Downloads/PetPlantr/.venv/bin/python backend/datasets/enhanced_shape_mvd_training.py
```

## 📊 Training Details
- **GPU:** A100 (40GB VRAM)
- **Dataset:** 150 images, 37 breeds, 100% breed diversity
- **Duration:** ~2-3 hours
- **Cost:** ~$2.50
- **Output:** Trained Shape-MVD model weights
- **Next:** Upload weights to S3, deploy to ECS

## 🔧 Budget Breakdown ($400 Total)
- **Training:** $2.50 (Shape-MVD on Modal)
- **Fine-tuning:** $10-20 (additional training iterations)
- **GPU Inference:** $50-100 (ECS GPU instances)
- **Development:** $50-100 (testing and optimization)
- **Production:** $200+ (ongoing inference costs)

## 🎯 After Training
1. Download trained model weights
2. Upload to S3 production bucket
3. Update Secrets Manager with model paths
4. Build and deploy Docker images to ECR
5. Launch ECS GPU instances
6. Update Step Functions to use GPU pipeline
7. End-to-end testing with real pet photos

## ⚠️ Important Notes
- Modal charges by GPU-hour: ~$1.25/hour for A100
- Training is estimated at ~2 hours = ~$2.50 total
- Payment method unlocks credits immediately
- No charges until you exceed $30 total usage
- Cancel anytime if needed

Ready to unlock your credits and start training! 🚀
