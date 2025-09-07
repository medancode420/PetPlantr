# Backend-Frontend API Endpoint Alignment

## Current Endpoint Mismatches and Solutions

### 1. Upload Endpoints

**Frontend Expectation:**
- `POST /api/upload` - Direct file upload

**Backend Reality:**
- `POST /api/presign` - Returns presigned URLs for S3 upload

**Solution:** Create a unified upload endpoint in the backend.

### 2. AI Processing Endpoints

**Frontend Calls:**
- `POST /api/analyze-pet` - Pet breed analysis
- `POST /api/replicate` - 3D model generation
- `POST /api/generate` - Alternative generation endpoint

**Backend Implementation:**
- No direct API Gateway endpoints for AI processing
- Lambda functions: `generateSTL`, `generateSTLEnhanced`

**Solution:** Add API Gateway routes for AI processing.

### 3. Health Check Endpoints

**Frontend Expectation:**
- `GET /api/health` - Health status check

**Backend Reality:**
- `GET /api/healthz` - Health check endpoint

**Solution:** Add `/api/health` alias or update frontend.

### 4. Checkout and Payment Endpoints

**Frontend Calls:**
- `POST /api/stripe/checkout` - Stripe checkout
- `POST /api/checkout` - Alternative checkout

**Backend Reality:**
- `POST /api/checkout` - Stripe checkout creation
- `POST /api/stripe/webhook` - Webhook handler

**Solution:** Add missing stripe/checkout endpoint.

## Implementation Plan

### Phase 1: Add Missing Backend Endpoints

1. **Add Upload Endpoint** - Direct file upload with S3 integration
2. **Add AI Processing Endpoints** - Pet analysis and 3D generation
3. **Add Health Endpoint Alias** - `/api/health` pointing to `/api/healthz`
4. **Add Stripe Checkout Endpoint** - `/api/stripe/checkout`

### Phase 2: Update Frontend to Use Correct Endpoints

1. **Update API calls** to match backend endpoints
2. **Add error handling** for endpoint mismatches
3. **Update environment variables** for API base URLs

### Phase 3: Add Missing Lambda Functions

1. **Pet Analysis Lambda** - For breed detection and analysis
2. **3D Generation Lambda** - For Replicate API integration
3. **File Upload Lambda** - For direct file handling

## Detailed Endpoint Mapping
