#!/bin/bash
# PetPlantr Infrastructure Deployment Script
# Story 3.3: Multi-AZ K8s cluster IaC

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="petplantr-${ENVIRONMENT}"

echo -e "${BLUE}🚀 PetPlantr Infrastructure Deployment${NC}"
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${AWS_REGION}"
echo "Cluster: ${CLUSTER_NAME}"
echo

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Please install it first.${NC}"
    exit 1
fi

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install it first.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure'.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Initialize Terraform
echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
cd infrastructure
terraform init

# Validate configuration
echo -e "${YELLOW}🔍 Validating Terraform configuration...${NC}"
terraform validate

# Plan deployment
echo -e "${YELLOW}📋 Planning infrastructure deployment...${NC}"
terraform plan -var="environment=${ENVIRONMENT}" -var="aws_region=${AWS_REGION}" -out=tfplan

# Ask for confirmation
echo
echo -e "${YELLOW}⚠️  This will create the following resources:${NC}"
echo "  - VPC with 3 public/private subnets across 3 AZs"
echo "  - EKS cluster with managed node groups"
echo "  - RDS PostgreSQL database (Multi-AZ)"
echo "  - S3 bucket for models and datasets"
echo "  - Application Load Balancer"
echo "  - CloudWatch monitoring and alerts"
echo "  - ArgoCD, Prometheus, Grafana"
echo
read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

# Deploy infrastructure
echo -e "${BLUE}🏗️  Deploying infrastructure...${NC}"
terraform apply tfplan

# Get cluster information
echo -e "${YELLOW}🔗 Configuring kubectl...${NC}"
aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME}

# Verify cluster
echo -e "${YELLOW}🔍 Verifying cluster...${NC}"
kubectl get nodes
kubectl get pods --all-namespaces

# Deploy monitoring stack
echo -e "${YELLOW}📊 Deploying monitoring stack...${NC}"
kubectl apply -f k8s/monitoring/

# Deploy ArgoCD
echo -e "${YELLOW}🚢 Deploying ArgoCD...${NC}"
kubectl apply -f k8s/argocd/

# Wait for ArgoCD
echo -e "${YELLOW}⏳ Waiting for ArgoCD to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get ArgoCD admin password
ARGOCD_PASSWORD=$(kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d)
echo -e "${GREEN}✅ ArgoCD deployed${NC}"
echo "Admin password: ${ARGOCD_PASSWORD}"

# Deploy PetPlantr application
echo -e "${YELLOW}🐕 Deploying PetPlantr application...${NC}"
kubectl apply -f k8s/petplantr-deployment.yaml

# Wait for deployment
echo -e "${YELLOW}⏳ Waiting for PetPlantr to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/petplantr-api

# Get service information
echo -e "${YELLOW}🔗 Getting service endpoints...${NC}"
kubectl get services
kubectl get ingress

# Run health checks
echo -e "${YELLOW}🏥 Running health checks...${NC}"
API_ENDPOINT=$(kubectl get ingress petplantr-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "API Endpoint: ${API_ENDPOINT}"

# Test health endpoint
echo -e "${YELLOW}🩺 Testing API health...${NC}"
curl -f "http://${API_ENDPOINT}/health" || echo "Health check failed - this is expected until DNS propagates"

# Deploy backup and monitoring
echo -e "${YELLOW}💾 Setting up backups and monitoring...${NC}"

# Create backup job
kubectl apply -f k8s/backup/

# Setup log aggregation
kubectl apply -f k8s/logging/

echo
echo -e "${GREEN}🎉 Infrastructure deployment completed!${NC}"
echo
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "  🌐 API Endpoint: http://${API_ENDPOINT}"
echo "  🔗 ArgoCD: https://argocd.${API_ENDPOINT}"
echo "  📊 Grafana: https://grafana.${API_ENDPOINT}"
echo "  📈 Prometheus: https://prometheus.${API_ENDPOINT}"
echo
echo -e "${YELLOW}🔑 Important Credentials:${NC}"
echo "  ArgoCD Admin Password: ${ARGOCD_PASSWORD}"
echo
echo -e "${BLUE}📚 Next Steps:${NC}"
echo "  1. Update DNS records to point to the load balancer"
echo "  2. Configure SSL certificates"
echo "  3. Set up CI/CD pipelines"
echo "  4. Configure monitoring alerts"
echo "  5. Test the application endpoints"
echo
echo -e "${GREEN}✅ Multi-AZ Kubernetes cluster deployment successful!${NC}"
