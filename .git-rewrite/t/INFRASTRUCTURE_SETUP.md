# 🚀 PetPlantr Enhanced AI Infrastructure Setup Guide

This guide covers the complete infrastructure setup for PetPlantr's enhanced AI features (Epic E-4), including Replicate/Shap-E integration, AWS S3/CloudFront CDN, Stripe payments, and 3D model viewer.

## 📋 Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured
- [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) installed
- [Node.js](https://nodejs.org/) 18+ and npm
- [GitHub CLI](https://cli.github.com/) (optional)
- Active accounts: AWS, Stripe, Replicate

## 🏗️ Infrastructure Components

### 1️⃣ Replicate + Shap-E Integration (PP-107, PP-102)

**Purpose**: AI-powered 3D model generation from pet photos

#### Setup Steps:

```bash
# 1. Create Replicate account and get API token
# Visit: https://replicate.com/account/api-tokens

# 2. Test API connection
curl -s -H "Authorization: Token $REPLICATE_API_TOKEN" \
  -d '{"version":"mareko/shap-e:db21...","input":{"image":"https://example.com/puppy.jpg"}}' \
  https://api.replicate.com/v1/predictions

# 3. Add to environment variables
echo "REPLICATE_API_TOKEN=r8_your_token_here" >> frontend/.env.local
```

#### API Endpoints:
- `POST /api/replicate` - Start 3D generation
- `GET /api/replicate?id={predictionId}` - Check status

### 2️⃣ AWS S3 + CloudFront CDN (PP-108)

**Purpose**: Fast, global delivery of 3D GLB model files

#### Automated Setup:

```bash
# Run the infrastructure setup script
./setup-infrastructure.sh

# Or manually with Terraform
cd infra
terraform init
terraform plan
terraform apply
```

#### Manual Setup:

```bash
# 1. Deploy infrastructure
make deploy-terraform

# 2. Get outputs
terraform output -json > ../terraform_outputs.json

# 3. Update environment variables
# CLOUDFRONT_DOMAIN and S3_BUCKET will be set automatically
```

#### Configuration Details:

- **S3 Bucket**: `petplantr-3d-models-prod`
- **CloudFront**: Global CDN with 24hr cache for GLB files
- **CORS**: Configured for web viewer access
- **Security**: Origin Access Control (OAC) for S3 protection

### 3️⃣ Stripe Checkout Integration (PP-105)

**Purpose**: Process payments for 3D printing services

#### Setup Steps:

```bash
# 1. Create Stripe account and get API keys
# Visit: https://dashboard.stripe.com/apikeys

# 2. Create product and price
# Product: "Custom Pet Planter 3D Print"
# Price: $45.00 one-time payment

# 3. Setup webhook endpoint
# URL: https://your-app.vercel.app/api/stripe/webhook
# Events: checkout.session.completed, payment_intent.succeeded, payment_intent.payment_failed

# 4. Add environment variables
cat >> frontend/.env.local << EOF
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_ID=price_your_price_id
EOF
```

#### API Endpoints:
- `POST /api/stripe/checkout` - Create checkout session
- `GET /api/stripe/checkout?session_id=...` - Get session status
- `POST /api/stripe/webhook` - Handle payment events

### 4️⃣ 3D Model Viewer (PP-104)

**Purpose**: Interactive 3D preview of generated models

#### Implementation:

The 3D viewer is implemented using React Three Fiber and model-viewer components:

```typescript
// Already implemented in /app/3d-viewer/[id]/page.tsx
<Suspense fallback={<Spinner />}>
  <Model url={`${process.env.NEXT_PUBLIC_CDN_URL}/${id}.glb`} />
</Suspense>
```

#### Features:
- Interactive orbit controls
- Loading states
- Mobile-responsive
- CDN-optimized delivery

## 🔧 Environment Configuration

### Frontend Environment Variables

Create `frontend/.env.local` with these values:

```bash
# Authentication (already configured)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_key
CLERK_SECRET_KEY=sk_test_your_clerk_key

# Replicate AI
REPLICATE_API_TOKEN=r8_your_replicate_token
NEXT_PUBLIC_REPLICATE_API_TOKEN=r8_your_replicate_token

# AWS Storage
AWS_ACCESS_KEY_ID=AKIA_your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=petplantr-3d-models-prod
NEXT_PUBLIC_CLOUDFRONT_DOMAIN=d1234567890123.cloudfront.net
NEXT_PUBLIC_CDN_BASE_URL=https://d1234567890123.cloudfront.net

# Stripe Payments
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_ID=price_your_price_id

# Application URLs
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

## 🚀 Deployment

### 1. Deploy Infrastructure

```bash
# Automated setup
make setup-infra

# Manual Terraform deployment
make deploy-terraform
```

### 2. Deploy Frontend

```bash
# Install dependencies
cd frontend && npm install

# Build and deploy to Vercel
make deploy-vercel
```

### 3. Configure DNS (Optional)

```bash
# Add CNAME record for custom CDN domain
# cdn.petplantr.com → d1234567890123.cloudfront.net
```

## 🧪 Testing

### Run E2E Tests

```bash
# Install Cypress and run tests
cd frontend
npm install cypress --save-dev
npm run cypress:run

# Or use Makefile
make e2e-test
```

### Test Full Workflow

```bash
# 1. Start development server
make frontend-dev

# 2. Run end-to-end test suite
make qa-full

# 3. Test specific user journey
npm run cypress:open
```

## 📊 Sprint Management

### Generate Burndown Chart

```bash
# Generate Sprint 1 burndown chart
export GITHUB_TOKEN=your_github_token
make sprint-report

# View chart at: reports/sprint_burndown.png
```

### Sprint 1 Issues (Capacity: 13 SP)

Move these issues to Sprint 1 board:

| Issue | SP | Epic | Description |
|-------|----|----- |-------------|
| PP-107 | 2 | E-4 | Replicate API setup |
| PP-101 | 3 | E-4 | Enhanced upload UI |
| PP-102 | 5 | E-4 | Shap-E integration |
| PP-105 | 3 | E-4 | Stripe checkout |

```bash
# Seed enhanced AI issues
make issue-seed-enhanced
```

## 🎯 Success Criteria (72-hour timeline)

### ✅ Technical Deliverables

1. **Photo → GLB Pipeline**: ≤15 second round-trip time
2. **3D Preview**: Browser-based GLB rendering
3. **Payment Flow**: Stripe test card processing (4242 4242 4242 4242)
4. **File Delivery**: STL download from S3/CDN

### ✅ QA Gates

```bash
# Automated QA pipeline
make prod-check

# Manual verification checklist:
# □ Upload photo → see processing indicator
# □ AI generates GLB → stored on S3
# □ 3D preview loads in browser
# □ Checkout creates Stripe session
# □ Webhook processes payment
# □ User receives download link
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Replicate API Errors
```bash
# Check API token
curl -H "Authorization: Token $REPLICATE_API_TOKEN" https://api.replicate.com/v1/models

# Verify model version exists
curl https://api.replicate.com/v1/models/openai/shap-e
```

#### 2. S3 Upload Failures
```bash
# Test AWS credentials
aws sts get-caller-identity

# Check bucket permissions
aws s3 ls s3://petplantr-3d-models-prod
```

#### 3. Stripe Webhook Issues
```bash
# Test webhook endpoint
curl -X POST https://your-app.vercel.app/api/stripe/webhook \
  -H "stripe-signature: test" \
  -d '{}'

# Check webhook logs in Stripe dashboard
```

#### 4. CloudFront Cache Issues
```bash
# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890123 \
  --paths "/*"
```

## 📚 Additional Resources

- [Replicate API Documentation](https://replicate.com/docs)
- [AWS S3 + CloudFront Setup](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.html)
- [Stripe Checkout Integration](https://stripe.com/docs/checkout/quickstart)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)

## 🆘 Support

For issues with this setup:

1. Check the troubleshooting section above
2. Review environment variable configuration
3. Verify all API keys and tokens are valid
4. Run `make qa-full` to identify specific failures
5. Check logs in Vercel, Stripe, and AWS consoles

---

**🎉 Ready to build amazing pet planters with AI!**
