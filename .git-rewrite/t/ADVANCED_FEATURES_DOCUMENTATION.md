# PetPlantr API - Advanced Features Documentation

## 🚀 Enhanced Features Overview

The PetPlantr 3D model generation API has been significantly enhanced with production-ready features including real-time progress tracking, intelligent caching, advanced security, quality assurance, and comprehensive analytics.

## 📋 Table of Contents

1. [Image Preprocessing Pipeline](#image-preprocessing-pipeline)
2. [Security & Rate Limiting](#security--rate-limiting)
3. [Performance Optimization](#performance-optimization)
4. [Quality Assurance System](#quality-assurance-system)
5. [Intelligent Caching](#intelligent-caching)
6. [Analytics & Monitoring](#analytics--monitoring)
7. [Batch Processing](#batch-processing)
8. [Real-time Progress Tracking](#real-time-progress-tracking)
9. [Advanced Configuration Options](#advanced-configuration-options)
10. [Testing & Validation](#testing--validation)

---

## 🔍 Image Preprocessing Pipeline

### Features
- **Automatic format detection** and optimization
- **Noise reduction** for clearer input images
- **Color optimization** for better AI analysis
- **Edge enhancement** for improved 3D reconstruction
- **Resolution upscaling** (optional)
- **Compression optimization** based on quality tier

### Usage
```json
{
  "imageUrl": "https://example.com/dog.jpg",
  "advancedOptions": {
    "enhanceClarity": true,
    "optimizeColors": true,
    "enhanceEdges": true,
    "upscaleResolution": false,
    "compressionLevel": "minimal"
  }
}
```

### Response
```json
{
  "preprocessingMetadata": {
    "originalUrl": "https://example.com/dog.jpg",
    "format": "jpg",
    "enhancementApplied": true,
    "noiseReduction": true,
    "colorOptimization": true,
    "edgeEnhancement": true
  }
}
```

---

## 🔒 Security & Rate Limiting

### Multi-Tier Rate Limiting
- **Standard Tier**: 50 requests/hour
- **Priority Tier**: 200 requests/hour (with API key)
- **Enterprise Tier**: 1000 requests/hour (with enterprise key)

### Security Features
- **IP-based rate limiting** with automatic blocking
- **DDOS protection** (100 requests/minute threshold)
- **Suspicious activity detection** (20 rapid requests)
- **IP whitelisting** support
- **Request fingerprinting** for abuse detection

### Headers
```bash
# Priority access
curl -H "X-Priority-Key: your-priority-key" \
     -H "Content-Type: application/json" \
     -d '{"imageUrl": "..."}' \
     http://localhost:3000/api/generate-enhanced-3d-simple

# Enterprise access
curl -H "X-Enterprise-Key: your-enterprise-key" \
     -H "Content-Type: application/json" \
     -d '{"imageUrl": "..."}' \
     http://localhost:3000/api/generate-enhanced-3d-simple
```

### Rate Limit Response
```json
{
  "error": "Rate limit exceeded",
  "retryAfter": 3600,
  "tier": "standard",
  "requestId": "req_abc123",
  "suggestion": "Consider upgrading to priority tier for higher limits"
}
```

---

## ⚡ Performance Optimization

### Quality-Based Settings
Each quality tier has optimized settings for performance vs quality:

#### Draft Quality
- **Timeout**: 15 seconds
- **Retry attempts**: 0
- **Memory optimization**: Aggressive
- **GPU acceleration**: Disabled

#### Standard Quality
- **Timeout**: 30 seconds
- **Retry attempts**: 1
- **Memory optimization**: Standard
- **GPU acceleration**: Disabled

#### Premium Quality
- **Timeout**: 60 seconds
- **Retry attempts**: 2
- **Memory optimization**: Standard
- **GPU acceleration**: Enabled
- **Parallel processing**: Enabled

#### Ultra Quality
- **Timeout**: 120 seconds
- **Retry attempts**: 3
- **Memory optimization**: Maximum quality
- **GPU acceleration**: Enabled
- **Parallel processing**: Enabled

### Configuration
```json
{
  "quality": "premium",
  "advancedOptions": {
    "optimizationLevel": "high",
    "useGpuAcceleration": true,
    "parallelProcessing": true,
    "memoryOptimization": "maximum_quality"
  }
}
```

---

## ✅ Quality Assurance System

### 7-Point Quality Checklist
1. **Model Geometry** (≥85% score required)
2. **Printability** (must be "excellent")
3. **Mesh Quality** (≥90% required)
4. **Texture Quality** (high-quality generation)
5. **Drainage Features** (planter holes present)
6. **Planter Integration** (perfect cavity integration)
7. **Breed Accuracy** (≥80% confidence)

### Quality Grades
- **Grade A**: 90-100% (Production ready)
- **Grade B**: 80-89% (Good quality)
- **Grade C**: 70-79% (Acceptable)
- **Grade D**: <70% (Needs improvement)

### Response Format
```json
{
  "qualityAssurance": {
    "score": 92.5,
    "grade": "A",
    "checks": {
      "modelGeometry": true,
      "printability": true,
      "meshQuality": true,
      "textureQuality": true,
      "drainageFeatures": true,
      "planterIntegration": true,
      "breedAccuracy": true
    },
    "recommendations": [],
    "passedChecks": 7,
    "totalChecks": 7
  }
}
```

---

## 💾 Intelligent Caching

### Features
- **MD5-based cache keys** for precise matching
- **LRU (Least Recently Used)** eviction policy
- **Cache hit tracking** and analytics
- **TTL (Time To Live)** of 1 hour
- **Automatic cleanup** when cache exceeds 1000 entries

### Cache Key Generation
Cache keys are generated from:
- Image URL
- All configuration options (sorted)
- Quality settings
- Advanced options

### Cache Analytics
```json
{
  "cached": true,
  "cacheHits": 5,
  "cacheMetrics": {
    "hitRate": 75.5,
    "totalEntries": 234,
    "avgHitsPerEntry": 3.2
  }
}
```

---

## 📊 Analytics & Monitoring

### Health Endpoint
```bash
GET /api/generate-enhanced-3d-simple?health=true
```

### Health Response
```json
{
  "status": "healthy",
  "timestamp": "2025-01-29T10:30:00.000Z",
  "metrics": {
    "cacheHitRate": 78.5,
    "avgProcessingTime": 12.3,
    "successRate": 94.2,
    "totalRequests": 1247
  }
}
```

### Analytics Endpoint
```bash
GET /api/generate-enhanced-3d-simple?analytics=true
```

### Analytics Response
```json
{
  "analytics": {
    "requests": 1247,
    "successRate": 0.942,
    "avgProcessingTime": 12.3,
    "topBreeds": ["Golden Retriever", "Labrador", "German Shepherd"],
    "popularOptions": [
      {"enhanceClarity": 89},
      {"optimizeColors": 76},
      {"highQuality": 45}
    ],
    "performanceMetrics": {
      "p95ResponseTime": 18.7,
      "errorRate": 5.8
    }
  }
}
```

---

## 🔄 Batch Processing

### Features
- Process up to **5 images** in a single request
- **Parallel processing** for efficiency
- **Individual error handling** per image
- **Consolidated results** with success/failure counts

### Request Format
```json
{
  "imageUrls": [
    "https://example.com/dog1.jpg",
    "https://example.com/dog2.jpg",
    "https://example.com/dog3.jpg"
  ],
  "quality": "standard",
  "breed": "Mixed Breed",
  "advancedOptions": {
    "batchOptimization": true
  }
}
```

### Response Format
```json
{
  "success": true,
  "batch": true,
  "totalImages": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "imageUrl": "https://example.com/dog1.jpg",
      "modelUrl": "/models/dog1_planter.glb",
      "success": true
    },
    {
      "imageUrl": "https://example.com/dog2.jpg",
      "modelUrl": "/models/dog2_planter.glb", 
      "success": true
    }
  ],
  "errors": [
    {
      "imageUrl": "https://example.com/dog3.jpg",
      "error": "Invalid image format"
    }
  ]
}
```

---

## 📈 Real-time Progress Tracking

### Features
- **Live progress updates** (0-100%)
- **Current step tracking** (preprocessing, analyzing, generating, etc.)
- **Estimated time remaining** calculation
- **Status monitoring** (queued, processing, complete, error)

### Progress States
1. **queued** - Request received and queued
2. **preprocessing** - Image enhancement and validation
3. **analyzing** - AI breed detection and analysis
4. **generating** - 3D model creation
5. **optimizing** - Model optimization and quality checks
6. **complete** - Processing finished successfully
7. **error** - Processing failed

### Progress Response
```json
{
  "requestId": "req_abc123",
  "progress": {
    "status": "generating",
    "progress": 65,
    "currentStep": "Converting image to 3D model",
    "estimatedTimeRemaining": 23,
    "startTime": 1706520600000
  }
}
```

---

## ⚙️ Advanced Configuration Options

### Complete Options List
```json
{
  "imageUrl": "https://example.com/dog.jpg",
  "quality": "premium",
  "breed": "Golden Retriever",
  "advancedOptions": {
    // Image Processing
    "enhanceClarity": true,
    "optimizeColors": true,
    "enhanceEdges": true,
    "upscaleResolution": false,
    
    // 3D Generation
    "includeColor": true,
    "textureSize": 1024,
    "meshSimplify": 0.95,
    "randomizeSeed": true,
    
    // Optimization
    "optimizationLevel": "high",
    "targetPolyCount": 20000,
    "minimizeSupports": true,
    
    // Planter Configuration
    "includeDrainage": true,
    "includeReservoir": false,
    "cavityDepth": "medium",
    "planterStyle": "classic",
    "planterSize": "standard",
    
    // Printing Settings
    "infillPercentage": "25%",
    "layerHeight": "0.2mm",
    "printSpeed": "60mm/s",
    "preferredMaterial": "PLA+",
    
    // Performance
    "useGpuAcceleration": true,
    "parallelProcessing": true,
    "memoryOptimization": "maximum_quality",
    
    // Output Formats
    "generateSTL": true,
    "generateOBJ": true,
    "generateThumbnails": true,
    "generateWireframe": true
  }
}
```

---

## 🧪 Testing & Validation

### Test Suite Features
The comprehensive test suite validates:

1. **Basic functionality** with enhanced options
2. **Batch processing** capabilities
3. **Intelligent caching** system
4. **Security features** and rate limiting
5. **Quality tiers** performance
6. **Analytics endpoints** accessibility
7. **Error handling** robustness
8. **Performance** under stress

### Running Tests
```bash
# Make the test script executable
chmod +x advanced_api_test_suite.py

# Run comprehensive tests
python3 advanced_api_test_suite.py

# Run basic functionality test only
python3 enhanced_api_test_v2.py
```

### Test Results Interpretation
- **All tests pass**: Production ready
- **80%+ pass**: Ready with minor issues
- **<80% pass**: Requires attention before production

---

## 🔧 Environment Variables

### Required Variables
```bash
# Core Configuration
NODE_ENV=production
ENABLE_PRODUCTION_AI=true

# API Keys
REPLICATE_API_TOKEN=your_replicate_token
PRIORITY_API_KEY=your_priority_key
ENTERPRISE_API_KEY=your_enterprise_key

# Services
AWS_LAMBDA_API_URL=https://your-lambda-url.amazonaws.com/dev
WEBHOOK_URL=https://your-webhook-endpoint.com/notify

# Security
WHITELISTED_IPS=192.168.1.100,10.0.0.50
```

### Optional Configuration
```bash
# Feature Flags
ENABLE_SMART_CACHING=true
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_QUALITY_ASSURANCE=true
ENABLE_REAL_TIME_PROGRESS=true
ENABLE_IMAGE_PREPROCESSING=true
ENABLE_SECURITY_FEATURES=true

# Performance Tuning
MAX_REQUESTS_PER_HOUR=50
PRIORITY_MAX_REQUESTS_PER_HOUR=200
ENTERPRISE_MAX_REQUESTS_PER_HOUR=1000
CACHE_TTL=3600
MAX_BATCH_SIZE=5
```

---

## 📈 Performance Benchmarks

### Response Times (Development Mode)
- **Draft Quality**: ~1-2 seconds
- **Standard Quality**: ~2-3 seconds
- **Premium Quality**: ~3-5 seconds
- **Ultra Quality**: ~5-8 seconds

### Response Times (Production Mode)
- **Draft Quality**: ~15-30 seconds
- **Standard Quality**: ~30-60 seconds
- **Premium Quality**: ~60-120 seconds
- **Ultra Quality**: ~120-300 seconds

### Cache Performance
- **Cache Hit Rate**: ~75-85% for repeated requests
- **Cache Response Time**: ~100-300ms
- **Memory Usage**: ~1-5MB per cached result

---

## 🚀 Production Deployment

### Pre-deployment Checklist
- [ ] All environment variables configured
- [ ] API keys validated and working
- [ ] Rate limiting configured appropriately
- [ ] Security features enabled
- [ ] Analytics endpoints secured (if needed)
- [ ] Webhook endpoints tested
- [ ] Cache storage configured (Redis recommended)
- [ ] Monitoring and alerting set up

### Monitoring Recommendations
- Monitor **success rates** (target: >95%)
- Track **response times** by quality tier
- Watch **cache hit rates** (target: >70%)
- Monitor **rate limit violations**
- Track **security events** and blocked IPs
- Monitor **resource usage** (CPU, memory, storage)

---

## 🔗 Related Documentation
- [API Testing Guide](./API_TESTING_GUIDE.md)
- [Enhanced API V2 Features](./ENHANCED_API_V2_COMPLETE.md)
- [Basic API Documentation](./ENHANCED_API_COMPLETE.md)

---

*Last updated: January 29, 2025*
*API Version: 2.1 (Advanced Features)*
