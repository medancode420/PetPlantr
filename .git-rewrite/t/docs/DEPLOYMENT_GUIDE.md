# PetPlantr Deployment Guide

## Overview
This guide provides step-by-step instructions for routine PetPlantr releases using the automated launch pipeline.

## Prerequisites

### Required Tools
- Docker 20.10+
- kubectl 1.24+
- AWS CLI v2
- Python 3.9+
- Bash 5.0+

### Required Access
- GitHub repository write access
- AWS ECR push permissions (via OIDC)
- ECS deployment permissions
- Grafana/Prometheus dashboard access

### Environment Setup
```bash
# Clone repository
git clone https://github.com/your-org/petplantr.git
cd petplantr

# Verify prerequisites
./check_environment.py

# Configure AWS OIDC (one-time setup)
aws configure set region us-west-2
```

## Launch Automation Flow

### 1. Pre-Deployment Validation
```bash
# Run comprehensive validation
bash ultimate_launch_automation.sh --environment staging

# Generate launch evidence report
bash launch_gate_checklist.sh --report launch_evidence_$(date +%Y%m%d).html
```

### 2. Staging Deployment
```bash
# Deploy to staging environment
bash deploy_enhanced.sh --environment staging --dry-run
bash deploy_enhanced.sh --environment staging

# Validate staging deployment
bash test_enhanced_system.sh --environment staging --slo-strict
```

### 3. Production Canary Deployment
```bash
# Start with 5% traffic canary
bash deploy_enhanced.sh --environment production --canary 5

# Monitor canary for 30 minutes
bash launch_status_report.sh --environment production --watch

# Verify SLO compliance
# - Latency P95 < 500ms
# - Accuracy ≥ 95%
# - Error rate < 1%
# - GPU VRAM < 5GB
```

### 4. Full Production Rollout
```bash
# If canary is healthy, proceed with full rollout
bash deploy_enhanced.sh --environment production --canary 100

# Continue monitoring for 2 hours
bash advanced_operational_care.sh --monitor --duration 120m
```

## Canary Deployment & Rollback

### Canary Traffic Splitting
```bash
# ECS Service Configuration
aws ecs update-service \
  --cluster petplantr-production \
  --service petplantr-api-canary \
  --desired-count 1

aws ecs update-service \
  --cluster petplantr-production \
  --service petplantr-api-stable \
  --desired-count 9
```

### Automated Rollback Triggers
- P95 latency > 600ms for 2 minutes
- Error rate > 2% for 1 minute
- GPU VRAM > 6GB for 3 minutes
- Manual trigger via Slack/PagerDuty

### Manual Rollback Procedure
```bash
# Immediate rollback (< 60 seconds)
kubectl rollout undo deployment/petplantr-api

# Or using ECS
aws ecs update-service \
  --cluster petplantr-production \
  --service petplantr-api \
  --task-definition petplantr-api:PREVIOUS_REVISION

# Verify rollback
curl -f https://api.petplantr.com/health
bash test_enhanced_system.sh --environment production --quick
```

## Post-Deploy Health Checks

### Immediate Checks (0-5 minutes)
```bash
# API health check
curl -f https://api.petplantr.com/health

# Smoke test inference
curl -X POST https://api.petplantr.com/v1/breed/detect \
  -F "file=@test_images/golden_retriever.jpg"

# Check Prometheus metrics
curl https://api.petplantr.com/metrics | grep inference_latency
```

### Extended Monitoring (5-30 minutes)
```bash
# Run comprehensive test suite
bash test_enhanced_system.sh --environment production --extended

# Monitor key metrics
# - Request rate
# - Error rate
# - Response times
# - GPU utilization
# - Memory usage
```

### Long-term Monitoring (30+ minutes)
- Grafana dashboard monitoring
- PagerDuty alert validation
- Model drift detection
- Cost optimization review

## Troubleshooting

### Common Issues

#### High Latency
1. Check GPU VRAM usage
2. Review batch size configuration
3. Verify model loading time
4. Check network connectivity

#### Model Accuracy Drop
1. Validate input preprocessing
2. Check model weights integrity
3. Review recent training data
4. Verify CUDA/PyTorch versions

#### Container Crashes
1. Check memory limits
2. Review GPU driver compatibility
3. Validate environment variables
4. Check model file permissions

### Emergency Contacts
- On-call Engineer: #petplantr-oncall
- Release Captain: #petplantr-releases
- Infrastructure: #infra-alerts

## Release Checklist

- [ ] All CI/CD checks pass
- [ ] Security scan completed (no HIGH/CRITICAL)
- [ ] Performance benchmarks meet SLOs
- [ ] Launch gate checklist passes
- [ ] Staging deployment validated
- [ ] Canary deployment healthy
- [ ] Full production rollout completed
- [ ] Post-deploy monitoring active
- [ ] Release notes published
- [ ] Stakeholders notified

## Environment-Specific Configurations

### Staging
- Single replica deployment
- Relaxed SLO thresholds
- Enhanced logging enabled
- Test data injection allowed

### Production
- Multi-replica with auto-scaling
- Strict SLO enforcement
- Optimized logging levels
- Production data only

## Monitoring & Alerting

### Key Dashboards
- [Inference Performance](https://grafana.petplantr.com/d/inference)
- [System Health](https://grafana.petplantr.com/d/health)
- [Business Metrics](https://grafana.petplantr.com/d/business)

### Critical Alerts
- API Down (immediate page)
- High Error Rate (immediate page)
- High Latency (page after 2 minutes)
- GPU VRAM Critical (page after 3 minutes)

## Maintenance Windows

### Weekly Maintenance
- Dependency updates
- Model cache cleanup
- Log rotation
- Performance optimization

### Monthly Maintenance
- Security patches
- Capacity planning review
- Cost optimization analysis
- Disaster recovery testing
