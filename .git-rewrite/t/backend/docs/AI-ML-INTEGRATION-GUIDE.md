# PetPlantr AI/ML Modeling Pipeline Integration Guide

## Overview

This document outlines how to integrate the high-fidelity AI/ML modeling pipeline into your existing PetPlantr backend infrastructure.

## Current vs. Enhanced Pipeline

### Current Simple Pipeline (Beta-0)
```
Photos → generateSTL (mock) → processSTL (cleanup) → notifyCustomer
```

### Enhanced AI/ML Pipeline (Production)
```
Photos → Feature Extraction → Depth Estimation → Mesh Reconstruction → Planter Geometry → Mesh Cleanup → notifyCustomer
```

## Integration Steps

### 1. Deploy Infrastructure Changes

The modeling pipeline requires additional AWS resources:

```bash
# Deploy the updated serverless configuration
npx dotenv-cli -e .env -- npx serverless deploy

# This will create:
# - New IAM role: ModelingPipelineRole
# - New Lambda function: modelingPipeline
# - Updated S3 bucket permissions
```

### 2. Create Additional S3 Buckets

```bash
# Create processing and model storage buckets
aws s3 mb s3://petplantr-processing-dev
aws s3 mb s3://petplantr-models-dev

# Set lifecycle policies for temp processing files
aws s3api put-bucket-lifecycle-configuration \
  --bucket petplantr-processing-dev \
  --lifecycle-configuration file://config/s3-lifecycle-processing.json
```

### 3. Update Step Functions Workflow

Replace the current simple `generateSTL` step with the multi-stage pipeline:

```json
{
  "FeatureExtraction": {
    "Type": "Task",
    "Resource": "${ModelingPipelineLambdaFunction}",
    "Parameters": {
      "stage": "featureExtraction",
      "orderId.$": "$.orderId",
      "userId.$": "$.userId", 
      "photoUrls.$": "$.photoUrls"
    },
    "Next": "DepthEstimation"
  },
  "DepthEstimation": {
    "Type": "Task",
    "Resource": "${ModelingPipelineLambdaFunction}",
    "Parameters": {
      "stage": "depthEstimation",
      "orderId.$": "$.orderId",
      "userId.$": "$.userId",
      "previousStageOutput.$": "$.outputPath"
    },
    "Next": "MeshReconstruction"
  }
  // ... continue for all stages
}
```

### 4. Model Deployment

Upload trained models to S3:

```bash
# Upload ViT feature extraction model
aws s3 cp vit-pet-faces-v1.0.pth s3://petplantr-models-dev/feature-extraction/

# Upload Shape-MVD reconstruction model  
aws s3 cp shape-mvd-pets-v1.0.pth s3://petplantr-models-dev/mesh-reconstruction/

# Update model paths in config/modeling-pipeline.json
```

### 5. GPU Compute Setup

For production deployment, consider:

- **AWS Batch**: For GPU-intensive model inference
- **SageMaker Endpoints**: For real-time model serving
- **ECS with GPU**: For containerized model execution

Example Batch job definition:
```json
{
  "jobDefinitionName": "petplantr-modeling-gpu",
  "type": "container",
  "containerProperties": {
    "image": "petplantr/modeling-pipeline:latest",
    "vcpus": 4,
    "memory": 32768,
    "jobRoleArn": "arn:aws:iam::ACCOUNT:role/PetPlantr-BatchJobRole",
    "resourceRequirements": [
      {
        "type": "GPU",
        "value": "1"
      }
    ]
  }
}
```

## Configuration Management

### Environment-Specific Settings

```yaml
# config/modeling-pipeline-dev.json
{
  "modelingPipeline": {
    "stages": {
      "featureExtraction": {
        "enabled": true,
        "compute": {
          "instanceType": "g4dn.xlarge"  # Dev: smaller instance
        }
      }
    }
  }
}

# config/modeling-pipeline-prod.json
{
  "modelingPipeline": {
    "stages": {
      "featureExtraction": {
        "enabled": true,
        "compute": {
          "instanceType": "p3.2xlarge"  # Prod: powerful GPU
        }
      }
    }
  }
}
```

### Performance Monitoring

Add CloudWatch metrics for each pipeline stage:

```typescript
// In modelingPipeline.ts
await cloudwatch.putMetricData({
  Namespace: 'PetPlantr/ModelingPipeline',
  MetricData: [{
    MetricName: 'ProcessingTime',
    Dimensions: [
      { Name: 'Stage', Value: stage },
      { Name: 'Environment', Value: process.env.STAGE }
    ],
    Value: processingTimeSeconds,
    Unit: 'Seconds'
  }]
});
```

## Testing Strategy

### 1. Beta-0: Keep Simple Pipeline

For Beta-0 launch, continue using the mock `generateSTL` function while you:
- Collect real pet photos from beta users
- Train models on diverse pet dataset
- Optimize pipeline performance

### 2. Beta-1: Gradual Rollout

- Deploy AI pipeline alongside existing simple pipeline
- A/B test: 10% of orders use AI pipeline, 90% use simple
- Monitor quality metrics and processing times
- Gradually increase AI pipeline percentage

### 3. Production: Full AI Pipeline

Once validated:
- Switch 100% of orders to AI pipeline
- Remove simple mock generateSTL function
- Monitor at scale with full observability

## Cost Optimization

### Compute Costs
- **Lambda**: $0.20/GB-second + $0.0000166667/request
- **GPU instances**: g4dn.xlarge ~$0.50/hour, p3.2xlarge ~$3.06/hour
- **Storage**: S3 standard ~$0.023/GB/month

### Optimization Strategies
1. **Batch Processing**: Group multiple orders together
2. **Spot Instances**: Use EC2 Spot for training/batch inference
3. **Model Optimization**: Quantization, pruning for faster inference
4. **Caching**: Cache model outputs for similar pet features

## Migration Timeline

### Week 1-2: Infrastructure
- [ ] Deploy updated serverless configuration
- [ ] Create additional S3 buckets
- [ ] Set up GPU compute environment

### Week 3-4: Model Training
- [ ] Collect and curate pet photo dataset
- [ ] Train ViT feature extraction model
- [ ] Fine-tune Shape-MVD reconstruction model
- [ ] Validate model outputs

### Week 5-6: Integration Testing
- [ ] Deploy models to S3
- [ ] Test end-to-end pipeline
- [ ] Performance optimization
- [ ] Quality validation

### Week 7-8: Beta Testing
- [ ] A/B test with small percentage of traffic
- [ ] Monitor quality and performance metrics
- [ ] Iterate based on results

### Week 9+: Production Rollout
- [ ] Gradual increase to 100% AI pipeline
- [ ] Full monitoring and alerting
- [ ] Continuous model improvement

## Support and Troubleshooting

### Common Issues

1. **GPU Memory Errors**: Reduce batch size or model resolution
2. **Long Processing Times**: Check instance types and model optimization
3. **Quality Issues**: Retrain models with more diverse data
4. **Cost Overruns**: Implement batch processing and spot instances

### Monitoring Commands

```bash
# Check modeling pipeline logs
aws logs filter-log-events \
  --log-group-name '/aws/lambda/petplantr-pipeline-dev-modelingPipeline' \
  --start-time $(date -v-1H +%s)000

# Monitor processing times
aws cloudwatch get-metric-statistics \
  --namespace 'PetPlantr/ModelingPipeline' \
  --metric-name 'ProcessingTime' \
  --start-time $(date -v-1H) \
  --end-time $(date) \
  --period 300 \
  --statistics Average
```

This integration maintains your current Beta-0 functionality while providing a clear path to production-grade AI/ML capabilities.
