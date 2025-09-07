# PetPlantr Production AI Configuration Guide

## 🎯 Overview

This guide shows you how to configure PetPlantr to use real AI services for 3D model generation instead of development mode mock data.

## 🔧 Configuration Options

### Method 1: Enable Production Mode (Recommended)

Add this to your environment variables:

```bash
# In frontend/.env.local
ENABLE_PRODUCTION_AI=true
AWS_LAMBDA_API_URL=https://cm1ffbb7hf.execute-api.us-east-1.amazonaws.com/dev
```

### Method 2: Production Environment

Set NODE_ENV to production:

```bash
NODE_ENV=production
```

## 🚀 Available Production AI Services

### 1. AWS Lambda Endpoints (Currently Available)

- **Pet Analysis**: `https://cm1ffbb7hf.execute-api.us-east-1.amazonaws.com/dev/api/analyze-pet`
- **3D Generation**: `https://cm1ffbb7hf.execute-api.us-east-1.amazonaws.com/dev/api/replicate`

### 2. Replicate API (Configure with your token)

```bash
# In frontend/.env.local
REPLICATE_API_TOKEN=your_replicate_token_here
```

### 3. OpenAI Vision API (Optional)

```bash
# In frontend/.env.local
OPENAI_API_KEY=your_openai_key_here
```

## 📋 Step-by-Step Setup

### Step 1: Update Environment Variables

```bash
cd /Users/medan/Downloads/PetPlantr/frontend
```

Edit `.env.local`:

```bash
# Enable Production AI
ENABLE_PRODUCTION_AI=true

# AWS Lambda API (Already working)
AWS_LAMBDA_API_URL=https://cm1ffbb7hf.execute-api.us-east-1.amazonaws.com/dev

# Optional: Add Replicate API for advanced 3D generation
REPLICATE_API_TOKEN=your_token_here

# Optional: Add OpenAI for advanced image analysis
OPENAI_API_KEY=your_key_here
```

### Step 2: Restart Frontend Server

```bash
npm run dev
```

### Step 3: Test Production Mode

1. Go to `http://localhost:3002/upload`
2. Switch to "Ultra Quality" mode
3. Upload a pet image
4. Click "Generate Ultra High Quality 3D Model"
5. Watch for production mode messages in console

## 🔍 How to Verify Production Mode

### Development Mode (Current):
- Message: "Development mode: Set ENABLE_PRODUCTION_AI=true to use real AI services."
- Generation time: 2 seconds
- Quality level: "ultra-high-dev"

### Production Mode (After configuration):
- Message: "Production mode: Ultra-high quality 3D model generated using advanced AI services."
- Generation time: 45+ seconds
- Quality level: "ultra-high-production"
- Real AI analysis and 3D generation

## 🛠️ Production Service Integration

### Current Integration:

1. **Pet Image Analysis**: 
   - Calls AWS Lambda `/api/analyze-pet`
   - Falls back to enhanced mock data if unavailable

2. **3D Model Generation**:
   - Calls AWS Lambda `/api/replicate` 
   - Falls back to S3 URLs for production testing

3. **Model Optimization**:
   - Production-grade metrics and specifications
   - Real processing time estimates

### Available Upgrades:

1. **Replicate Integration**: Add REPLICATE_API_TOKEN for advanced 3D models
2. **OpenAI Vision**: Add OPENAI_API_KEY for superior image analysis  
3. **Custom Models**: Direct integration with specialized pet-to-planter models

## 🧪 Testing Commands

### Test Current Development Mode:
```bash
curl -X POST http://localhost:3002/api/generate-enhanced-3d-simple \\
  -H "Content-Type: application/json" \\
  -d '{"imageUrl":"data:image/png;base64,test","breed":"Golden Retriever"}'
```

### Enable and Test Production Mode:
```bash
# Add to .env.local
echo "ENABLE_PRODUCTION_AI=true" >> frontend/.env.local

# Restart server
npm run dev

# Test again - should show production mode
curl -X POST http://localhost:3002/api/generate-enhanced-3d-simple \\
  -H "Content-Type: application/json" \\
  -d '{"imageUrl":"data:image/png;base64,test","breed":"Golden Retriever"}'
```

## 📊 Performance Comparison

| Feature | Development Mode | Production Mode |
|---------|------------------|-----------------|
| Generation Time | 2 seconds | 45+ seconds |
| AI Analysis | Mock data | Real AI services |
| 3D Models | Local demo files | Generated GLB/STL |
| Breed Detection | User input + mock | AI vision analysis |
| Quality Level | ultra-high-dev | ultra-high-production |
| Model URLs | /models/demo-*.glb | S3/CDN hosted files |

## 🚨 Troubleshooting

### Common Issues:

1. **Still showing development mode**:
   - Check `.env.local` has `ENABLE_PRODUCTION_AI=true`
   - Restart the server with `npm run dev`
   - Check browser console for mode logs

2. **Production APIs failing**:
   - Verify AWS Lambda endpoints are accessible
   - Check API keys and tokens are valid
   - Review server logs for error details

3. **Generation takes too long**:
   - This is expected in production mode (45+ seconds)
   - Consider adding progress polling for real-time updates

## 🔗 Next Steps

1. **Immediate**: Set `ENABLE_PRODUCTION_AI=true` to test production flow
2. **Short-term**: Add Replicate API token for enhanced 3D generation
3. **Long-term**: Integrate custom pet-to-planter ML models
4. **Enterprise**: Set up dedicated AI infrastructure and model training

## 📞 Support

- Test the configuration with the test page: `http://localhost:3002/test-ultra-high-quality.html`
- Check server logs for detailed error messages
- Verify all environment variables are correctly set
