# PetPlantr Operations Drills

## Overview
This document tracks operational readiness drills to validate incident response procedures and system resilience.

## Drill Schedule

### Quarterly Drills (Required)
- **GPU VRAM Alert Drill:** Test alerting and auto-remediation
- **Canary Rollback Drill:** Validate blue-green deployment rollback
- **Security Breach Drill:** Test secrets leakage detection and response
- **Data Drift Drill:** Validate model retraining triggers

### Monthly Drills (Recommended)
- **Database Failover:** Test RDS failover procedures
- **Network Partition:** Test service mesh resilience
- **Cost Spike Alert:** Test cost monitoring and controls
- **Load Testing:** Validate auto-scaling under traffic spikes

## Drill Execution Log

### Drill #2025-08-001: GPU VRAM Alert
**Date:** 2025-08-04T14:30:00Z  
**Duration:** 45 minutes  
**Scenario:** Artificially trigger GPU VRAM usage > 6GB to test alerting pipeline  
**Executor:** John Doe (SRE)  
**Observer:** Jane Smith (Engineering Manager)  

#### Pre-Drill Setup
```bash
# Current configuration
kubectl get deployment petplantr-api -o yaml | grep -A 5 resources
# limits:
#   memory: "8Gi"
#   nvidia.com/gpu: 1
# requests:
#   memory: "4Gi"
#   nvidia.com/gpu: 1

# Baseline VRAM usage
kubectl exec deployment/petplantr-api -- nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
# 2048 MB (normal)
```

#### Drill Execution
```bash
# Step 1: Increase batch size to trigger high VRAM usage
kubectl set env deployment/petplantr-api MAX_BATCH_SIZE=32

# Step 2: Generate load to trigger larger batches
python load_test.py --target https://api.petplantr.com/v1/breed/detect \
                   --requests 100 --concurrency 10

# Step 3: Monitor VRAM usage
watch kubectl exec deployment/petplantr-api -- nvidia-smi
```

#### Results
- **Time to VRAM threshold breach:** 3 minutes 24 seconds
- **Time to Prometheus alert:** 5 minutes 12 seconds (2m rule + scrape interval)
- **Time to PagerDuty notification:** 5 minutes 45 seconds
- **Time to acknowledge alert:** 1 minute 30 seconds
- **Time to implement mitigation:** 2 minutes 15 seconds
- **Time to full recovery:** 8 minutes 30 seconds

#### Timeline
| Time | Event | Action |
|------|-------|--------|
| 14:30:00 | Drill start | Increased MAX_BATCH_SIZE to 32 |
| 14:33:24 | VRAM > 6GB | Threshold breached |
| 14:35:12 | Alert fired | Prometheus rule triggered |
| 14:35:45 | Page sent | PagerDuty notification sent |
| 14:37:15 | Alert ack | On-call engineer acknowledged |
| 14:39:30 | Fix applied | Reduced batch size to 8 |
| 14:42:00 | Recovery | VRAM back to normal levels |

#### Issues Identified
1. **Alert delay too long:** 5+ minutes to notification
2. **Missing auto-remediation:** No automatic batch size reduction
3. **Unclear runbook:** Steps not specific enough for new team members

#### Action Items
- [ ] **Reduce alert evaluation interval** from 2m to 1m (Owner: SRE team, Due: 2025-08-10)
- [ ] **Implement auto-remediation** for VRAM alerts (Owner: Platform team, Due: 2025-08-15)
- [ ] **Update runbook** with specific kubectl commands (Owner: Documentation team, Due: 2025-08-08)
- [ ] **Add VRAM usage to main dashboard** for better visibility (Owner: SRE team, Due: 2025-08-12)

#### Lessons Learned
1. Current alerting latency of 5+ minutes is too slow for GPU issues
2. Auto-remediation would have resolved this in <2 minutes
3. Need better real-time VRAM monitoring in Grafana
4. Runbook needs more specific commands for faster response

---

### Drill #2025-08-002: Canary Rollback
**Date:** 2025-08-04T16:00:00Z  
**Duration:** 30 minutes  
**Scenario:** Deploy faulty version to canary, trigger rollback  
**Executor:** Sarah Wilson (DevOps)  
**Observer:** Mike Chen (Release Manager)  

#### Pre-Drill Setup
```bash
# Current production version
kubectl get deployment petplantr-api -o yaml | grep image:
# image: petplantr/api:v2.1.0

# Baseline health metrics
curl https://api.petplantr.com/health
# {"status": "healthy", "version": "2.1.0"}
```

#### Drill Execution
```bash
# Step 1: Create faulty container (returns 500s)
docker build -t petplantr/api:drill-faulty -f Dockerfile.faulty .
docker push petplantr/api:drill-faulty

# Step 2: Deploy to canary (5% traffic)
kubectl set image deployment/petplantr-api-canary api=petplantr/api:drill-faulty

# Step 3: Wait for readiness probe failures
kubectl get pods -l app=petplantr-api-canary --watch

# Step 4: Monitor traffic shifting
kubectl logs -f deployment/istio-proxy -c istio-proxy | grep canary
```

#### Results
- **Time to canary deployment:** 2 minutes 15 seconds
- **Time to readiness probe failure:** 30 seconds
- **Time to traffic stop:** 1 minute 45 seconds (Istio circuit breaker)
- **Time to automated rollback:** 3 minutes 20 seconds
- **Time to full recovery:** 5 minutes 30 seconds

#### Timeline
| Time | Event | Action |
|------|-------|--------|
| 16:00:00 | Drill start | Deployed faulty image to canary |
| 16:02:15 | Canary deployed | Pod started, image pulled |
| 16:02:45 | Health check fail | Readiness probe returning 500 |
| 16:03:45 | Circuit breaker | Istio stopped routing to canary |
| 16:05:20 | Auto rollback | ArgoCD reverted to previous version |
| 16:07:30 | Full recovery | All traffic back to healthy pods |

#### Issues Identified
1. **Slow rollback trigger:** 3+ minutes to detect and rollback
2. **Limited canary monitoring:** No automated error rate detection
3. **Manual intervention needed:** ArgoCD required manual trigger

#### Action Items
- [ ] **Implement automated rollback** based on error rate >5% (Owner: Platform team, Due: 2025-08-20)
- [ ] **Reduce readiness probe interval** from 30s to 10s (Owner: SRE team, Due: 2025-08-12)
- [ ] **Add canary error rate alerts** to PagerDuty (Owner: SRE team, Due: 2025-08-15)
- [ ] **Configure ArgoCD auto-rollback** on health check failures (Owner: DevOps team, Due: 2025-08-18)

#### Lessons Learned
1. Current rollback time of 5+ minutes exceeds SLO target of <2 minutes
2. Circuit breaker worked well but rollback was too manual
3. Need automated error rate monitoring for canary deployments
4. Readiness probe intervals too long for fast failure detection

---

### Drill #2025-08-003: Secrets Leakage Scan
**Date:** 2025-08-04T17:30:00Z  
**Duration:** 15 minutes  
**Scenario:** Commit fake AWS credentials to test TruffleHog gate  
**Executor:** Alex Rodriguez (Security)  
**Observer:** Emma Thompson (DevSecOps)  

#### Pre-Drill Setup
```bash
# Create test branch
git checkout -b drill-secrets-test

# Current CI/CD security scan status
gh workflow list | grep security
# security-scan  active  1234567
```

#### Drill Execution
```bash
# Step 1: Add fake AWS credentials to test file
cat > test_secrets.py << 'EOF'
# Fake AWS credentials for testing
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def connect_to_aws():
    return boto3.client('s3', 
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
EOF

# Step 2: Commit and push to trigger CI
git add test_secrets.py
git commit -m "Test secrets for drill - DO NOT MERGE"
git push origin drill-secrets-test

# Step 3: Create PR to trigger security scan
gh pr create --title "DRILL: Secrets Test - DO NOT MERGE" \
             --body "Testing security scanning for secrets"
```

#### Results
- **Time to commit:** 30 seconds
- **Time to CI trigger:** 45 seconds
- **Time to TruffleHog scan:** 2 minutes 15 seconds
- **Time to CI failure:** 2 minutes 30 seconds
- **Time to PR block:** 2 minutes 45 seconds

#### Timeline
| Time | Event | Action |
|------|-------|--------|
| 17:30:00 | Drill start | Created test file with fake secrets |
| 17:30:30 | Commit made | Committed fake AWS credentials |
| 17:30:45 | CI triggered | GitHub Actions workflow started |
| 17:32:15 | TruffleHog scan | Security scanner detected secrets |
| 17:32:30 | CI failed | Build marked as failed |
| 17:32:45 | PR blocked | Merge prevention rule activated |

#### Issues Identified
✅ **All systems working correctly!**
1. TruffleHog detected fake credentials as expected
2. CI failed with clear error message
3. PR was blocked from merging
4. Security team received notification

#### Action Items
- [ ] **Document drill results** in security playbook (Owner: Security team, Due: 2025-08-08)
- [ ] **Test with different secret types** (API keys, tokens) in next drill (Owner: Security team, Due: 2025-11-04)

#### Lessons Learned
1. Security scanning is working effectively
2. Clear error messages help developers understand issues
3. 2+ minute scan time is acceptable for this gate
4. Need to test other secret types in future drills

---

### Drill #2025-08-004: Data Drift Detection
**Date:** 2025-08-04T19:00:00Z  
**Duration:** 60 minutes  
**Scenario:** Inject mixed-breed photos to trigger drift detection  
**Executor:** Maria Garcia (ML Engineer)  
**Observer:** David Kim (Data Scientist)  

#### Pre-Drill Setup
```bash
# Current model performance baseline
python scripts/validate_model.py --dataset test_set_v2.1.0
# Accuracy: 95.2%, F1: 0.948, Precision: 0.951

# Prepare mixed-breed injection dataset
aws s3 sync s3://petplantr-test-data/mixed-breeds/ ./drill_data/
# Downloaded 100 mixed-breed images
```

#### Drill Execution
```bash
# Step 1: Run baseline shadow validation
python scripts/shadow_validation.py --baseline --samples 1000

# Step 2: Inject mixed-breed photos into validation stream
python scripts/inject_test_data.py --source ./drill_data/ --count 100

# Step 3: Run drift detection
python scripts/detect_drift.py --threshold 0.05 --samples 1100

# Step 4: Monitor for drift alerts
tail -f /var/log/petplantr/drift_monitor.log
```

#### Results
- **Time to inject test data:** 5 minutes
- **Time to drift detection:** 15 minutes (next validation cycle)
- **KL divergence measured:** 0.087 (threshold: 0.05)
- **Time to alert:** 16 minutes 30 seconds
- **Time to Jira ticket creation:** 17 minutes 15 seconds

#### Timeline
| Time | Event | Measurement |
|------|-------|-------------|
| 19:00:00 | Drill start | Baseline KL divergence: 0.02 |
| 19:05:00 | Data injected | 100 mixed-breed images added |
| 19:15:00 | Drift detected | KL divergence: 0.087 |
| 19:16:30 | Alert fired | Slack notification sent |
| 19:17:15 | Ticket created | Jira ticket AUTO-1234 opened |
| 19:20:00 | Manual review | Data scientist confirmed drift |

#### Drift Metrics
```yaml
drift_analysis:
  baseline_accuracy: 95.2%
  post_injection_accuracy: 88.7%
  accuracy_drop: 6.5%
  kl_divergence: 0.087
  confidence_shift: -0.15
  false_positive_increase: 3.2%
```

#### Issues Identified
1. **Slow detection cycle:** 15 minutes is too long for production
2. **No automated mitigation:** Required manual intervention
3. **Alert fatigue risk:** Too sensitive to small data shifts

#### Action Items
- [ ] **Reduce validation cycle** from 15m to 5m (Owner: ML team, Due: 2025-08-12)
- [ ] **Implement staged alerts** (warning at 0.03, critical at 0.05) (Owner: ML team, Due: 2025-08-15)
- [ ] **Add auto-retraining trigger** for KL > 0.08 (Owner: ML Platform, Due: 2025-08-25)
- [ ] **Create drift analysis dashboard** (Owner: Data team, Due: 2025-08-20)

#### Lessons Learned
1. Drift detection is working but too slow for real-time response
2. Need graduated alerting to reduce false positives
3. Automated mitigation would improve response time
4. Better visualization needed for drift analysis

---

## Drill Performance Summary

### Response Time Metrics (Q3 2025)
| Drill Type | Target Response | Actual Response | Status |
|------------|----------------|-----------------|---------|
| GPU VRAM Alert | <3 minutes | 5m 45s | ⚠️ NEEDS IMPROVEMENT |
| Canary Rollback | <2 minutes | 5m 30s | ⚠️ NEEDS IMPROVEMENT |
| Secrets Scan | <5 minutes | 2m 45s | ✅ MEETS TARGET |
| Data Drift | <10 minutes | 16m 30s | ⚠️ NEEDS IMPROVEMENT |

### Key Improvement Areas
1. **Alerting Latency:** Reduce from 5+ minutes to <3 minutes
2. **Auto-Remediation:** Implement for GPU and rollback scenarios
3. **Monitoring Granularity:** Increase from 15-minute to 5-minute cycles
4. **Runbook Clarity:** Add specific commands and decision trees

## Upcoming Drills (Q4 2025)

### Scheduled Drills
- **2025-10-15:** Database failover drill
- **2025-11-04:** Enhanced secrets detection (API keys, tokens)
- **2025-11-15:** Load testing with traffic spike simulation
- **2025-12-03:** Full disaster recovery simulation

### New Drill Scenarios
- **Kubernetes node failure:** Test pod rescheduling and recovery
- **S3 outage simulation:** Test model loading fallback procedures  
- **Cost spike alert:** Test budget controls and scaling limits
- **Model corruption:** Test backup restore and validation

## Drill Process Improvements

### Before Each Drill
- [ ] Review previous drill lessons learned
- [ ] Update runbooks with recent changes
- [ ] Notify stakeholders 24 hours in advance
- [ ] Prepare rollback plans for drill failures

### During Each Drill
- [ ] Follow scripted scenario exactly
- [ ] Document all timestamps and actions
- [ ] Record any deviations from expected behavior
- [ ] Take screenshots of relevant dashboards

### After Each Drill
- [ ] Conduct immediate hot wash (15 minutes)
- [ ] Update this document within 24 hours
- [ ] Create action items with owners and due dates
- [ ] Schedule follow-up review in 1 week

## Contact Information

### Drill Coordinators
- **SRE Team Lead:** John Doe (john.doe@petplantr.com)
- **Security Lead:** Alex Rodriguez (alex.rodriguez@petplantr.com)
- **ML Engineering:** Maria Garcia (maria.garcia@petplantr.com)
- **DevOps Lead:** Sarah Wilson (sarah.wilson@petplantr.com)

### Escalation
- **Engineering Manager:** Jane Smith (#eng-escalation)
- **VP Engineering:** Mike Johnson (#exec-escalation)
- **Incident Commander:** On-call rotation (#incident-response)
