# PetPlantr Production Launch Documentation

This repository contains comprehensive documentation for PetPlantr's production deployment, monitoring, and operational procedures.

## 📚 Documentation Index

### Core Deployment Guides
- **[Deployment Guide](./DEPLOYMENT_GUIDE.md)** - Step-by-step routine release procedures
- **[Runbook](./RUNBOOK_BREED_API.md)** - Emergency response and troubleshooting guide  
- **[Dataset Versioning](./DATASET_VERSIONING.md)** - Model provenance and audit trail
- **[Operations Drills](./OPERATIONS_DRILLS.md)** - Drill execution log and improvement tracking
- **Edge Canary Rollout:** NGINX ([guide](./edge/canary/nginx.md)), Traefik ([guide](./edge/canary/traefik.md)), Cloudflare ([guide](./edge/canary/cloudflare.md))

### Architecture & Design
- **[API Documentation](../src/api/)** - REST API endpoints and schemas
- **[Model Architecture](../src/ai/models/)** - CLIP+LoRA breed detection implementation
- **[Training Pipeline](../src/ai/training/)** - Model training and fine-tuning procedures

### Security & Compliance
- **[Security Hardening](../security_hardening.sh)** - OIDC, secrets management, and security controls
- **[Deployment Security Checklist](../DEPLOYMENT_SECURITY_CHECKLIST.md)** - Pre-deployment security validation

## 🚀 Quick Start

### Prerequisites
```bash
# Verify environment setup
python check_environment.py

# Install dependencies
pip install -r requirements.txt

# Configure AWS OIDC (one-time)
aws configure set region us-west-2
```

### Launch Validation
```bash
# Run comprehensive launch validation
bash launch_gate_checklist.sh --report launch_evidence.html

# Deploy to staging
bash deploy_enhanced.sh --environment staging

# Run production readiness tests
bash test_enhanced_system.sh --environment staging --slo-strict
```

### Production Deployment
```bash
# Full automated launch
bash ultimate_launch_automation.sh --environment production

# Monitor deployment status
bash launch_status_report.sh --environment production --watch
```

## 📊 Monitoring & Observability

### Dashboards
- **[Grafana Inference Dashboard](../monitoring/grafana/dashboards/inference_gpu_latency.json)** - GPU VRAM, latency, and performance metrics
- **[Prometheus Alerts](../monitoring/prometheus/alerts/gpu_vram.yml)** - GPU monitoring and alerting rules

### Key Metrics
| Metric | SLO Target | Alert Threshold |
|--------|------------|-----------------|
| **Accuracy** | ≥95% | <95% for 5m |
| **Latency (P50)** | ≤500ms | >500ms for 2m |
| **Error Rate** | ≤1% | >1% for 1m |
| **GPU VRAM** | ≤5GB | >5GB for 2m |
| **False Positive** | ≤2% | >2% for 5m |

### Monitoring Access
- **Grafana:** https://grafana.petplantr.com
- **Prometheus:** https://prometheus.petplantr.com
- **PagerDuty:** https://petplantr.pagerduty.com

## 🛠️ Operational Procedures

### Incident Response
1. **Immediate Response:** Follow [Runbook](./RUNBOOK_BREED_API.md) for your specific incident
2. **Escalation:** Use #incident-response Slack channel
3. **Communication:** Follow incident communication templates in runbook

### Regular Maintenance
- **Weekly:** Dependency updates, log rotation, performance review
- **Monthly:** Security patches, capacity planning, cost optimization  
- **Quarterly:** Disaster recovery testing, operational drills

### Emergency Contacts
- **On-Call Engineer:** #petplantr-oncall (Slack)
- **Engineering Manager:** #eng-escalation (Slack)
- **Security Team:** #security-alerts (Slack)

## 🔧 Development Workflow

### CI/CD Pipeline
The GitHub Actions workflow includes:
- **Unit Tests:** Fast mode with stubs (`test-unit` job)
- **Security Scanning:** TruffleHog secrets detection, vulnerability scanning
- **Performance Testing:** SLO validation and benchmarking
- **Deployment:** OIDC-based secure deployment to AWS

### Testing Strategy
```bash
# Unit tests (fast mode)
pytest tests/ -m "not integration"

# Integration tests
pytest tests/ --integration

# Performance benchmarks
bash test_enhanced_system.sh --benchmark --iterations 100

# Security validation
bash security_hardening.sh
```

### Release Process
1. **Feature Development:** Create feature branch from `develop`
2. **Code Review:** Ensure all CI checks pass, require security review
3. **Staging Deployment:** Auto-deploy to staging on `develop` merge
4. **Production Release:** Manual promotion via `main` branch merge
5. **Post-Deploy Monitoring:** 2-hour monitoring window with automated rollback

## 📈 Performance Optimization

### GPU Optimization
- **Batch Size Tuning:** Balance between throughput and VRAM usage
- **Model Quantization:** Reduce VRAM footprint while maintaining accuracy
- **TensorRT Integration:** Optimize inference speed on NVIDIA GPUs

### Cost Optimization
- **Auto-Scaling:** Scale based on request volume and GPU utilization
- **Spot Instances:** Use spot instances for development and training
- **Model Caching:** Intelligent model loading and caching strategies

## 🔒 Security & Compliance

### Security Controls
- **OIDC Authentication:** No static AWS credentials in CI/CD
- **Secrets Management:** All secrets stored in AWS Secrets Manager
- **Network Security:** VPC isolation, security groups, WAF protection
- **Container Security:** Non-root containers, vulnerability scanning

### Compliance
- **Data Privacy:** GDPR compliance for user-uploaded images
- **Audit Logging:** Comprehensive audit trail for all operations
- **Access Control:** Role-based access with principle of least privilege

## 📋 Checklists

### Pre-Deployment
- [ ] All CI/CD checks pass
- [ ] Security scan completed (no HIGH/CRITICAL)
- [ ] Performance benchmarks meet SLOs
- [ ] Launch gate checklist passes
- [ ] Staging deployment validated

### Post-Deployment
- [ ] Health checks pass
- [ ] Monitoring dashboards active
- [ ] Error rates within SLOs
- [ ] Performance metrics stable
- [ ] Rollback plan tested

### Quarterly Review
- [ ] Operational drill execution
- [ ] Security assessment
- [ ] Performance optimization review
- [ ] Cost analysis and optimization
- [ ] Documentation updates

## 🆘 Troubleshooting

### Common Issues
- **High Latency:** Check GPU VRAM usage, reduce batch size, scale replicas
- **Model Accuracy Drop:** Validate preprocessing, check model weights integrity
- **Container Crashes:** Review memory limits, GPU driver compatibility
- **API Errors:** Check application logs, verify configuration

### Debug Commands
```bash
# Check pod status
kubectl get pods -l app=petplantr-api

# View application logs
kubectl logs -l app=petplantr-api --tail=100

# Check GPU utilization
kubectl exec deployment/petplantr-api -- nvidia-smi

# Test API health
curl -f https://api.petplantr.com/health

# Run diagnostic suite
bash utils/diagnostic_suite.sh
```

## 📞 Support & Escalation

### Internal Support
- **SRE Team:** #sre-support (Slack)
- **Development Team:** #petplantr-dev (Slack)
- **Security Team:** #security-alerts (Slack)

### External Support
- **AWS Support:** [Console](https://console.aws.amazon.com/support/)
- **NVIDIA Support:** [Developer Portal](https://developer.nvidia.com/support)
- **PagerDuty:** [Incidents Dashboard](https://petplantr.pagerduty.com)

### Escalation Matrix
| Severity | Response Time | Escalation |
|----------|---------------|------------|
| **SEV-1** | 5 minutes | Immediate page to on-call |
| **SEV-2** | 15 minutes | Slack notification |
| **SEV-3** | 1 hour | Normal business hours |
| **SEV-4** | 24 hours | Next business day |

## 📝 Contributing

### Documentation Updates
1. Create branch from `main`
2. Update relevant documentation
3. Test all linked scripts and procedures
4. Submit PR with documentation review required

### Code Changes
1. Follow the development workflow above
2. Ensure all automation scripts pass
3. Update documentation if procedures change
4. Include performance impact assessment

### Operations Improvements
1. Document improvement in [Operations Drills](./OPERATIONS_DRILLS.md)
2. Update runbooks with lessons learned
3. Share improvements with team via #ops-improvements

---

**Last Updated:** August 4, 2025  
**Maintained By:** SRE Team (@sre-team)  
**Review Frequency:** Monthly  

For questions or improvements, contact: sre@petplantr.com
