# 🚀 PetPlantr Production Deployment Guide

## Quick Deploy (Recommended)

### Option 1: One-Click Vercel Deploy
```bash
# 1. Build and test locally
npm run build

# 2. Deploy to Vercel
vercel --prod

# 3. Set environment variables in Vercel dashboard
# Go to: https://vercel.com/dashboard -> Your Project -> Settings -> Environment Variables
```

### Option 2: Deploy with GitHub Integration
1. Push to main branch on GitHub
2. Connect repository to Vercel
3. Auto-deploy on every push

## Environment Variables Setup

### Required Production Variables (Set in Vercel Dashboard):
```bash
# AI Services
REPLICATE_API_TOKEN=r8_your_production_token_here

# AWS S3 Storage  
AWS_ACCESS_KEY_ID=your_production_aws_access_key
AWS_SECRET_ACCESS_KEY=your_production_aws_secret_key
AWS_S3_BUCKET=petplantr-production-assets
NEXT_PUBLIC_CLOUDFRONT_DOMAIN=cdn.petplantr.com

# Stripe Payments
STRIPE_SECRET_KEY=sk_live_your_production_stripe_secret
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_production_stripe_key

# Authentication  
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your_clerk_key
CLERK_SECRET_KEY=sk_live_your_clerk_secret

# App Configuration
NEXT_PUBLIC_APP_URL=https://petplantr.com
NODE_ENV=production
```

## Pre-Deployment Checklist

- [ ] ✅ Build passes locally (`npm run build`)
- [ ] ✅ All tests pass (`npm run test`)  
- [ ] ✅ Environment variables configured
- [ ] ✅ Domain configured (optional)
- [ ] ✅ S3 bucket and CloudFront set up
- [ ] ✅ Replicate API credits available
- [ ] ✅ Stripe account configured

## Post-Deployment Checklist

- [ ] Test live site: https://your-deployment-url.vercel.app
- [ ] Upload a test image and verify AI generation
- [ ] Test 3D model viewer
- [ ] Test download STL functionality  
- [ ] Test Stripe checkout (use test mode first)
- [ ] Run production health check
- [ ] Monitor error logs
- [ ] Set up domain (if custom)

## Monitoring & Maintenance

### Health Check
```bash
# Run production health check
./scripts/production_health_check.sh https://your-deployment-url.vercel.app
```

### View Logs
```bash
# View deployment logs
vercel logs https://your-deployment-url.vercel.app
```

### Update Deployment
```bash
# Deploy updates
git push origin main  # Auto-deploy if GitHub connected
# OR
vercel --prod  # Manual deploy
```

## Troubleshooting

### Common Issues:

**Build Failures:**
- Check environment variables are set
- Verify all dependencies are installed
- Check TypeScript errors

**API Errors:**  
- Verify Replicate API token and credits
- Check AWS S3 permissions
- Confirm environment variables in Vercel

**3D Viewer Issues:**
- Ensure GLB files are properly served
- Check CORS headers for model files
- Verify model-viewer dependencies

**Payment Issues:**
- Confirm Stripe keys (test vs production)
- Check webhook endpoints
- Verify Stripe account setup

## Success Metrics

### Expected Performance:
- ⚡ Page load: < 3 seconds
- 🤖 AI generation: 5-10 seconds  
- 📦 Model loading: < 5 seconds
- 💳 Checkout: < 30 seconds

### Monitor:
- User conversion rates
- AI generation success rates
- Error rates and types
- Performance metrics

---

🎉 **Ready to launch!** Your AI-powered pet planter platform is production-ready!
