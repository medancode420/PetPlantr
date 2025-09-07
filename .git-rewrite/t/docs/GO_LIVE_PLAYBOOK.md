# PetPlantr Go-Live Playbook
## 24-Hour Launch Window Execution Guide

### Pre-Launch Checklist (T-minus 24h → 0)

| T-minus | Owner | Command / Action | Evidence Artifact |
|---------|-------|------------------|-------------------|
| **-24h** | ML-Eng | `bash one_hour_finetune.sh --wandb-tag release-v1.0.0` | W&B run link in OPERATIONS_DRILLS.md |
| **-12h** | SRE | `bash final_launch_validation.sh --report preflight.html` | Pre-flight HTML report attached to Release draft |
| **-6h** | DevOps | `terraform apply -var image_tag=<sha>` | TF plan & apply logs in evidence report |
| **-2h** | Release Captain | `bash ultimate_launch_automation.sh --canary 5` | Canary evidence in evidence_<sha>.html |
| **0** | RC + Stakeholders | Promote traffic to 100% if error rate < 1% & p95 latency < 0.5s | Grafana snapshot link |
| **+1h** | Release Captain | Close Release → tag v1.0.0 | Git tag; changelog updated |
| **+24h** | Product Manager | Post-launch retrospective | Notes in OPERATIONS_DRILLS.md |

---

## T-minus 24 Hours: Model Fine-Tuning

**Owner:** ML Engineering  
**Duration:** 1 hour  
**Prerequisites:** Latest dataset version, clean W&B project

### Execution Steps
```bash
# 1. Verify dataset integrity
python scripts/validate_dataset.py --version v2.1.0

# 2. Start fine-tuning with release tag
bash one_hour_finetune.sh --wandb-tag release-v1.0.0 --validation-strict

# 3. Record W&B run details
echo "W&B Run: https://wandb.ai/petplantr/breed-detection/runs/$(cat .wandb_run_id)" >> docs/OPERATIONS_DRILLS.md
```

### Success Criteria
- [ ] Training completes with >95% validation accuracy
- [ ] No significant accuracy regression vs previous model
- [ ] W&B artifacts uploaded successfully
- [ ] Model weights pushed to S3 with versioning

---

## T-minus 12 Hours: Pre-Flight Validation

**Owner:** SRE Team  
**Duration:** 45 minutes  
**Prerequisites:** All automation scripts tested, staging environment ready

### Execution Steps
```bash
# 1. Run comprehensive pre-flight validation
bash final_launch_validation.sh --report preflight_$(date +%Y%m%d_%H%M).html

# 2. Generate launch evidence package
bash launch_gate_checklist.sh --report launch_evidence_$(git rev-parse --short HEAD).html

# 3. Attach reports to GitHub Release draft
gh release create v1.0.0-rc \
  --title "PetPlantr v1.0.0 Release Candidate" \
  --notes-file RELEASE_NOTES.md \
  --draft \
  preflight_*.html launch_evidence_*.html
```

### Success Criteria
- [ ] All 17 launch gates pass
- [ ] Security scan shows 0 HIGH/CRITICAL vulnerabilities
- [ ] Performance benchmarks meet SLO targets
- [ ] HTML evidence reports generated and attached

---

## T-minus 6 Hours: Infrastructure Deployment

**Owner:** DevOps Team  
**Duration:** 30 minutes  
**Prerequisites:** Terraform state backed up, AWS credentials configured

### Execution Steps
```bash
# 1. Generate deployment plan
terraform plan -var="image_tag=$(git rev-parse HEAD)" \
              -var="environment=production" \
              -out=production.tfplan

# 2. Apply infrastructure changes
terraform apply production.tfplan 2>&1 | tee terraform_apply_$(date +%Y%m%d_%H%M).log

# 3. Verify infrastructure health
bash infrastructure_health_check.sh --environment production
```

### Success Criteria
- [ ] Terraform apply completes successfully
- [ ] All ECS services report healthy
- [ ] Load balancer health checks pass
- [ ] Monitoring stack operational

---

## T-minus 2 Hours: Canary Deployment

**Owner:** Release Captain  
**Duration:** 1 hour  
**Prerequisites:** Infrastructure deployed, monitoring active

### Execution Steps
```bash
# 1. Deploy canary with 5% traffic
bash ultimate_launch_automation.sh --canary 5 \
                                   --report canary_evidence_$(git rev-parse --short HEAD).html

# 2. Monitor canary metrics for 30 minutes
bash monitor_canary_deployment.sh --duration 30m --alert-threshold 1%

# 3. Validate canary performance
bash validate_canary_slos.sh --error-rate-max 1 --latency-p95-max 500
```

### Success Criteria
- [ ] Canary deployment successful
- [ ] Error rate < 1% for 30 minutes
- [ ] P95 latency < 500ms
- [ ] No critical alerts fired
- [ ] GPU VRAM usage < 5GB

---

## T-0: Full Production Rollout

**Owner:** Release Captain + Stakeholders  
**Duration:** 15 minutes  
**Prerequisites:** Canary validation passed, stakeholder approval

### Execution Steps
```bash
# 1. Capture pre-rollout Grafana snapshot
curl -X POST "https://grafana.petplantr.com/api/snapshots" \
     -H "Authorization: Bearer $GRAFANA_API_KEY" \
     -d '{"dashboard":{"uid":"petplantr_gpu_latency"},"name":"Pre-Rollout Baseline"}'

# 2. Promote canary to 100% traffic
bash ultimate_launch_automation.sh --canary 100

# 3. Capture post-rollout snapshot
curl -X POST "https://grafana.petplantr.com/api/snapshots" \
     -H "Authorization: Bearer $GRAFANA_API_KEY" \
     -d '{"dashboard":{"uid":"petplantr_gpu_latency"},"name":"Post-Rollout Production"}'
```

### Go/No-Go Decision Matrix
| Metric | Threshold | Current | Status |
|--------|-----------|---------|--------|
| Error Rate | < 1% | ___ % | ⏳ |
| P95 Latency | < 500ms | ___ ms | ⏳ |
| GPU VRAM | < 5GB | ___ GB | ⏳ |
| Model Accuracy | > 95% | ___ % | ⏳ |

**Decision:** ✅ GO / ❌ NO-GO

---

## T+1 Hour: Release Closure

**Owner:** Release Captain  
**Duration:** 15 minutes  
**Prerequisites:** Production rollout stable

### Execution Steps
```bash
# 1. Tag final release
git tag -a v1.0.0 -m "PetPlantr v1.0.0 - Production Launch"
git push origin v1.0.0

# 2. Promote GitHub release from draft
gh release edit v1.0.0-rc --tag v1.0.0 --latest

# 3. Update changelog
echo "## [1.0.0] - $(date +%Y-%m-%d)" >> CHANGELOG.md
echo "### Added" >> CHANGELOG.md
echo "- Production launch with 95%+ breed detection accuracy" >> CHANGELOG.md
```

### Success Criteria
- [ ] Git tag created and pushed
- [ ] GitHub release published
- [ ] Changelog updated
- [ ] Stakeholder notifications sent

---

## T+24 Hours: Post-Launch Retrospective

**Owner:** Product Manager  
**Duration:** 1 hour  
**Prerequisites:** 24 hours of production data

### Agenda
1. **Metrics Review** (15 min)
   - Launch timeline adherence
   - Performance vs SLO targets
   - Customer feedback summary

2. **What Went Well** (15 min)
   - Process improvements
   - Team coordination
   - Technical execution

3. **Areas for Improvement** (15 min)
   - Timeline deviations
   - Unexpected issues
   - Process gaps

4. **Action Items** (15 min)
   - Process improvements for next release
   - Technical debt priorities
   - Monitoring enhancements

### Documentation
```bash
# Record retrospective notes
echo "## Post-Launch Retrospective $(date +%Y-%m-%d)" >> docs/OPERATIONS_DRILLS.md
echo "### Launch Timeline Performance" >> docs/OPERATIONS_DRILLS.md
echo "- Actual vs planned: ___ minutes deviation" >> docs/OPERATIONS_DRILLS.md
echo "### Key Metrics First 24h" >> docs/OPERATIONS_DRILLS.md
echo "- Total requests: ___" >> docs/OPERATIONS_DRILLS.md
echo "- Average accuracy: ___%" >> docs/OPERATIONS_DRILLS.md
echo "- P95 latency: ___ms" >> docs/OPERATIONS_DRILLS.md
echo "- Error rate: ___%"  >> docs/OPERATIONS_DRILLS.md
```

---

## Emergency Procedures

### Rollback Triggers
- Error rate > 5% for 2 minutes
- P95 latency > 1000ms for 2 minutes  
- GPU VRAM > 20GB for 1 minute
- Model accuracy < 90% for 5 minutes

### Emergency Rollback
```bash
# Immediate rollback (< 60 seconds)
kubectl rollout undo deployment/petplantr-api

# Verify rollback
bash test_enhanced_system.sh --environment production --quick

# Emergency communication
echo "🚨 EMERGENCY ROLLBACK EXECUTED" | slack-notify #incident-response
```

### Communication Plan
- **Internal:** #petplantr-launches Slack channel
- **External:** Status page at status.petplantr.com
- **Customer Support:** Support team briefed on new features
- **Stakeholders:** Email update with Grafana dashboard links

---

## Launch Day Checklist

### T-minus 24h
- [ ] Model fine-tuning completed successfully
- [ ] W&B run documented in operations log
- [ ] Training accuracy meets >95% threshold

### T-minus 12h  
- [ ] Pre-flight validation passes all gates
- [ ] HTML evidence reports generated
- [ ] GitHub release draft created with artifacts

### T-minus 6h
- [ ] Infrastructure deployment successful
- [ ] Terraform apply logs captured
- [ ] Health checks passing

### T-minus 2h
- [ ] Canary deployment at 5% traffic
- [ ] Canary metrics within SLO targets
- [ ] Evidence report generated

### T-0
- [ ] Go/No-Go decision documented
- [ ] Grafana snapshots captured
- [ ] 100% traffic promotion completed

### T+1h
- [ ] Git tag v1.0.0 created
- [ ] GitHub release published
- [ ] Changelog updated

### T+24h
- [ ] Retrospective conducted
- [ ] Lessons learned documented
- [ ] Next release planning initiated

**Launch Status:** 🔄 In Progress | ✅ Complete | ❌ Failed

---

## Next-Phase Roadmap (Post-Launch Months 2-6)

### Advanced Capabilities

#### Chaos Engineering
```bash
bash next_phase_enhancements.sh --phase chaos
```
- [ ] Chaos mesh experiments and resilience testing
- [ ] KEDA GPU auto-scaling (drill remediation implemented)
- [ ] Automated failure recovery workflows
- [ ] Network partitioning and latency injection tests

#### Edge Compute Optimization
```bash
bash next_phase_enhancements.sh --phase edge
```
- [ ] Cloudflare Workers for edge inference
- [ ] CDN optimization and intelligent caching
- [ ] Geographic load balancing and regional failover
- [ ] WASM model deployment for ultra-low latency

#### Advanced Analytics
```bash
bash next_phase_enhancements.sh --phase analytics
```
- [ ] MLflow tracking server integration
- [ ] Weights & Biases experiment management
- [ ] A/B testing framework for model deployments
- [ ] ML observability and drift detection

#### Cost Governance
```bash
bash next_phase_enhancements.sh --phase cost
```
- [ ] FinOps automation and optimization
- [ ] AWS budget alerts and cost monitoring
- [ ] Resource rightsizing recommendations
- [ ] Spot instance optimization for training

#### Privacy Engineering
```bash
bash next_phase_enhancements.sh --phase privacy
```
- [ ] GDPR compliance endpoints (/privacy/export, /privacy/delete)
- [ ] PII detection and anonymization
- [ ] Data retention policy automation
- [ ] Privacy impact assessments

#### Security Aftercare
```bash
bash next_phase_enhancements.sh --phase security
```
- [ ] Automated key rotation (TLS, API keys, DB passwords)
- [ ] SBOM generation and vulnerability tracking
- [ ] Compliance monitoring and reporting
- [ ] Bug bounty program readiness

### Scaling Preparations
- [ ] Multi-region deployment with traffic routing
- [ ] Blue-green deployment automation
- [ ] SLO-as-code implementation with automated enforcement
- [ ] Compliance automation (SOC2, GDPR, HIPAA)
- [ ] Advanced incident response with runbooks

### Drill Remediations (Implemented)

These remediations address specific issues found during operational drills:

#### KEDA GPU VRAM Auto-scale
```bash
bash drill_remediations.sh --type keda
```
- [x] Automatic scaling based on GPU memory utilization
- [x] Queue-based scaling for training workloads
- [x] Cron-based scaling for batch operations

#### Prometheus Optimization  
```bash
bash drill_remediations.sh --type prometheus
```
- [x] Optimized scrape intervals (30s default, 10s for critical metrics)
- [x] Fast error-rate detection for SLO monitoring
- [x] GPU metrics collection optimization

#### Sentinel Drift Detection
```bash
bash drill_remediations.sh --type sentinel
```
- [x] Fast drift detection using sentinel dataset (<100ms vs 10s+)
- [x] Representative baseline for production comparison
- [x] Automated maintenance and updates

### Validation Commands
```bash
# Validate all drill remediations
bash validate_drill_remediations.sh

# Apply all next-phase enhancements
for phase in chaos privacy cost analytics edge security; do
    bash next_phase_enhancements.sh --phase $phase --dry-run
done
```

---

*This playbook should be executed by the release captain with support from the engineering team. Each step requires explicit sign-off before proceeding to the next phase.*
