#!/bin/bash

# PetPlantr GPU Container Deployment Script
# Builds and deploys Docker containers to ECR and ECS

set -e

echo "🚀 PetPlantr GPU Container Deployment"
echo "===================================="

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="680604703891"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
CLUSTER_NAME="petplantr-gpu-cluster"

# Check dependencies
echo "🔍 Checking dependencies..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed"; exit 1; }

# Check AWS authentication
echo "🔐 Checking AWS authentication..."
aws sts get-caller-identity > /dev/null || { echo "❌ AWS authentication failed"; exit 1; }

# Login to ECR
echo "🔑 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Function to create ECR repository if it doesn't exist
create_ecr_repo() {
    local repo_name=$1
    echo "📦 Checking ECR repository: $repo_name"
    
    if ! aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION >/dev/null 2>&1; then
        echo "🆕 Creating ECR repository: $repo_name"
        aws ecr create-repository --repository-name $repo_name --region $AWS_REGION
        
        # Set lifecycle policy to keep only 5 most recent images
        aws ecr put-lifecycle-policy --repository-name $repo_name --region $AWS_REGION --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep only 5 most recent images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": 5
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }'
    else
        echo "✅ ECR repository exists: $repo_name"
    fi
}

# Function to build and push Docker image
build_and_push() {
    local service_name=$1
    local docker_dir="docker/$service_name"
    local image_name="petplantr-$service_name"
    local tag="latest"
    
    echo ""
    echo "🔨 Building $service_name container..."
    echo "Service: $service_name"
    echo "Directory: $docker_dir"
    echo "Image: $image_name:$tag"
    
    # Create ECR repository
    create_ecr_repo $image_name
    
    # Build Docker image
    echo "🐳 Building Docker image..."
    docker build -t $image_name:$tag $docker_dir
    
    # Tag for ECR
    docker tag $image_name:$tag $ECR_REGISTRY/$image_name:$tag
    
    # Push to ECR
    echo "📤 Pushing to ECR..."
    docker push $ECR_REGISTRY/$image_name:$tag
    
    echo "✅ $service_name container deployed successfully"
    echo "   Image: $ECR_REGISTRY/$image_name:$tag"
}

# Function to register ECS task definition
register_task_definition() {
    local service_name=$1
    local task_file="ecs/$service_name-task.json"
    
    echo ""
    echo "📋 Registering ECS task definition: $service_name"
    
    if [ -f "$task_file" ]; then
        aws ecs register-task-definition \
            --cli-input-json file://$task_file \
            --region $AWS_REGION
        echo "✅ Task definition registered: $service_name"
    else
        echo "⚠️  Task definition file not found: $task_file"
    fi
}

# Function to create ECS cluster if it doesn't exist
create_ecs_cluster() {
    echo ""
    echo "🏗️  Checking ECS cluster: $CLUSTER_NAME"
    
    if ! aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
        echo "🆕 Creating ECS cluster: $CLUSTER_NAME"
        aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
        
        # Add tags
        cluster_arn=$(aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION --query 'clusters[0].clusterArn' --output text)
        aws ecs tag-resource --resource-arn $cluster_arn --tags key=Service,value=PetPlantr key=Component,value=GPU-Inference --region $AWS_REGION
    else
        echo "✅ ECS cluster exists: $CLUSTER_NAME"
    fi
}

# Function to create CloudWatch log groups
create_log_groups() {
    local services=("feature-extraction" "depth-estimation" "shape-mvd")
    
    echo ""
    echo "📊 Creating CloudWatch log groups..."
    
    for service in "${services[@]}"; do
        local log_group="/ecs/petplantr-$service"
        
        if ! aws logs describe-log-groups --log-group-name-prefix $log_group --region $AWS_REGION --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$log_group"; then
            echo "🆕 Creating log group: $log_group"
            aws logs create-log-group --log-group-name $log_group --region $AWS_REGION
            aws logs put-retention-policy --log-group-name $log_group --retention-in-days 30 --region $AWS_REGION
        else
            echo "✅ Log group exists: $log_group"
        fi
    done
}

# Main deployment function
main() {
    echo "📍 Working directory: $(pwd)"
    echo "🌍 AWS Region: $AWS_REGION"
    echo "🏷️  AWS Account: $AWS_ACCOUNT_ID"
    echo ""
    
    # Create infrastructure
    create_ecs_cluster
    create_log_groups
    
    # Build and deploy containers
    echo ""
    echo "🐳 Building and deploying containers..."
    
    build_and_push "feature-extraction"
    register_task_definition "feature-extraction"
    
    build_and_push "depth-estimation"
    register_task_definition "depth-estimation"
    
    build_and_push "shape-mvd"
    register_task_definition "shape-mvd"
    
    echo ""
    echo "🎉 GPU Container Deployment Complete!"
    echo "=================================="
    echo ""
    echo "✅ Infrastructure:"
    echo "   • ECS Cluster: $CLUSTER_NAME"
    echo "   • CloudWatch log groups created"
    echo ""
    echo "✅ Container Images:"
    echo "   • Feature Extraction: $ECR_REGISTRY/petplantr-feature-extraction:latest"
    echo "   • Depth Estimation: $ECR_REGISTRY/petplantr-depth-estimation:latest"
    echo "   • Shape-MVD: $ECR_REGISTRY/petplantr-shape-mvd:latest"
    echo ""
    echo "✅ ECS Task Definitions:"
    echo "   • petplantr-feature-extraction"
    echo "   • petplantr-depth-estimation"
    echo "   • petplantr-shape-mvd"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Update Step Functions definition to use ECS tasks"
    echo "2. Deploy EC2 instances with GPU support to ECS cluster"
    echo "3. Test the GPU-powered AI pipeline"
    echo ""
    echo "💡 To run a task manually:"
    echo "aws ecs run-task --cluster $CLUSTER_NAME --task-definition petplantr-feature-extraction --launch-type EC2"
    echo ""
}

# Check if running from correct directory
if [ ! -d "docker" ]; then
    echo "❌ Error: docker directory not found"
    echo "Please run this script from the backend directory"
    exit 1
fi

# Run main function
main
