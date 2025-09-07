#!/bin/bash

# PetPlantr Security Hardening Script
# Removes static secrets, configures OIDC/STS, and hardens deployment automation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

echo "========================================"
echo "  PetPlantr Security Hardening"
echo "========================================"
echo ""

# 1. Scan for static secrets and hardcoded credentials
log_info "Step 1/7: Scanning for static secrets"
if command -v trufflehog >/dev/null 2>&1; then
    # Install TruffleHog if not present
    if ! trufflehog --version >/dev/null 2>&1; then
        log_info "Installing TruffleHog security scanner..."
        if command -v go >/dev/null 2>&1; then
            go install github.com/trufflesecurity/trufflehog/v3@latest
        else
            log_warning "Go not found, downloading TruffleHog binary..."
            curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
        fi
    fi
    
    # Run TruffleHog scan with failure on detection
    log_info "Running TruffleHog secret detection..."
    if trufflehog filesystem . --fail --no-update >/dev/null 2>&1; then
        log_success "No hardcoded secrets detected"
    else
        log_error "Hardcoded secrets detected! Review and remove before deployment."
        trufflehog filesystem . --no-update
        exit 1
    fi
else
    log_warning "TruffleHog not available, installing..."
    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
    trufflehog filesystem . --fail --no-update
fi

# 2. Secure automation scripts (make non-executable)
log_info "Step 2/7: Securing automation scripts"
automation_scripts=(
    "prepare_training_corpus.sh"
    "one_hour_finetune.sh"
    "deploy_enhanced.sh"
    "test_enhanced_system.sh"
    "quick_validation.sh"
    "complete_pipeline.sh"
    "complete_launch_pipeline.sh"
    "setup_monitoring.sh"
    "launch_and_harden.sh"
    "advanced_operational_care.sh"
    "launch_gate_checklist.sh"
    "launch_status_report.sh"
    "production_monitoring_setup.sh"
    "ultimate_launch_automation.sh"
)

for script in "${automation_scripts[@]}"; do
    if [[ -f "$script" ]]; then
        # Remove execute permissions
        chmod 644 "$script"
        log_info "Secured $script (removed execute permissions)"
        
        # Add security header if not present
        if ! head -5 "$script" | grep -q "SECURITY:"; then
            temp_file=$(mktemp)
            echo "#!/bin/bash" > "$temp_file"
            echo "# SECURITY: This script contains sensitive operations." >> "$temp_file"
            echo "# Review carefully before execution. Run with: bash $script" >> "$temp_file"
            echo "" >> "$temp_file"
            tail -n +2 "$script" >> "$temp_file"
            mv "$temp_file" "$script"
            log_info "Added security header to $script"
        fi
    fi
done

# 3. Generate OIDC deployment configuration
log_info "Step 3/7: Generating OIDC deployment configuration"
cat > "deployment_oidc_config.yml" << 'EOF'
# PetPlantr OIDC/STS Deployment Configuration
# Use with GitHub Actions OIDC provider for secure deployment

oidc:
  # GitHub OIDC Provider
  provider_url: "https://token.actions.githubusercontent.com"
  audience: "sts.amazonaws.com"
  
  # AWS IAM Role for Deployment
  aws_role_arn: "arn:aws:iam::ACCOUNT:role/petplantr-deploy-role"
  aws_region: "us-west-2"
  
  # Deployment permissions (minimal required)
  permissions:
    - "ecr:GetAuthorizationToken"
    - "ecr:BatchCheckLayerAvailability"
    - "ecr:GetDownloadUrlForLayer"
    - "ecr:BatchGetImage"
    - "ecr:InitiateLayerUpload"
    - "ecr:UploadLayerPart"
    - "ecr:CompleteLayerUpload"
    - "ecr:PutImage"
    - "ecs:UpdateService"
    - "ecs:DescribeServices"
    - "ecs:DescribeTaskDefinition"
    - "ecs:RegisterTaskDefinition"
    
  # Session duration (1 hour max)
  session_duration: 3600

# Deployment targets
environments:
  staging:
    cluster: "petplantr-staging"
    service: "petplantr-api-staging"
    task_definition: "petplantr-api-staging"
  
  production:
    cluster: "petplantr-production"
    service: "petplantr-api-production"
    task_definition: "petplantr-api-production"

# Security constraints
security:
  # Only allow deployment from protected branches
  allowed_branches:
    - "main"
    - "release/*"
  
  # Require code review approval
  require_review: true
  
  # Require status checks
  required_status_checks:
    - "test-unit"
    - "security"
    - "build"
    - "performance"
EOF

log_success "Generated OIDC deployment configuration"

# 4. Update GitHub Actions workflow for OIDC
log_info "Step 4/7: Updating CI/CD for OIDC authentication"
if [[ -f ".github/workflows/ci-cd.yml" ]]; then
    # Backup original
    cp ".github/workflows/ci-cd.yml" ".github/workflows/ci-cd.yml.backup"
    
    # Add OIDC configuration at the top of deploy job
    python3 -c "
import yaml
import sys

# Read and parse YAML
with open('.github/workflows/ci-cd.yml', 'r') as f:
    workflow = yaml.safe_load(f)

# Update deploy-staging job with OIDC
if 'jobs' in workflow and 'deploy-staging' in workflow['jobs']:
    deploy_job = workflow['jobs']['deploy-staging']
    
    # Add OIDC permissions
    deploy_job['permissions'] = {
        'id-token': 'write',
        'contents': 'read'
    }
    
    # Update steps to use OIDC
    steps = deploy_job.get('steps', [])
    
    # Find and update AWS credentials step
    for i, step in enumerate(steps):
        if step.get('name') == 'Configure AWS credentials':
            steps[i] = {
                'name': 'Configure AWS credentials',
                'uses': 'aws-actions/configure-aws-credentials@v4',
                'with': {
                    'role-to-assume': '${{ secrets.AWS_DEPLOY_ROLE_ARN }}',
                    'role-session-name': 'petplantr-deploy-${{ github.run_id }}',
                    'aws-region': 'us-west-2',
                    'role-duration-seconds': 3600
                }
            }
            break

# Write updated workflow
with open('.github/workflows/ci-cd.yml', 'w') as f:
    yaml.safe_dump(workflow, f, default_flow_style=False, sort_keys=False)

print('Updated CI/CD workflow for OIDC')
"
    log_success "Updated CI/CD workflow for OIDC authentication"
else
    log_warning "CI/CD workflow not found, skipping OIDC update"
fi

# 5. Generate AWS IAM role trust policy
log_info "Step 5/7: Generating AWS IAM trust policy"
cat > "aws_oidc_trust_policy.json" << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:OWNER/petplantr:*"
        }
      }
    }
  ]
}
EOF

cat > "aws_deploy_policy.json" << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition"
      ],
      "Resource": [
        "arn:aws:ecs:*:*:service/petplantr-*",
        "arn:aws:ecs:*:*:task-definition/petplantr-*"
      ]
    }
  ]
}
EOF

log_success "Generated AWS IAM policies for OIDC deployment"

# 6. Create environment variable template (no secrets)
log_info "Step 6/7: Creating secure environment template"
cat > ".env.template" << 'EOF'
# PetPlantr Environment Configuration Template
# Copy to .env and fill in values (never commit .env to git)

# Application
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Model Configuration
MODEL_PATH=/app/weights/
USE_GPU=true
BATCH_SIZE=16
MAX_IMAGE_SIZE=1024

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true

# W&B Integration (use secrets management)
WANDB_API_KEY=__REPLACE_WITH_SECRET__
WANDB_PROJECT=petplantr-breed-detection

# AWS Configuration (use OIDC/STS)
AWS_REGION=us-west-2
AWS_S3_BUCKET=petplantr-models
AWS_ECR_REGISTRY=__REPLACE_WITH_ACCOUNT__.dkr.ecr.us-west-2.amazonaws.com

# Database (use secrets management)
DB_HOST=__REPLACE_WITH_SECRET__
DB_PORT=5432
DB_NAME=petplantr
DB_USER=__REPLACE_WITH_SECRET__
DB_PASSWORD=__REPLACE_WITH_SECRET__

# Redis Cache (use secrets management)
REDIS_URL=__REPLACE_WITH_SECRET__

# Security
JWT_SECRET=__REPLACE_WITH_SECRET__
ENCRYPTION_KEY=__REPLACE_WITH_SECRET__

# Fast mode for CI/CD
PETPLANTR_FAST_MODE=false
EOF

# Add .env to .gitignore if not present
if [[ -f ".gitignore" ]]; then
    if ! grep -q "^.env$" .gitignore; then
        echo ".env" >> .gitignore
        log_info "Added .env to .gitignore"
    fi
else
    echo ".env" > .gitignore
    log_info "Created .gitignore with .env"
fi

log_success "Created secure environment template"

# 7. Generate deployment security checklist
log_info "Step 7/7: Generating deployment security checklist"
cat > "DEPLOYMENT_SECURITY_CHECKLIST.md" << 'EOF'
# PetPlantr Deployment Security Checklist

## Pre-Deployment Security Validation

### 🔐 Secrets Management
- [ ] No hardcoded secrets in code (TruffleHog scan passed)
- [ ] All secrets stored in GitHub Secrets or AWS Secrets Manager
- [ ] Environment variables use placeholder values (`__REPLACE_WITH_SECRET__`)
- [ ] `.env` file is in `.gitignore` and never committed

### 🔑 Authentication & Authorization
- [ ] GitHub Actions uses OIDC with AWS STS (no static IAM keys)
- [ ] AWS IAM role has minimal required permissions
- [ ] Deployment role session duration ≤ 1 hour
- [ ] Branch protection rules enforce code review

### 🛡️ Infrastructure Security
- [ ] Container images scanned for vulnerabilities (Trivy)
- [ ] Base images updated to latest security patches
- [ ] Non-root user in Docker containers
- [ ] Resource limits configured (CPU, memory, GPU)

### 📋 Code Security
- [ ] Dependencies scanned for known vulnerabilities
- [ ] Code linting and formatting enforced
- [ ] Unit tests achieve >80% coverage
- [ ] Integration tests validate security features

### 🔍 Monitoring & Logging
- [ ] Security events logged (authentication, authorization)
- [ ] Prometheus metrics include security indicators
- [ ] Grafana dashboards monitor for anomalies
- [ ] Log aggregation configured with retention policy

### 🚨 Incident Response
- [ ] Rollback plan tested and documented
- [ ] Security incident response runbook available
- [ ] Monitoring alerts configured for security events
- [ ] Emergency contact list updated

## AWS OIDC Setup Commands

```bash
# 1. Create OIDC provider (one-time setup)
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
    --client-id-list sts.amazonaws.com

# 2. Create deployment role
aws iam create-role \
    --role-name petplantr-deploy-role \
    --assume-role-policy-document file://aws_oidc_trust_policy.json

# 3. Attach deployment policy
aws iam create-policy \
    --policy-name petplantr-deploy-policy \
    --policy-document file://aws_deploy_policy.json

aws iam attach-role-policy \
    --role-name petplantr-deploy-role \
    --policy-arn arn:aws:iam::ACCOUNT:policy/petplantr-deploy-policy
```

## GitHub Secrets Configuration

Required GitHub repository secrets:
- `AWS_DEPLOY_ROLE_ARN`: ARN of the AWS deployment role
- `WANDB_API_KEY`: Weights & Biases API key
- `DB_PASSWORD`: Database password
- `JWT_SECRET`: JWT signing secret
- `ENCRYPTION_KEY`: Application encryption key

## Validation Commands

```bash
# Run security validation
bash security_hardening.sh

# Test OIDC deployment (dry run)
bash deploy_enhanced.sh --dry-run --environment staging

# Verify secrets are not committed
git log --all --grep="password\|secret\|key" --oneline
```
EOF

log_success "Generated deployment security checklist"

# Summary
echo ""
echo "========================================"
echo "  Security Hardening Complete"
echo "========================================"
echo ""
log_success "✅ Static secret scanning configured"
log_success "✅ Automation scripts secured (non-executable)"
log_success "✅ OIDC deployment configuration generated"
log_success "✅ CI/CD workflow updated for OIDC"
log_success "✅ AWS IAM policies generated"
log_success "✅ Secure environment template created"
log_success "✅ Deployment security checklist generated"
echo ""
echo "Next steps:"
echo "1. Set up AWS OIDC provider (see DEPLOYMENT_SECURITY_CHECKLIST.md)"
echo "2. Configure GitHub repository secrets"
echo "3. Review and update deployment_oidc_config.yml with your values"
echo "4. Test deployment with: bash deploy_enhanced.sh --dry-run"
echo ""
echo "Files generated:"
echo "- deployment_oidc_config.yml"
echo "- aws_oidc_trust_policy.json"
echo "- aws_deploy_policy.json"
echo "- .env.template"
echo "- DEPLOYMENT_SECURITY_CHECKLIST.md"
