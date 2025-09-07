# Frontend Integration Guide for Enhanced Pipeline

## Overview
The enhanced API now returns real AI-generated assets. Here's how to integrate them into the frontend.

## API Response Changes

### Enhanced GET Response:
```typescript
interface EnhancedResponse {
  success: boolean;
  status: 'processing' | 'succeeded' | 'failed';
  modelUrl: string; // Now can be real CDN URL
  conceptImage?: string; // NEW: Real AI-generated concept image
  threeDPredictionId?: string; // NEW: For polling 3D generation
  pipeline: 'real' | 'demo' | 'hybrid'; // NEW: Pipeline indicator
  data: {
    s3ModelKey?: string; // NEW: S3 key for the model
    s3ConceptKey?: string; // NEW: S3 key for concept image
    threeDGeneration?: any; // NEW: 3D generation details
  };
  note?: string; // Enhanced status messages
}
```

## Frontend Updates Needed

### 1. Display Real Concept Image
```typescript
// In your upload component, after successful generation:
if (result.conceptImage) {
  // Show the real AI-generated concept image
  setConceptImageUrl(result.conceptImage);
}
```

### 2. Enhanced Status Polling
```typescript
// Poll with potential 3D prediction ID
const pollStatus = async (predictionId: string, threeDPredictionId?: string) => {
  const params = new URLSearchParams({ id: predictionId });
  if (threeDPredictionId) {
    params.append('threeDPredictionId', threeDPredictionId);
  }
  
  const response = await fetch(`/api/replicate?${params}`);
  const result = await response.json();
  
  // Handle different pipeline states
  switch (result.pipeline) {
    case 'real':
      // Both concept and 3D model are real
      break;
    case 'hybrid':
      // Real concept, demo 3D model
      break;
    case 'demo':
      // Demo mode fallback
      break;
  }
  
  return result;
};
```

### 3. Progressive Enhancement
```typescript
// Show progress based on pipeline phase
if (result.threeDPredictionId) {
  setStatusMessage('🎨 Generating 3D model from concept...');
  setShowConceptImage(true); // Show the generated concept
}
```

### 4. Checkout Integration
```typescript
// Pass real asset URLs to checkout
const checkoutData = {
  modelUrl: result.modelUrl, // Real or demo GLB
  conceptImage: result.conceptImage, // Real concept image
  pipeline: result.pipeline, // For analytics
  s3Keys: {
    model: result.data.s3ModelKey,
    concept: result.data.s3ConceptKey
  }
};
```

## Component Updates

### EnhancedUpload.tsx Changes:
```typescript
// Add new state
const [conceptImageUrl, setConceptImageUrl] = useState<string | null>(null);
const [pipelineType, setPipelineType] = useState<string>('unknown');

// In the polling logic
useEffect(() => {
  if (predictionId && result?.threeDPredictionId) {
    // Poll for 3D generation status
    pollWithThreeDId(predictionId, result.threeDPredictionId);
  }
}, [predictionId, result?.threeDPredictionId]);

// Display concept image if available
{conceptImageUrl && (
  <div className="concept-preview">
    <h3>AI-Generated Concept</h3>
    <img src={conceptImageUrl} alt="Pet planter concept" />
  </div>
)}
```

## Testing the Integration

### 1. Run Enhanced Pipeline Test:
```bash
# Test real AI generation
curl -X POST "http://localhost:3000/api/replicate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A cute Golden Retriever planter"}'

# Poll for results  
curl "http://localhost:3000/api/replicate?id=PREDICTION_ID"
```

### 2. Verify Assets:
- Check `conceptImage` URL is accessible
- Verify `modelUrl` points to real or demo GLB
- Confirm `pipeline` field indicates the correct mode

## Next Steps

1. **Update upload component** to display `conceptImage`
2. **Enhance progress indicators** for different pipeline phases
3. **Modify 3D viewer** to handle real GLB files
4. **Update checkout flow** with real asset URLs
5. **Add analytics** to track pipeline performance

## Backwards Compatibility

The enhanced API is fully backwards compatible:
- Existing frontend will work without changes
- New fields are optional and additive
- Demo mode continues to work as before
- Performance is improved with S3/CDN delivery
