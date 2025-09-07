# Enhanced 3D Model Generation API - Testing Guide

## Quick Start

The enhanced API endpoint is available at: `POST /api/generate-enhanced-3d-simple`

### Prerequisites
1. Start the Next.js development server:
   ```bash
   cd /Users/medan/Downloads/PetPlantr/frontend
   npm run dev
   ```
   The server will run on http://localhost:3003 (or another port if 3000 is in use)

## Basic Testing with curl

### 1. Basic Request (Standard Quality)
```bash
curl -X POST http://localhost:3003/api/generate-enhanced-3d-simple \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://example.com/dog.jpg",
    "quality": "standard"
  }' | jq .
```

### 2. Premium Quality with Advanced Options
```bash
curl -X POST http://localhost:3003/api/generate-enhanced-3d-simple \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://example.com/husky.jpg",
    "quality": "premium",
    "advancedOptions": {
      "geometry": {
        "resolution": 1024,
        "smoothing": true,
        "optimization": "quality"
      },
      "planter": {
        "drainageHoles": true,
        "waterReservoir": true,
        "plantCompatibility": ["succulents", "herbs"]
      },
      "customization": {
        "scaleAdjustment": 1.2,
        "personalizedEngraving": "My Dog Planter"
      }
    }
  }' | jq .
```

### 3. Ultra Quality - All Features
```bash
curl -X POST http://localhost:3003/api/generate-enhanced-3d-simple \
  -H "Content-Type: application/json" \
  -d '{
    "imageUrl": "https://example.com/german-shepherd.jpg",
    "quality": "ultra",
    "advancedOptions": {
      "geometry": {
        "resolution": 2048,
        "detailLevel": "maximum",
        "meshComplexity": "high"
      },
      "planter": {
        "size": "extra_large",
        "wallThickness": 4.0,
        "rimDesign": "decorative"
      },
      "ai": {
        "enhancedBreedDetection": true,
        "anatomicalAccuracy": "high"
      }
    }
  }' | jq .
```

## Error Testing

### Invalid URL
```bash
curl -X POST http://localhost:3003/api/generate-enhanced-3d-simple \
  -H "Content-Type: application/json" \
  -d '{"imageUrl": "invalid-url", "quality": "standard"}' | jq .
```

### Invalid Quality Level
```bash
curl -X POST http://localhost:3003/api/generate-enhanced-3d-simple \
  -H "Content-Type: application/json" \
  -d '{"imageUrl": "https://example.com/dog.jpg", "quality": "invalid"}' | jq .
```

### Missing Required Field
```bash
curl -X POST http://localhost:3003/api/generate-enhanced-3d-simple \
  -H "Content-Type: application/json" \
  -d '{"quality": "standard"}' | jq .
```

## Advanced Options Reference

The API supports 25+ advanced customization options:

### Geometry Options
- `resolution`: 256, 512, 1024, 2048
- `smoothing`: true/false
- `optimization`: "speed", "quality", "balanced"
- `detailLevel`: "low", "medium", "high", "ultra-high", "maximum"
- `surfaceFinish`: "smooth", "textured", "matte"
- `meshComplexity`: "low", "medium", "high"

### Planter Options
- `drainageHoles`: true/false
- `waterReservoir`: true/false
- `plantCompatibility`: ["succulents", "herbs", "small_flowers", "all_plants"]
- `size`: "small", "medium", "large", "extra_large"
- `wallThickness`: 2.0-5.0 (mm)
- `baseType`: "flat", "stable", "weighted"
- `rimDesign`: "simple", "decorative", "functional"

### Printing Options
- `supportGeneration`: "none", "minimal", "tree", "touching"
- `overhangOptimization`: true/false
- `hollowPercentage`: 0-30
- `printOrientation`: "auto", "optimal", "strength"
- `layerOptimization`: true/false

### Customization Options
- `scaleAdjustment`: 0.5-2.0
- `colorPreservation`: true/false
- `textureDetail`: "low", "medium", "high", "ultra"
- `personalizedEngraving`: string
- `breedAccentuation`: true/false

### Quality Options
- `meshDensity`: "low", "medium", "high", "ultra-high", "maximum"
- `geometryPrecision`: "standard", "high", "maximum", "professional"
- `surfaceSmoothing`: true/false
- `edgeRefinement`: true/false
- `watertightValidation`: true/false

### AI Options
- `enhancedBreedDetection`: true/false
- `anatomicalAccuracy`: "standard", "high", "maximum"
- `expressionPreservation`: true/false
- `proportionOptimization`: true/false

## Expected Response Structure

Successful responses include:
- `success`: true
- `modelUrl`: GLB file URL
- `stlUrl`: STL file URL  
- `objUrl`: OBJ file URL
- `thumbnailUrl`: Preview image URL
- `breedAnalysis`: Detailed breed detection results
- `qualityMetrics`: Generation quality scores
- `metadata`: 3D printing information
- `generationDetails`: Processing information
- `processingTime`: Generation duration
- `estimatedCost`: Cost estimate

## Production vs Development Mode

- **Production Mode**: Uses real AI services (Replicate TRELLIS, FLUX, AWS Lambda)
- **Development Mode**: Returns enhanced mock data for testing

Mode is controlled by environment variables in `.env.local`.

## Rate Limiting

- 50 requests per hour per IP address
- Rate limit headers included in responses
- 429 status code when limit exceeded

## Python Test Script

For comprehensive testing, run:
```bash
python3 test_api_comprehensive.py
```

This tests all features, error conditions, and validates response structure.
