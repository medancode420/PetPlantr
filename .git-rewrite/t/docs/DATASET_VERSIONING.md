# PetPlantr Dataset Versioning Guide

## Overview
This document provides the audit trail and provenance tracking for all datasets used in PetPlantr's breed detection models.

## Dataset Version Control

### Current Production Dataset
```yaml
dataset_id: "breed-detection-v2.1.0"
creation_date: "2025-08-01"
sha256_hash: "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
s3_location: "s3://petplantr-datasets/breed-detection/v2.1.0/"
total_images: 125,847
total_breeds: 175
label_count: 125,847
quality_score: 0.97
status: "PRODUCTION_ACTIVE"
```

### Dataset Registry

#### v2.1.0 (Current Production)
- **Date Locked:** 2025-08-01T10:30:00Z
- **SHA256:** `a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456`
- **Images:** 125,847 total
  - Training: 100,678 (80%)
  - Validation: 12,568 (10%)
  - Test: 12,601 (10%)
- **Breeds:** 175 distinct breeds
- **S3 Location:** `s3://petplantr-datasets/breed-detection/v2.1.0/`
- **Model Performance:** 95.2% accuracy, 1.8% FP rate
- **Quality Audit:** PASSED (human review on 5% sample)

#### v2.0.3 (Previous Stable)
- **Date Locked:** 2025-07-15T14:22:00Z
- **SHA256:** `b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567`
- **Images:** 118,234 total
- **Breeds:** 172 distinct breeds
- **S3 Location:** `s3://petplantr-datasets/breed-detection/v2.0.3/`
- **Model Performance:** 94.1% accuracy, 2.3% FP rate
- **Status:** ARCHIVED

#### v2.0.2 (Deprecated - Quality Issues)
- **Date Locked:** 2025-07-01T09:15:00Z
- **SHA256:** `c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678`
- **Status:** DEPRECATED (mislabeled mixed breeds detected)
- **Issue:** 1,247 mixed breed images incorrectly labeled as pure breeds
- **Resolution:** Fixed in v2.0.3

## Data Collection Standards

### Image Quality Requirements
```yaml
image_standards:
  min_resolution: "512x512"
  max_resolution: "4096x4096"
  formats: ["jpg", "jpeg", "png"]
  min_file_size: "50KB"
  max_file_size: "10MB"
  color_space: "RGB"
  quality_score_min: 0.8
```

### Labeling Standards
```yaml
labeling_requirements:
  purity_threshold: 0.95  # Mixed breed if < 95% single breed
  confidence_requirement: 0.9  # Human labeler confidence
  dual_review_required: true
  expert_validation: true  # For rare breeds
  breed_mapping: "AKC_standard_2025"
```

### Breed Coverage Requirements
```yaml
breed_coverage:
  min_images_per_breed: 100
  max_images_per_breed: 2000
  rare_breed_min: 50
  mixed_breed_representation: "15%"
  age_diversity: ["puppy", "adult", "senior"]
  pose_diversity: ["front", "side", "three_quarter"]
```

## Audit Trail

### Data Provenance Tracking
Each dataset version maintains complete provenance:

```json
{
  "dataset_id": "breed-detection-v2.1.0",
  "creation_timestamp": "2025-08-01T10:30:00Z",
  "creator": "data-pipeline-bot",
  "source_datasets": [
    {
      "name": "breed-detection-v2.0.3",
      "contribution": "baseline_images",
      "image_count": 118234
    },
    {
      "name": "community-upload-2025-07",
      "contribution": "new_submissions",
      "image_count": 5613
    },
    {
      "name": "synthetic-augmentation-v3",
      "contribution": "data_augmentation",
      "image_count": 2000
    }
  ],
  "processing_steps": [
    {
      "step": "deduplication",
      "method": "perceptual_hash",
      "removed_count": 1247
    },
    {
      "step": "quality_filtering",
      "method": "inception_score",
      "removed_count": 892
    },
    {
      "step": "label_validation",
      "method": "expert_review",
      "corrected_count": 156
    }
  ],
  "quality_metrics": {
    "label_accuracy": 0.974,
    "image_quality_score": 0.891,
    "breed_distribution_balance": 0.823,
    "duplicate_rate": 0.003
  }
}
```

### S3 Bucket Structure
```
s3://petplantr-datasets/
├── breed-detection/
│   ├── v2.1.0/
│   │   ├── manifest.json
│   │   ├── labels.csv
│   │   ├── train/
│   │   │   ├── golden_retriever/
│   │   │   ├── labrador_retriever/
│   │   │   └── ...
│   │   ├── validation/
│   │   └── test/
│   ├── v2.0.3/
│   └── archived/
├── metadata/
│   ├── checksums/
│   ├── audit_logs/
│   └── quality_reports/
└── backups/
    ├── weekly/
    └── monthly/
```

## Dataset Validation

### Automated Validation Pipeline
```bash
#!/bin/bash
# validate_dataset.sh

DATASET_PATH="$1"
VERSION="$2"

# 1. Checksum validation
echo "Validating checksums..."
sha256sum -c "${DATASET_PATH}/checksums.txt"

# 2. Label consistency check
echo "Checking label consistency..."
python scripts/validate_labels.py "${DATASET_PATH}/labels.csv"

# 3. Image quality validation
echo "Validating image quality..."
python scripts/validate_images.py "${DATASET_PATH}"

# 4. Breed distribution analysis
echo "Analyzing breed distribution..."
python scripts/analyze_distribution.py "${DATASET_PATH}/labels.csv"

# 5. Duplicate detection
echo "Checking for duplicates..."
python scripts/detect_duplicates.py "${DATASET_PATH}"

echo "✅ Dataset ${VERSION} validation complete"
```

### Quality Gates
Before a dataset can be promoted to production:

1. **Checksum Verification:** All files match expected SHA256 hashes
2. **Label Accuracy:** >97% label accuracy on human-reviewed sample
3. **Image Quality:** >89% average quality score
4. **Breed Balance:** No breed >2x over-represented vs. target distribution  
5. **Duplicate Rate:** <0.5% duplicate images
6. **Expert Review:** Veterinarian approval for new/rare breeds

## Version Promotion Process

### Staging to Production Checklist
- [ ] Dataset validation passes all automated checks
- [ ] Model training completes with >95% accuracy
- [ ] A/B testing shows no regression in user metrics
- [ ] Security scan passes (no PII in metadata)
- [ ] Legal review complete (licensing/attribution)
- [ ] Backup created in long-term storage
- [ ] Rollback plan tested and documented

### Promotion Commands
```bash
# Promote dataset from staging to production
aws s3 sync s3://petplantr-datasets-staging/breed-detection/v2.1.0/ \
            s3://petplantr-datasets/breed-detection/v2.1.0/

# Update production manifest
aws s3 cp production_manifest.json \
          s3://petplantr-datasets/breed-detection/CURRENT_VERSION.json

# Tag release
git tag dataset-v2.1.0
git push origin dataset-v2.1.0

# Update model training pipeline
kubectl set env deployment/training-pipeline DATASET_VERSION=v2.1.0
```

## Data Retention & Archival

### Retention Policy
- **Production Datasets:** Retained indefinitely
- **Development Datasets:** 1 year
- **Experimental Datasets:** 6 months
- **Deprecated Datasets:** 2 years before permanent deletion
- **Audit Logs:** 7 years (compliance requirement)

### Archival Process
```bash
# Archive old dataset version
aws s3 sync s3://petplantr-datasets/breed-detection/v2.0.2/ \
            s3://petplantr-datasets-archive/breed-detection/v2.0.2/ \
            --storage-class GLACIER

# Update dataset registry
python scripts/update_registry.py --archive v2.0.2 --reason "superseded"
```

## Access Control & Security

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/petplantr-training-role"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::petplantr-datasets/*"
      ]
    }
  ]
}
```

### Access Audit
Monthly access review includes:
- User access patterns
- Download frequency by dataset
- Cross-region access attempts
- Unusual access patterns

## Compliance & Legal

### Data Sources
- **Public Datasets:** Properly attributed with licenses
- **User Submissions:** Explicit consent for ML training use
- **Licensed Content:** Commercial usage rights verified
- **Synthetic Data:** Generated using licensed base models

### Privacy Protection
- **PII Scrubbing:** Automated removal of EXIF data, GPS coordinates
- **Face Blurring:** Human faces automatically blurred in images
- **Background Sanitization:** Personal information in backgrounds removed

### GDPR Compliance
- **Right to be Forgotten:** User image removal process documented
- **Data Minimization:** Only necessary metadata retained
- **Purpose Limitation:** Data used only for declared ML training purposes

## Monitoring & Alerts

### Dataset Health Metrics
```yaml
monitoring:
  checksum_validation:
    frequency: "daily"
    alert_threshold: "any_failure"
  
  access_patterns:
    frequency: "hourly" 
    alert_threshold: "unusual_spike"
  
  storage_costs:
    frequency: "weekly"
    alert_threshold: "20%_increase"
  
  data_freshness:
    frequency: "daily"
    alert_threshold: "7_days_stale"
```

### Grafana Dashboard
Key metrics tracked:
- Dataset version usage across environments
- Training pipeline success rate by dataset
- Storage costs and growth trends
- Data quality scores over time
- Access patterns and anomalies

## Emergency Procedures

### Dataset Corruption Response
1. **Immediate:** Switch to previous known-good version
2. **Short-term:** Restore from backup 
3. **Long-term:** Root cause analysis and prevention

### Security Incident Response
1. **Immediate:** Revoke access, isolate affected data
2. **Investigation:** Audit access logs, identify scope
3. **Remediation:** Implement fixes, update security controls
4. **Communication:** Notify stakeholders per incident response plan

## Contact Information

### Dataset Team
- **Data Engineering Lead:** data-eng-lead@petplantr.com
- **ML Engineering Lead:** ml-eng-lead@petplantr.com  
- **Quality Assurance:** qa-lead@petplantr.com
- **Legal/Compliance:** legal@petplantr.com

### Emergency Escalation
- **Data Incidents:** #data-incidents (Slack)
- **Security Issues:** #security-alerts (Slack)
- **Legal Issues:** legal-emergency@petplantr.com
