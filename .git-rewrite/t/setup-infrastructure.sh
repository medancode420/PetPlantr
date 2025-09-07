#!/bin/bash
# Infrastructure Setup Script for PetPlantr
# This script helps automate the infrastructure deployment

set -e

echo "🚀 PetPlantr Infrastructure Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    commands=("terraform" "aws" "node" "npm")
    missing=()
    
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing[*]}"
        echo "Please install them and run this script again."
        echo ""
        echo "Installation guide:"
        echo "- Terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli"
        echo "- AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
        echo "- Node.js: https://nodejs.org/"
        exit 1
    fi
    
    print_success "All required tools are installed"
}

# Setup AWS credentials
setup_aws() {
    print_status "Setting up AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        print_warning "AWS credentials not configured"
        echo "Please run: aws configure"
        echo "You'll need:"
        echo "- AWS Access Key ID"
        echo "- AWS Secret Access Key"
        echo "- Default region (e.g., us-east-1)"
        read -p "Press Enter after configuring AWS credentials..."
    else
        print_success "AWS credentials are configured"
    fi
}

# Deploy Terraform infrastructure
deploy_terraform() {
    print_status "Deploying Terraform infrastructure..."
    
    cd infra
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan -out=tfplan
    
    echo ""
    print_warning "Review the Terraform plan above"
    read -p "Do you want to apply these changes? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        terraform apply tfplan
        print_success "Terraform infrastructure deployed"
        
        # Get outputs
        echo ""
        print_status "Infrastructure outputs:"
        terraform output
        
        # Save outputs to file
        terraform output -json > ../terraform_outputs.json
        print_success "Outputs saved to terraform_outputs.json"
    else
        print_warning "Terraform deployment cancelled"
    fi
    
    cd ..
}

# Setup environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    if [ ! -f ".env.local" ]; then
        cp .env.template .env.local
        print_success "Created .env.local from template"
        print_warning "Please edit .env.local with your actual values"
    else
        print_warning ".env.local already exists"
    fi
    
    # Extract Terraform outputs if available
    if [ -f "terraform_outputs.json" ]; then
        print_status "Updating .env.local with Terraform outputs..."
        
        # Extract values from Terraform outputs
        S3_BUCKET=$(jq -r '.s3_bucket_name.value' terraform_outputs.json)
        CLOUDFRONT_DOMAIN=$(jq -r '.cloudfront_domain_name.value' terraform_outputs.json)
        
        # Update .env.local
        sed -i '' "s/AWS_S3_BUCKET=.*/AWS_S3_BUCKET=$S3_BUCKET/" .env.local
        sed -i '' "s/CLOUDFRONT_DOMAIN=.*/CLOUDFRONT_DOMAIN=$CLOUDFRONT_DOMAIN/" .env.local
        sed -i '' "s|CDN_BASE_URL=.*|CDN_BASE_URL=https://$CLOUDFRONT_DOMAIN|" .env.local
        
        print_success "Updated .env.local with infrastructure values"
    fi
}

# Setup Stripe webhook
setup_stripe_webhook() {
    print_status "Setting up Stripe webhook..."
    
    echo "To complete Stripe setup:"
    echo "1. Go to https://dashboard.stripe.com/webhooks"
    echo "2. Click 'Add endpoint'"
    echo "3. Use URL: https://your-app.vercel.app/api/webhooks/stripe"
    echo "4. Select events: payment_intent.succeeded, payment_intent.payment_failed"
    echo "5. Copy the webhook secret to your .env.local"
    echo ""
    read -p "Press Enter when you've completed the Stripe webhook setup..."
}

# Main execution
main() {
    echo ""
    print_status "Starting infrastructure setup..."
    echo ""
    
    check_requirements
    setup_aws
    deploy_terraform
    setup_env
    setup_stripe_webhook
    
    echo ""
    print_success "Infrastructure setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Update .env.local with your API keys:"
    echo "   - REPLICATE_API_TOKEN"
    echo "   - STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY"
    echo "   - STRIPE_WEBHOOK_SECRET"
    echo ""
    echo "2. Deploy your Next.js app to Vercel:"
    echo "   vercel deploy"
    echo ""
    echo "3. Test the full pipeline:"
    echo "   npm run dev"
    echo ""
}

# Run main function
main "$@"
