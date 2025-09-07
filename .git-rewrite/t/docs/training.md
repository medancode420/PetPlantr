# PetPlantr AI Training Pipeline Documentation

## Overview

The PetPlantr training pipeline implements a progressive complexity approach for 3D pet planter generation using Shape-MVD (Multi-View Diffusion) models.

## Pipeline Architecture

```
📊 Local M3 Max → ☁️ GPU Training → 🏭 Production
     CLIP          Shape-MVD        Inference API
   Embeddings        Training         Lambda
```

## Training Stages

### Stage 1: Oxford Backbone Pre-training
- **Model**: UNet-128 (64M parameters)
- **GPU**: Tesla T4 
- **Dataset**: Oxford-IIIT enhanced dataset (150 images, 37 breeds)
- **Duration**: ~45 minutes
- **Cost**: ~$0.60
- **Output**: `s3://petplantr-models/backbone/oxford_pretrain.pt`

**Command:**
```bash
modal run backend/datasets/oxford_backbone_training.py
```

**Job ID Example**: `ap-aAUGz3CuBS5kl1ukUREqmn`

### Stage 2: Enhanced UNet (Planned)
- **Model**: UNet-256 with EMA
- **GPU**: Tesla T4
- **Batch Size**: 1 with gradient accumulation
- **Duration**: ~60 minutes 
- **Cost**: ~$0.80

**Command:**
```bash
make stage-2-unet
```

### Stage 3: Full Scale (Future)
- **Model**: UNet-320, full Shape-MVD channels
- **GPU**: A10G
- **Batch Size**: 4
- **Duration**: ~2.5 hours
- **Cost**: ~$1.80

**Command:**
```bash
make stage-3-full
```

## Current Job Monitoring

### Active Training Job
- **Status**: Running Oxford Backbone Training
- **Job ID**: `ap-aAUGz3CuBS5kl1ukUREqmn`
- **Modal URL**: https://modal.com/apps/medancode420/main/ap-aAUGz3CuBS5kl1ukUREqmn
- **Started**: June 23, 2025

### Monitoring Commands

```bash
# List active Modal apps
modal app list

# View logs for specific job
modal app logs <job-id>

# Check current training progress (every 10 minutes)
modal app list | grep petpl
```

## CLI Commands Reference

### Training Commands

```bash
# Local embedding preparation (M3 Max)
make prep-embeddings

# Stage 1 Oxford backbone training 
modal run backend/datasets/oxford_backbone_training.py

# Stage 2 enhanced training (coming soon)
make stage-2-unet

# Full Shape-MVD training (future)
make fine-tune-mvd
```

### Weight Management

```bash
# Promote trained weights to production
./promote_weights.sh s3://petplantr-models/backbone/oxford_pretrain.pt

# Test inference with promoted weights
python infer_shape_mvd.py --weights oxford_pretrain.pt --input test_images/mydog_front.jpg
```

### Monitoring & Alerts

```bash
# Setup AWS cost monitoring
./setup_gpu_budget_alert.sh

# Send Slack notifications
python backend/datasets/notify_job_status.py --status success --job-type "Oxford Backbone" --duration "45min" --cost "$0.60"
```

## File Structure

```
backend/datasets/
├── oxford_backbone_training.py    # Stage 1 training (ACTIVE)
├── train_unet_stage1.py          # Alternative Stage 1 (needs fixing)
├── unet128.py                    # UNet-128 model definition
├── unet256.py                    # UNet-256 model definition (Stage 2)
├── embedding_dataset.py          # Dataset class for embeddings
├── export_embeddings.py          # CLIP embedding extraction
└── notify_job_status.py          # Slack notification system

scripts/
├── promote_weights.sh            # Production weight promotion
├── infer_shape_mvd.py            # Smoke test inference
└── setup_gpu_budget_alert.sh     # AWS cost monitoring
```

## Configuration Files

### Makefile Targets
```makefile
prep-embeddings:    # Extract CLIP embeddings locally
stage-1-unet:       # Train UNet-128 on T4 GPU  
stage-2-unet:       # Train UNet-256 with EMA
stage-3-full:       # Full Shape-MVD training
```

### Environment Variables
```bash
# Required for Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# AWS credentials for S3 and Secrets Manager
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

## Success Metrics

### Stage 1 Oxford Backbone
- ✅ Training completes 5 epochs without OOM
- ✅ Final validation loss < 0.5
- ✅ Weights uploaded to S3 successfully
- ✅ Smoke test generates valid STL files

### Stage 2 Enhanced UNet
- 🎯 Training completes without VRAM issues
- 🎯 EMA improves loss curve stability
- 🎯 Generated planters show improved quality

### Production Readiness
- 🎯 Inference API responds < 30 seconds
- 🎯 STL files print successfully without holes
- 🎯 Customer satisfaction ≥ 4/5 rating

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure all dependencies are in Modal image
2. **CUDA OOM**: Reduce batch size or enable gradient checkpointing
3. **S3 Upload Fails**: Verify AWS credentials and bucket permissions
4. **Modal Auth**: Run `modal token new` to refresh authentication

### Emergency Contacts

- **AI/ML Issues**: ML Team Lead
- **Infrastructure**: DevOps Team  
- **Production Outages**: On-call rotation
- **Slack Alerts**: #ops-alerts channel

## Recent Updates

**June 23, 2025**:
- ✅ Oxford backbone training active (Job: `ap-aAUGz3CuBS5kl1ukUREqmn`)
- ✅ Stage 2 UNet-256 configuration prepared and tested
- ✅ Slack notification system implemented
- ✅ Weight promotion automation completed
- ✅ Smoke test inference script ready
- 🎯 AWS cost monitoring script created

**Next Steps**:
1. Monitor Stage 1 training completion
2. Execute smoke test validation
3. Promote weights to production
4. Begin Stage 2 training preparation
