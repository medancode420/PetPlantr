# 🚩 Vercel Environment Variables Checklist

## Required for Production Deployment

Copy these environment variables to Vercel Project → Settings → Environment Variables
**Mark all as "Production & Preview" ✅ so local/preview links work too**

### Core API Keys
```bash
REPLICATE_API_TOKEN=r8_OeKP1Fak16l2csjbzavBnE5na4YaQrc2KL8kF
NEXT_PUBLIC_REPLICATE_API_TOKEN=r8_OeKP1Fak16l2csjbzavBnE5na4YaQrc2KL8kF
```

### AWS Infrastructure  
```bash
AWS_ACCESS_KEY_ID=AKIAZ45ZTTSJ655P6OUO
AWS_SECRET_ACCESS_KEY=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
AWS_REGION=us-east-1
AWS_S3_BUCKET=petplantr-3d-models-prod
AWS_S3_REGION=us-east-1
```

### CloudFront CDN
```bash
NEXT_PUBLIC_CLOUDFRONT_DOMAIN=dpa0b9puwj06h.cloudfront.net
NEXT_PUBLIC_CDN_BASE_URL=https://dpa0b9puwj06h.cloudfront.net
CLOUDFRONT_URL=https://dpa0b9puwj06h.cloudfront.net
```

### Stripe Payment (Test Keys)
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### Authentication (Clerk)
```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_aHVtb3JvdXMtaGVyb24tODQuY2xlcmsuYWNjb3VudHMuZGV2JA
CLERK_SECRET_KEY=sk_test_8C40EKYyeXd2EE0Ra4gYYOokXdC7kHFAMtDAt6tkw5
```

### App Configuration
```bash
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
NEXTAUTH_URL=https://your-app.vercel.app
NEXTAUTH_SECRET=your_nextauth_secret
```

## ✅ Verification Commands

After setting in Vercel, test locally:
```bash
# Test Replicate API
curl -H "Authorization: Token $REPLICATE_API_TOKEN" https://api.replicate.com/v1/models | head -5

# Test AWS S3 access  
aws s3 ls s3://petplantr-3d-models-prod/

# Test CloudFront
curl -I https://dpa0b9puwj06h.cloudfront.net/
```

## 🚀 Deployment Commands
```bash
cd frontend
vercel --prod --confirm
```
