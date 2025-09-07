# PetPlantr API v2 Documentation

## Overview
Enhanced API endpoints with advanced features, analytics, and batch processing.

## New Endpoints

### POST /api/v2/predict/batch
Batch prediction for multiple images.

**Request:**
```json
{
  "images": ["base64_encoded_image_1", "base64_encoded_image_2"],
  "options": {"model": "clip-dpt"}
}
```

**Response:**
```json
{
  "results": [
    {
      "breed": "Golden Retriever",
      "confidence": 0.89,
      "processing_time": 0.45,
      "timestamp": "2025-09-06T10:30:00Z"
    }
  ],
  "total_processed": 2,
  "average_confidence": 0.89,
  "processing_time": 0.9
}
```

### GET /api/v2/analytics
Get analytics data for specified time range.

**Parameters:**
- `days` (int): Number of days to analyze (default: 7)

**Response:**
```json
{
  "total_predictions": 150,
  "average_confidence": 0.87,
  "top_breeds": [
    {"breed": "Golden Retriever", "count": 25, "percentage": 16.7}
  ],
  "performance_metrics": {
    "avg_processing_time": 0.45,
    "predictions_per_day": 21.4
  },
  "time_range": "7 days"
}
```

### GET /api/v2/health/detailed
Detailed health check with system metrics.

**Response:**
```json
{
  "status": "healthy",
  "uptime": 3600.5,
  "memory_usage": 45.2,
  "cpu_usage": 12.3,
  "active_connections": 0,
  "last_prediction": "2025-09-06T10:30:00Z"
}
```

### POST /api/v2/feedback
Submit user feedback for model improvement.

### GET /api/v2/models/info
Get information about loaded ML models.

## Features
- ✅ Batch processing
- ✅ Real-time analytics
- ✅ Enhanced health monitoring
- ✅ User feedback collection
- ✅ Automatic data cleanup
- ✅ Performance metrics
