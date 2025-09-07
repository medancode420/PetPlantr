# PetPlantr Disaster Recovery Runbook
## RTO: < 2 hours | RPO: < 15 minutes

### Document Information
- **Version**: 1.0
- **Last Updated**: September 5, 2025
- **Owner**: DevOps Team
- **Review Cycle**: Quarterly

---

## 1. Executive Summary

This runbook outlines the disaster recovery procedures for PetPlantr, ensuring business continuity with:
- **Recovery Time Objective (RTO)**: Less than 2 hours
- **Recovery Point Objective (RPO)**: Less than 15 minutes
- **Service Level Agreement**: 99.9% uptime

---

## 2. System Architecture Overview

### Primary Components
- **API Server**: FastAPI application (Port 8000)
- **Model Service**: CLIP+DPT breed detection model
- **Database**: PostgreSQL (if applicable)
- **Storage**: AWS S3 for datasets and models
- **Infrastructure**: Docker containers with Kubernetes orchestration

### Critical Data
- User data and configurations
- Trained ML models (v1.4)
- Dataset manifests and metadata
- Application logs and metrics

---

## 3. Disaster Scenarios & Response Procedures

### Scenario 1: API Server Failure
**Impact**: Service unavailable, users cannot access breed detection
**RTO**: 30 minutes | **RPO**: N/A (stateless service)

#### Immediate Response (0-5 minutes)
```bash
# Check service status
curl -f http://localhost:8000/api/v1/health || echo "Service down"

# Restart service
docker-compose restart api-server
# OR
systemctl restart petplantr-api
```

#### Escalation (5-15 minutes)
```bash
# Check logs
docker logs petplantr-api --tail 100

# Verify model loading
curl http://localhost:8000/api/v1/breed/health

# Scale up if needed
kubectl scale deployment petplantr-api --replicas=3
```

#### Full Recovery (15-30 minutes)
```bash
# Deploy fresh instance
kubectl apply -f k8s/api-deployment.yaml

# Verify all endpoints
curl http://localhost:8000/api/v1/breed/detect -X POST -F "image=@test.jpg"
```

### Scenario 2: Model Corruption/Failure
**Impact**: Breed detection returns incorrect results
**RTO**: 1 hour | **RPO**: 15 minutes

#### Immediate Response (0-10 minutes)
```bash
# Check model health
curl http://localhost:8000/api/v1/breed/health

# Switch to backup model
kubectl set image deployment/petplantr-api api=petplantr/api:v1.3
```

#### Recovery Process (10-45 minutes)
```bash
# Download latest model from S3
aws s3 cp s3://petplantr-models/v1.4/model.bin ./models/
aws s3 cp s3://petplantr-models/v1.4/config.json ./models/

# Validate model integrity
python3 -c "
from transformers import CLIPModel
model = CLIPModel.from_pretrained('./models/')
print('Model validation: PASSED')
"

# Deploy updated model
docker build -t petplantr/api:v1.4-updated .
kubectl set image deployment/petplantr-api api=petplantr/api:v1.4-updated
```

#### Verification (45-60 minutes)
```bash
# Test breed detection
curl -X POST http://localhost:8000/api/v1/breed/detect \\
  -F "image=@golden_retriever.jpg" \\
  -H "Content-Type: multipart/form-data"

# Validate accuracy
python3 scripts/validate_model_accuracy.py
```

### Scenario 3: Database Failure
**Impact**: User data and configurations unavailable
**RTO**: 1.5 hours | **RPO**: 15 minutes

#### Immediate Response (0-15 minutes)
```bash
# Check database connectivity
pg_isready -h localhost -p 5432

# Check replication status
psql -c "SELECT * FROM pg_stat_replication;"
```

#### Failover Process (15-60 minutes)
```bash
# Promote standby to primary
pg_ctl promote -D /var/lib/postgresql/data

# Update application configuration
sed -i 's/db-primary/db-standby/g' config/database.yaml

# Restart application
kubectl rollout restart deployment/petplantr-api
```

#### Data Recovery (60-90 minutes)
```bash
# Restore from latest backup
pg_restore -d petplantr /backups/latest.dump

# Validate data integrity
psql -d petplantr -c "SELECT COUNT(*) FROM users;"

# Re-enable replication
pg_basebackup -h db-primary -D /var/lib/postgresql/data -P
```

### Scenario 4: Complete Infrastructure Failure
**Impact**: Full service outage
**RTO**: 2 hours | **RPO**: 15 minutes

#### Emergency Response (0-30 minutes)
```bash
# Activate backup region
aws ec2 start-instances --instance-ids i-backup-region

# Update DNS to backup
aws route53 change-resource-record-sets \\
  --hosted-zone-id Z123456789 \\
  --change-batch file://dns-failover.json
```

#### Full Recovery (30-120 minutes)
```bash
# Deploy infrastructure
terraform apply -var-file=backup-region.tfvars

# Restore data from backup
aws s3 sync s3://petplantr-backups/latest/ /data/

# Deploy application
kubectl apply -f k8s/

# Verify services
curl https://api.petplantr.com/health
```

---

## 4. Backup Strategy

### Automated Backups
```bash
# Database backups (every 15 minutes)
pg_dump petplantr | gzip > /backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Model backups (daily)
aws s3 sync ./models/ s3://petplantr-models/$(date +%Y%m%d)/

# Configuration backups (hourly)
tar czf /backups/config_$(date +%Y%m%d_%H%M%S).tar.gz ./config/
```

### Backup Verification
```bash
# Test database restore
pg_restore --dry-run /backups/latest.dump

# Test model loading
python3 -c "CLIPModel.from_pretrained('/backups/models/')"

# Test configuration
python3 -c "import yaml; yaml.safe_load(open('/backups/config/app.yaml'))"
```

---

## 5. Monitoring & Alerting

### Key Metrics to Monitor
- API response time (< 500ms)
- Error rate (< 1%)
- Model accuracy (> 85%)
- Database replication lag (< 15min)
- Infrastructure utilization (< 80%)

### Alert Conditions
```yaml
# Prometheus alerting rules
groups:
  - name: petplantr
    rules:
      - alert: APIDown
        expr: up{job="petplantr-api"} == 0
        for: 5m
        labels:
          severity: critical

      - alert: HighErrorRate
        expr: rate(http_requests_total{status="500"}[5m]) > 0.01
        for: 5m
        labels:
          severity: warning

      - alert: ModelAccuracyDrop
        expr: model_accuracy < 0.85
        for: 10m
        labels:
          severity: critical
```

---

## 6. Testing & Validation

### Regular DR Tests
```bash
# Monthly failover test
kubectl drain node-1  # Simulate node failure
kubectl uncordon node-1  # Restore

# Quarterly full DR test
terraform destroy  # Destroy primary region
terraform apply -var-file=backup-region.tfvars  # Restore in backup region
```

### Performance Validation
```bash
# Load testing during DR
hey -n 1000 -c 10 https://api.petplantr.com/api/v1/breed/detect

# Accuracy validation
python3 scripts/e2e_accuracy_test.py
```

---

## 7. Communication Plan

### Internal Communication
- **Slack Channel**: #petplantr-incidents
- **Email Distribution**: devops@petplantr.com
- **Status Page**: https://status.petplantr.com

### External Communication
- **Customer Email**: customers@petplantr.com
- **Status Page Updates**: Automatic via PagerDuty
- **Social Media**: @PetPlantr on Twitter

### Escalation Matrix
1. **Level 1**: On-call engineer (15 minutes)
2. **Level 2**: DevOps lead (30 minutes)
3. **Level 3**: CTO (1 hour)
4. **Level 4**: Executive team (2 hours)

---

## 8. Continuous Improvement

### Post-Incident Review
- **Timeline**: Within 24 hours of incident resolution
- **Participants**: All team members involved
- **Deliverables**: Incident report with root cause and action items

### Metrics Tracking
- Mean Time To Recovery (MTTR)
- Mean Time Between Failures (MTBF)
- Recovery success rate
- RTO/RPO compliance rate

### Lessons Learned
- Update runbook based on incidents
- Improve monitoring and alerting
- Enhance automation where possible
- Regular training and drills

---

## 9. Contact Information

### Primary Contacts
- **DevOps Lead**: devops@petplantr.com
- **On-call Engineer**: +1 (555) 123-4567
- **AWS Support**: aws-support@petplantr.com

### External Resources
- **AWS Enterprise Support**: 1-888-280-4331
- **Cloudflare Support**: support@cloudflare.com
- **GitHub Support**: support@github.com

---

*This runbook is reviewed quarterly and updated based on lessons learned from incidents and changes in infrastructure.*
