# PetPlantr Breed API Runbook

## Emergency Response Guide

### SEV-1 Template

```yaml
incident_type: SEV-1
service: petplantr-breed-api
description: "Critical service degradation affecting production users"
initial_response_time: "< 5 minutes"
escalation_time: "15 minutes if not resolved"
communication_channel: "#incident-response"
```

## Critical Issues & Immediate Actions

### 🚨 API Completely Down (HTTP 5xx)
**Symptom:** Health check returning 500/503, no successful requests

**Immediate Actions (< 2 minutes):**
```bash
# 1. Check service status
kubectl get pods -l app=petplantr-api
kubectl describe pod <failing-pod>

# 2. Emergency scaling to zero (stops bad pods)
kubectl scale deployment petplantr-api --replicas=0

# 3. Rollback to last known good version
kubectl rollout undo deployment/petplantr-api

# 4. Scale back up
kubectl scale deployment petplantr-api --replicas=3

# 5. Verify recovery
curl -f https://api.petplantr.com/health
```

**Investigation Steps:**
1. Check recent deployments: `kubectl rollout history deployment/petplantr-api`
2. Review application logs: `kubectl logs -l app=petplantr-api --tail=100`
3. Check resource constraints: `kubectl top pods`
4. Validate configuration: `kubectl get configmap petplantr-config -o yaml`

### 🐌 High Latency (P95 > 1 second)
**Symptom:** Inference requests taking > 1000ms, user complaints

**Immediate Actions (< 5 minutes):**
```bash
# 1. Check GPU VRAM usage
kubectl exec -it deployment/petplantr-api -- nvidia-smi

# 2. Reduce batch size temporarily
kubectl set env deployment/petplantr-api BATCH_SIZE=1

# 3. Scale up replicas for load distribution
kubectl scale deployment petplantr-api --replicas=6

# 4. Monitor improvement
watch 'curl -w "%{time_total}" https://api.petplantr.com/v1/breed/detect'
```

**Root Cause Analysis:**
- GPU memory exhaustion
- Model loading delays
- Input image preprocessing bottleneck
- Network congestion

### 🧠 Model Accuracy Drop (< 90%)
**Symptom:** Breed predictions showing low confidence or incorrect results

**Immediate Actions (< 10 minutes):**
```bash
# 1. Run model validation test
bash test_enhanced_system.sh --model-validation-only

# 2. Check model file integrity
kubectl exec deployment/petplantr-api -- sha256sum /app/weights/model.pth

# 3. Verify preprocessing pipeline
kubectl logs -l app=petplantr-api | grep "preprocessing"

# 4. If corrupted, reload from backup
kubectl create job model-reload --from=cronjob/model-sync
```

**Escalation Criteria:**
- Model weights corrupted
- Training data contamination detected
- CUDA/PyTorch version mismatch

### 🔥 GPU VRAM Exhaustion (> 20GB)
**Symptom:** CUDA out of memory errors, inference failures

**Immediate Actions (< 3 minutes):**
```bash
# 1. Emergency batch size reduction
kubectl set env deployment/petplantr-api BATCH_SIZE=1 MAX_BATCH_SIZE=4

# 2. Clear GPU memory cache
kubectl exec deployment/petplantr-api -- python -c "import torch; torch.cuda.empty_cache()"

# 3. Restart pods to clear memory leaks
kubectl rollout restart deployment/petplantr-api

# 4. Monitor VRAM usage
kubectl exec deployment/petplantr-api -- watch nvidia-smi
```

### 💾 High Memory Usage (> 8GB)
**Symptom:** Pod restarts due to OOMKilled, slow response times

**Immediate Actions:**
```bash
# 1. Check memory usage by pod
kubectl top pods -l app=petplantr-api

# 2. Increase memory limits temporarily
kubectl patch deployment petplantr-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"12Gi"}}}]}}}}'

# 3. Clear application caches
kubectl exec deployment/petplantr-api -- python -c "
import gc
gc.collect()
"

# 4. Scale out instead of up
kubectl scale deployment petplantr-api --replicas=5
```

## Investigation Playbooks

### Performance Degradation
1. **Metrics Review:**
   ```bash
   # Check Prometheus metrics
   curl http://prometheus:9090/api/v1/query?query=rate(inference_latency_seconds_sum[5m])/rate(inference_latency_seconds_count[5m])
   
   # GPU utilization
   curl http://prometheus:9090/api/v1/query?query=dcgm_gpu_utilization
   ```

2. **Log Analysis:**
   ```bash
   # Recent errors
   kubectl logs -l app=petplantr-api --since=10m | grep ERROR
   
   # Inference timing
   kubectl logs -l app=petplantr-api | grep "inference_time"
   ```

3. **Resource Analysis:**
   ```bash
   kubectl describe nodes
   kubectl top nodes
   kubectl get events --sort-by=.metadata.creationTimestamp
   ```

### Data Pipeline Issues
1. **Input Validation:**
   ```bash
   # Check image preprocessing
   kubectl exec deployment/petplantr-api -- python -c "
   from PIL import Image
   import requests
   img = Image.open(requests.get('https://example.com/test.jpg', stream=True).raw)
   print(f'Image size: {img.size}, mode: {img.mode}')
   "
   ```

2. **Model Loading:**
   ```bash
   # Verify model files
   kubectl exec deployment/petplantr-api -- ls -la /app/weights/
   kubectl exec deployment/petplantr-api -- python -c "
   import torch
   model = torch.load('/app/weights/model.pth')
   print('Model loaded successfully')
   "
   ```

## Monitoring & Alerting

### Critical Dashboards
- **Grafana Inference Dashboard:** https://grafana.petplantr.com/d/inference
- **System Health Dashboard:** https://grafana.petplantr.com/d/health
- **GPU Monitoring Dashboard:** https://grafana.petplantr.com/d/gpu

### Alert Thresholds
```yaml
alerts:
  high_latency:
    threshold: "p95 > 1000ms"
    duration: "2 minutes"
    severity: "warning"
  
  api_down:
    threshold: "success_rate < 50%"
    duration: "1 minute"
    severity: "critical"
  
  gpu_vram_high:
    threshold: "vram_usage > 18GB"
    duration: "3 minutes"
    severity: "warning"
  
  model_accuracy_low:
    threshold: "accuracy < 90%"
    duration: "5 minutes"
    severity: "warning"
```

## Escalation Procedures

### Level 1: On-Call Engineer (0-15 minutes)
- Follow immediate action runbooks
- Implement temporary fixes
- Gather initial diagnostics

### Level 2: Senior SRE (15-30 minutes)
- Deep dive into root cause
- Coordinate with development team
- Implement permanent fixes

### Level 3: Engineering Manager + Product (30+ minutes)
- Customer communication
- Business impact assessment
- Post-incident review planning

## Communication Templates

### Incident Declaration
```
🚨 SEV-1 INCIDENT DECLARED
Service: PetPlantr Breed API
Impact: [High latency / Complete outage / Accuracy degradation]
User Impact: [X% of requests affected]
ETA: [Under investigation / Fix in progress / Testing solution]
War Room: #incident-[timestamp]
```

### Status Updates (every 15 minutes)
```
UPDATE [HH:MM]: 
Actions Taken: [Brief summary]
Current Status: [What's happening now]
Next Steps: [What we're doing next]
ETA: [Updated estimate]
```

### Resolution Notice
```
✅ RESOLVED [HH:MM]:
Root Cause: [Brief explanation]
Fix Applied: [What was done]
Prevention: [How we'll prevent recurrence]
Post-Mortem: [Link when available]
```

## Recovery Validation

### Post-Incident Checklist
- [ ] API health check passes
- [ ] Inference accuracy validation
- [ ] Performance benchmarks meet SLOs
- [ ] All monitoring alerts cleared
- [ ] Customer impact assessment complete
- [ ] Incident timeline documented
- [ ] Post-mortem scheduled

### Validation Commands
```bash
# Full system validation
bash test_enhanced_system.sh --environment production --comprehensive

# Performance validation  
bash launch_status_report.sh --environment production --slo-check

# Model accuracy validation
python validate_model_accuracy.py --threshold 0.95
```

## Contact Information

### Primary Contacts
- **On-Call Engineer:** #petplantr-oncall (Slack)
- **Engineering Manager:** @john.doe (Slack)
- **Product Manager:** @jane.smith (Slack)
- **Infrastructure Team:** #infra-support (Slack)

### External Contacts
- **AWS Support:** [Case Portal](https://console.aws.amazon.com/support/)
- **NVIDIA Support:** [Developer Portal](https://developer.nvidia.com/support)
- **PagerDuty:** [Incidents Dashboard](https://petplantr.pagerduty.com)

## Additional Resources

### Documentation
- [Architecture Overview](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Performance Tuning](./PERFORMANCE_TUNING.md)

### Tools & Scripts
- [Emergency Scripts](../scripts/emergency/)
- [Diagnostic Tools](../scripts/diagnostics/)
- [Recovery Procedures](../scripts/recovery/)

### Historical Incidents
- [Incident Database](https://petplantr.atlassian.net/incidents)
- [Post-Mortem Archive](./incidents/)
- [Lessons Learned](./LESSONS_LEARNED.md)
