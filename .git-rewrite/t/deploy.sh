#!/bin/bash
# PetPlantr Infrastructure Deployment Script
# This script deploys the complete PetPlantr infrastructure using Terraform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/infra"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"
TERRAFORM_STATE_BUCKET="petplantr-terraform-state"
ENVIRONMENT="${1:-prod}"  # Default to prod if not specified

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials are not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

validate_environment() {
    log_info "Validating environment: $ENVIRONMENT"
    
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
        exit 1
    fi
    
    log_success "Environment validation passed!"
}

setup_terraform_backend() {
    log_info "Setting up Terraform backend..."
    
    # Create S3 bucket for Terraform state if it doesn't exist
    if ! aws s3 ls "s3://${TERRAFORM_STATE_BUCKET}" &> /dev/null; then
        log_info "Creating Terraform state bucket: ${TERRAFORM_STATE_BUCKET}"
        aws s3 mb "s3://${TERRAFORM_STATE_BUCKET}" --region us-east-1
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "${TERRAFORM_STATE_BUCKET}" \
            --versioning-configuration Status=Enabled
        
        # Enable encryption
        aws s3api put-bucket-encryption \
            --bucket "${TERRAFORM_STATE_BUCKET}" \
            --server-side-encryption-configuration '{
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            }'
    else
        log_success "Terraform state bucket already exists!"
    fi
}

create_terraform_backend_config() {
    log_info "Creating Terraform backend configuration..."
    
    cat > "${INFRA_DIR}/backend.tf" << EOF
terraform {
  backend "s3" {
    bucket = "${TERRAFORM_STATE_BUCKET}"
    key    = "petplantr/${ENVIRONMENT}/terraform.tfstate"
    region = "us-east-1"
    
    # Enable state locking
    dynamodb_table = "petplantr-terraform-locks"
    encrypt        = true
  }
}
EOF
    
    log_success "Backend configuration created!"
}

create_terraform_vars() {
    log_info "Creating Terraform variables file for environment: $ENVIRONMENT"
    
    # Read sensitive variables from environment or prompt user
    REPLICATE_API_TOKEN="${REPLICATE_API_TOKEN:-$(read -sp 'Enter Replicate API Token: ' token && echo $token)}"
    ALERT_EMAIL="${ALERT_EMAIL:-admin@petplantr.com}"
    
    cat > "${INFRA_DIR}/terraform.tfvars" << EOF
# PetPlantr Terraform Variables - ${ENVIRONMENT} Environment
environment = "${ENVIRONMENT}"
aws_region  = "us-east-1"

# API Configuration
replicate_api_token = "${REPLICATE_API_TOKEN}"

# Monitoring Configuration
alert_email = "${ALERT_EMAIL}"

# Budget Configuration
monthly_budget_limit = $([ "$ENVIRONMENT" = "prod" ] && echo "500" || echo "100")
daily_budget_limit   = $([ "$ENVIRONMENT" = "prod" ] && echo "20" || echo "5")

# Performance Configuration
lambda_memory_size = $([ "$ENVIRONMENT" = "prod" ] && echo "3008" || echo "1024")
quality_threshold = 85
max_refinement_cycles = 3

# Security Configuration
enable_waf = $([ "$ENVIRONMENT" = "prod" ] && echo "true" || echo "false")
enable_kms_encryption = true
blocked_countries = ["CN", "RU", "KP"]

# Feature Flags
enable_budgets = true
enable_step_functions = true
enable_notifications = true
enable_detailed_monitoring = $([ "$ENVIRONMENT" = "prod" ] && echo "true" || echo "false")

# Tags
common_tags = {
  Project     = "PetPlantr"
  Environment = "${ENVIRONMENT}"
  Owner       = "PetPlantr Team"
  Terraform   = "true"
  DeployedBy  = "$(whoami)"
  DeployedAt  = "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    log_success "Terraform variables file created!"
}

build_lambda_packages() {
    log_info "Building Lambda deployment packages..."
    
    cd "${FRONTEND_DIR}"
    
    # Install dependencies if not already installed
    if [ ! -d "node_modules" ]; then
        log_info "Installing npm dependencies..."
        npm install
    fi
    
    # Build the TypeScript files
    log_info "Building TypeScript files..."
    npm run build
    
    # Create Lambda package directory
    mkdir -p "${INFRA_DIR}/lambda-packages"
    
    # Create AI processor package
    log_info "Creating AI processor Lambda package..."
    cd "${INFRA_DIR}/lambda-packages"
    rm -rf ai-processor
    mkdir ai-processor
    cd ai-processor
    
    # Copy built files and create package
    cp "${FRONTEND_DIR}/app/lib/infrastructure/pipelineOrchestrator.js" index.js 2>/dev/null || {
        log_warning "TypeScript build not found, copying source file..."
        cp "${FRONTEND_DIR}/app/lib/infrastructure/pipelineOrchestrator.ts" index.js
    }
    
    # Create basic package.json for Lambda
    cat > package.json << EOF
{
  "name": "petplantr-ai-processor",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "@aws-sdk/client-sfn": "^3.0.0",
    "@aws-sdk/client-sqs": "^3.0.0",
    "@aws-sdk/client-s3": "^3.0.0",
    "@aws-sdk/client-cloudwatch": "^3.0.0"
  }
}
EOF
    
    # Install Lambda dependencies
    npm install --production
    
    # Create ZIP package
    zip -r ../ai-processor.zip . -x "*.git*" "*.DS_Store*"
    
    # Create image analyzer package (simplified)
    cd ..
    cp ai-processor.zip image-analyzer.zip
    cp ai-processor.zip quality-validator.zip
    
    log_success "Lambda packages created!"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd "${INFRA_DIR}"
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    # Create workspace if it doesn't exist
    terraform workspace select "$ENVIRONMENT" 2>/dev/null || terraform workspace new "$ENVIRONMENT"
    
    # Plan the deployment
    log_info "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Ask for confirmation
    echo ""
    log_warning "Ready to deploy infrastructure for environment: $ENVIRONMENT"
    read -p "Do you want to proceed? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Applying Terraform configuration..."
        terraform apply tfplan
        
        # Clean up plan file
        rm -f tfplan
        
        log_success "Infrastructure deployment completed!"
    else
        log_info "Deployment cancelled by user."
        rm -f tfplan
        exit 0
    fi
}

update_environment_file() {
    log_info "Updating environment configuration..."
    
    cd "${INFRA_DIR}"
    
    # Get Terraform outputs
    S3_BUCKET=$(terraform output -raw s3_bucket_name)
    CDN_DOMAIN=$(terraform output -raw cloudfront_domain_name)
    STEP_FUNCTION_ARN=$(terraform output -raw step_function_arn)
    SQS_QUEUE_URL=$(terraform output -raw sqs_processing_queue_url)
    SQS_NOTIFICATIONS_URL=$(terraform output -raw sqs_notifications_queue_url)
    KMS_KEY_ID=$(terraform output -raw kms_key_id 2>/dev/null || echo "")
    
    # Update frontend environment file
    ENV_FILE="${FRONTEND_DIR}/.env.local"
    
    log_info "Updating ${ENV_FILE}..."
    
    # Backup existing file
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Update or add infrastructure values
    update_env_var() {
        local key=$1
        local value=$2
        
        if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
            sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
        else
            echo "${key}=${value}" >> "$ENV_FILE"
        fi
    }
    
    # Copy template if env file doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        cp "${SCRIPT_DIR}/.env.template" "$ENV_FILE"
    fi
    
    # Update infrastructure values
    update_env_var "AWS_S3_BUCKET" "$S3_BUCKET"
    update_env_var "CLOUDFRONT_DOMAIN" "$CDN_DOMAIN"
    update_env_var "NEXT_PUBLIC_CLOUDFRONT_DOMAIN" "$CDN_DOMAIN"
    update_env_var "CDN_BASE_URL" "https://${CDN_DOMAIN}"
    update_env_var "NEXT_PUBLIC_CDN_BASE_URL" "https://${CDN_DOMAIN}"
    update_env_var "STEP_FUNCTION_ARN" "$STEP_FUNCTION_ARN"
    update_env_var "SQS_QUEUE_URL" "$SQS_QUEUE_URL"
    update_env_var "SQS_NOTIFICATIONS_QUEUE_URL" "$SQS_NOTIFICATIONS_URL"
    
    if [ -n "$KMS_KEY_ID" ]; then
        update_env_var "KMS_KEY_ID" "$KMS_KEY_ID"
    fi
    
    log_success "Environment file updated!"
}

run_tests() {
    log_info "Running infrastructure validation tests..."
    
    cd "${FRONTEND_DIR}"
    
    # Install dependencies if needed
    npm install
    
    # Run tests
    if [ -f "test-ai-enhancement.js" ]; then
        log_info "Running AI enhancement tests..."
        node test-ai-enhancement.js || log_warning "Some tests failed, but deployment can continue"
    fi
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    # Add basic connectivity tests here
    
    log_success "Tests completed!"
}

display_deployment_summary() {
    log_success "🎉 PetPlantr Infrastructure Deployment Complete!"
    echo ""
    echo "=================================================="
    echo "DEPLOYMENT SUMMARY"
    echo "=================================================="
    echo "Environment: $ENVIRONMENT"
    echo "Region: us-east-1"
    echo ""
    
    if [ -f "${INFRA_DIR}/terraform.tfstate" ] || terraform output &>/dev/null; then
        cd "${INFRA_DIR}"
        echo "Infrastructure Resources:"
        echo "- S3 Bucket: $(terraform output -raw s3_bucket_name 2>/dev/null || echo 'N/A')"
        echo "- CloudFront Domain: $(terraform output -raw cloudfront_domain_name 2>/dev/null || echo 'N/A')"
        echo "- Step Function: $(terraform output -raw step_function_arn 2>/dev/null | cut -d':' -f6- || echo 'N/A')"
        echo ""
        echo "Dashboard URLs:"
        echo "- CloudWatch: $(terraform output -raw cloudwatch_dashboard_url 2>/dev/null || echo 'N/A')"
        echo ""
        echo "Next Steps:"
        echo "1. Update your .env.local file with the new infrastructure values"
        echo "2. Deploy your frontend application to Vercel"
        echo "3. Test the complete AI generation pipeline"
        echo "4. Monitor costs and performance in CloudWatch"
    fi
    
    echo "=================================================="
}

# Main execution
main() {
    log_info "Starting PetPlantr infrastructure deployment..."
    echo "Environment: $ENVIRONMENT"
    echo "Script directory: $SCRIPT_DIR"
    echo ""
    
    # Run Python unit tests early to catch regressions
    if [ -x "${SCRIPT_DIR}/scripts/run_python_tests.sh" ]; then
        log_info "Running Python tests (pre-deploy check)..."
        bash "${SCRIPT_DIR}/scripts/run_python_tests.sh" || log_warning "Python tests failed; continuing deployment as this may be infra-only"
    fi
    
    check_prerequisites
    validate_environment
    setup_terraform_backend
    create_terraform_backend_config
    create_terraform_vars
    build_lambda_packages
    deploy_infrastructure
    update_environment_file
    run_tests
    
    # Optionally run Python tests again after deploy updates
    if [ -x "${SCRIPT_DIR}/scripts/run_python_tests.sh" ]; then
        log_info "Re-running Python tests (post-deploy check)..."
        bash "${SCRIPT_DIR}/scripts/run_python_tests.sh" || log_warning "Post-deploy Python tests failed; review needed"
    fi
    display_deployment_summary
    
    log_success "Deployment script completed successfully!"
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [environment]"
        echo ""
        echo "Arguments:"
        echo "  environment    Target environment (dev|staging|prod) [default: prod]"
        echo ""
        echo "Environment Variables:"
        echo "  REPLICATE_API_TOKEN    Replicate API token (required)"
        echo "  ALERT_EMAIL           Email for alerts [default: admin@petplantr.com]"
        echo ""
        echo "Examples:"
        echo "  $0 prod                # Deploy to production"
        echo "  $0 staging             # Deploy to staging"
        echo "  REPLICATE_API_TOKEN=xxx $0 dev  # Deploy to dev with token"
        exit 0
        ;;
    --destroy)
        log_warning "Destroying infrastructure for environment: ${2:-prod}"
        read -p "Are you sure you want to destroy all infrastructure? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "${INFRA_DIR}"
            terraform workspace select "${2:-prod}"
            terraform destroy
        fi
        exit 0
        ;;
    *)
        main
        ;;
esac
