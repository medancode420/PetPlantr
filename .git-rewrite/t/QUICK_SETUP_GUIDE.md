# 🚀 Quick Setup Guide for PetPlantr Real AI Models

## 🎯 IMMEDIATE NEXT STEPS

### Option A: Test Locally First (Recommended)

1. **Get Replicate API Token**:
   ```bash
   # 1. Go to: https://replicate.com/account/api-tokens
   # 2. Sign up/login if needed
   # 3. Create new token or copy existing one
   # 4. Add billing info (required for API usage)
   ```

2. **Set Up Local Environment**:
   ```bash
   cd /Users/medan/Downloads/PetPlantr
   chmod +x test_local.sh
   ./test_local.sh
   ```

3. **Edit .env.local** (when prompted):
   ```bash
   # Replace this line in .env.local:
   REPLICATE_API_TOKEN=your_replicate_api_token_here
   # With your actual token:
   REPLICATE_API_TOKEN=r8_abc123your_actual_token_here
   ```

4. **Run Local Test Again**:
   ```bash
   ./test_local.sh
   ```

5. **Expected Local Results**:
   - ✅ Pipeline: "real"
   - ✅ hasReplicateToken: true
   - ✅ Server running on http://localhost:3000

### Option B: Deploy to Production Directly

1. **Vercel Deployment**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Find PetPlantr project → Settings → Environment Variables
   - Add: `REPLICATE_API_TOKEN` = `your_token`
   - Force redeploy from Deployments tab

2. **Test Production**:
   - Wait 2-3 minutes after redeploy
   - Open: https://petplantr.vercel.app/api/health
   - Should show: `"pipeline": "real"`, `"hasReplicateToken": true`

## 🎯 SUCCESS CRITERIA

When working correctly, you should see:

### Health Endpoint Response:
```json
{
  "status": "ok",
  "pipeline": "real",
  "environment": {
    "hasReplicateToken": true
  },
  "models": [
    "cjwbw/shap-e (hardcoded version: 5957069...)",
    "cjwbw/point-e (hardcoded version: 1a4da7a...)"
  ],
  "message": "PetPlantr API is running with REAL AI models - NO DEMO FALLBACK"
}
```

### API Generation Response:
```json
{
  "success": true,
  "status": "processing",
  "usedModel": "cjwbw/shap-e",
  "threeDPredictionId": "pred_abc123...",
  "conceptImage": "https://..."
}
```

## 🚨 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| `hasReplicateToken: false` | Add REPLICATE_API_TOKEN to environment |
| `pipeline: undefined` | Code not deployed - force redeploy |
| `Failed to fetch` | Environment missing or deployment incomplete |
| Local test fails | Check .env.local has real token, run `npm install` |

## 🔄 After Local Testing Works

Once local testing shows real AI models working:

1. **Deploy to Production** with same environment variables
2. **Test production** with health endpoint
3. **Generate real 3D models** in production
4. **You're done!** 🎉

---

**Start with local testing to confirm everything works before production deployment.**
