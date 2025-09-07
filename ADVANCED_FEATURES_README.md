# PetPlantr Advanced Features

## 🚀 Overview

PetPlantr has been enhanced with comprehensive advanced features including analytics, user management, model gallery, notifications, and batch processing. This document provides a complete guide to all the new capabilities.

## 📊 Analytics Service

Track and analyze platform usage, performance metrics, and user behavior.

### Features
- **Real-time Metrics**: Total generations, success rates, processing times
- **User Insights**: Individual user analytics and usage patterns
- **System Health**: Overall platform health and performance monitoring
- **Popular Breeds**: Track trending dog breeds
- **Performance Insights**: Bottleneck identification and optimization recommendations

### API Endpoints
```
GET /api/v2/analytics/realtime          # Get real-time metrics
GET /api/v2/analytics/user/{user_id}    # Get user insights
GET /api/v2/analytics/health           # Get system health
GET /api/v2/analytics/performance      # Get performance insights
```

### Usage Example
```python
from src.services.analytics_service import track_generation_started, track_generation_completed

# Track generation events
track_generation_started("user_123", "Golden Retriever", "high", "medium")
track_generation_completed("user_123", 15.5, "Golden Retriever", "high", "medium")
```

## 👥 User Management Service

Complete user account management with profiles, preferences, and usage tracking.

### Features
- **User Profiles**: Complete user information and preferences
- **Usage Statistics**: Detailed generation history and analytics
- **Role Management**: Support for different user tiers (Free, Premium, Enterprise)
- **Subscription Tracking**: Monitor user subscription status
- **Leaderboard**: Top users by generation activity

### API Endpoints
```
POST /api/v2/users                     # Create user account
GET  /api/v2/users/{user_id}           # Get user profile
PUT  /api/v2/users/{user_id}           # Update user profile
GET  /api/v2/users/{user_id}/usage     # Get user usage stats
GET  /api/v2/users/leaderboard         # Get usage leaderboard
```

### Usage Example
```python
from src.services.user_management_service import create_user_account, get_user_profile

# Create user
user = create_user_account("user@example.com", "username")

# Get profile
profile = get_user_profile(user.user_id)
print(f"User: {profile.username}, Generations: {profile.get_usage_summary()['total_generations']}")
```

## 🖼️ Gallery Service

Community-driven model sharing and showcase platform.

### Features
- **Model Upload**: Share your generated models with the community
- **Public Gallery**: Browse and discover models from other users
- **Search & Filter**: Find models by breed, tags, or creator
- **Like & Comment**: Interact with community models
- **Download Tracking**: Monitor model popularity
- **Quality Ratings**: Models categorized by quality level

### API Endpoints
```
POST /api/v2/gallery/models            # Add model to gallery
GET  /api/v2/gallery/models            # Get public models
GET  /api/v2/gallery/models/{model_id} # Get model details
GET  /api/v2/gallery/search            # Search models
GET  /api/v2/gallery/popular           # Get popular models
POST /api/v2/gallery/models/{model_id}/like # Like a model
```

### Usage Example
```python
from src.services.gallery_service import add_model_to_gallery, search_gallery

# Add model to gallery
model = add_model_to_gallery(
    user_id="user_123",
    title="Golden Retriever Planter",
    description="Beautiful custom planter",
    breed="Golden Retriever",
    file_path="/path/to/model.stl",
    tags=["golden", "retriever", "custom"]
)

# Search gallery
results = search_gallery("golden", limit=10)
```

## 📬 Notification Service

Real-time notifications and user communication system.

### Features
- **Multiple Notification Types**: Generation complete, failed, model interactions, system updates
- **Priority Levels**: Low, Medium, High, Urgent
- **User Preferences**: Customizable notification settings
- **Expiration Management**: Automatic cleanup of old notifications
- **Action URLs**: Direct links to relevant content
- **Unread Tracking**: Monitor notification status

### API Endpoints
```
GET  /api/v2/notifications/{user_id}                    # Get user notifications
GET  /api/v2/notifications/{user_id}/unread/count       # Get unread count
PUT  /api/v2/notifications/{notification_id}/read       # Mark as read
PUT  /api/v2/notifications/{user_id}/read-all           # Mark all as read
PUT  /api/v2/notifications/preferences/{user_id}        # Update preferences
```

### Usage Example
```python
from src.services.notification_service import send_generation_complete_notification

# Send notification
send_generation_complete_notification(
    user_id="user_123",
    model_title="Golden Retriever Planter",
    download_url="/download/model_123"
)
```

## 📦 Batch Processing Service

Efficient batch processing for multiple model generations.

### Features
- **Batch Creation**: Group multiple generations into a single batch
- **Parallel Processing**: Concurrent processing with configurable limits
- **Progress Tracking**: Real-time progress monitoring
- **Queue Management**: Automatic job queuing and prioritization
- **Error Handling**: Individual job failure handling
- **Resource Management**: Configurable concurrent job limits

### API Endpoints
```
POST /api/v2/batch                      # Create batch
POST /api/v2/batch/{batch_id}/jobs      # Add job to batch
POST /api/v2/batch/{batch_id}/start     # Start batch processing
GET  /api/v2/batch/{batch_id}           # Get batch status
GET  /api/v2/batch/{batch_id}/jobs/{job_id} # Get job status
GET  /api/v2/batch/user/{user_id}       # Get user batches
DELETE /api/v2/batch/{batch_id}         # Cancel batch
```

### Usage Example
```python
from src.services.batch_service import create_batch_request, start_batch_processing

# Create batch with multiple jobs
batch = create_batch_request(
    user_id="user_123",
    title="Breed Collection",
    jobs_data=[
        {"breed": "Golden Retriever", "quality": "high", "size": "large"},
        {"breed": "Labrador", "quality": "high", "size": "medium"},
        {"breed": "Poodle", "quality": "ultra", "size": "small"}
    ]
)

# Start processing
start_batch_processing(batch.batch_id)
```

## 🔗 Service Integration

All services work together seamlessly for a complete platform experience.

### Complete Workflow Example
```python
# 1. User creates account
user = create_user_account("user@example.com", "username")

# 2. Track generation start
track_generation_started(user.user_id, "Golden Retriever", "high", "medium")

# 3. Generation completes
track_generation_completed(user.user_id, 15.5, "Golden Retriever", "high", "medium")

# 4. Record usage
record_generation_usage(user.user_id, True, 15.5, "Golden Retriever")

# 5. Add to gallery
model = add_model_to_gallery(
    user.user_id, "My Planter", "Custom design",
    "Golden Retriever", "/path/to/model.stl"
)

# 6. Send notification
send_generation_complete_notification(user.user_id, model.title, f"/download/{model.model_id}")

# 7. Get user insights
insights = get_user_insights(user.user_id)
```

## 📈 System Statistics

Comprehensive system monitoring and analytics.

### API Endpoint
```
GET /api/v2/system/stats    # Get comprehensive system statistics
```

### Response Format
```json
{
  "analytics": {
    "total_generations": 150,
    "successful_generations": 142,
    "average_processing_time": 18.5
  },
  "users": {
    "total_users": 45,
    "active_users_24h": 12,
    "role_distribution": {"free": 30, "premium": 12, "enterprise": 3}
  },
  "gallery": {
    "total_models": 89,
    "public_models": 67,
    "total_downloads": 1250
  },
  "notifications": {
    "total_notifications": 234,
    "unread_notifications": 45,
    "active_users_with_notifications": 23
  },
  "batch_processing": {
    "total_batches": 12,
    "active_batches": 3,
    "success_rate": 94.2
  }
}
```

## 🛠️ Configuration

### Environment Variables
```bash
# Analytics
ANALYTICS_DATA_FILE=analytics_data.json

# User Management
USERS_DATA_FILE=users_data.json

# Gallery
GALLERY_MODELS_FILE=gallery_models.json
GALLERY_COMMENTS_FILE=gallery_comments.json

# Notifications
NOTIFICATIONS_DATA_FILE=notifications_data.json

# Batch Processing
BATCH_REQUESTS_FILE=batch_requests.json
MAX_CONCURRENT_JOBS=5
```

### Service Initialization
```python
# Initialize all services
analytics = get_analytics_service()
user_service = get_user_management_service()
gallery = get_gallery_service()
notifications = get_notification_service()
batch_service = get_batch_service()

# Start background tasks
batch_service.start_cleanup_task()
```

## 📚 API Documentation

Complete API documentation is available at:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

## 🧪 Testing

Run the comprehensive demo:
```bash
python3 demo_advanced_features.py
```

This will test all services and demonstrate their integration.

## 🔧 Development

### Project Structure
```
src/
├── services/
│   ├── analytics_service.py          # Analytics and metrics
│   ├── user_management_service.py    # User accounts and profiles
│   ├── gallery_service.py            # Model gallery and sharing
│   ├── notification_service.py       # Notifications and alerts
│   └── batch_service.py              # Batch processing
├── api/
│   └── advanced_endpoints.py         # API endpoints for all services
└── ...
```

### Adding New Features
1. Create a new service in `src/services/`
2. Add API endpoints in `src/api/advanced_endpoints.py`
3. Update the main `api_server.py` to include new routes
4. Add to the demo script for testing

## 📋 Requirements

- Python 3.11+
- FastAPI
- AsyncIO support
- JSON file storage (can be replaced with database)

## 🚀 Deployment

The advanced features are automatically included when running the main API server:

```bash
python3 api_server.py
```

All services will initialize automatically and be available through the `/api/v2/` endpoints.

## 🤝 Contributing

When adding new features:
1. Follow the existing service pattern
2. Include comprehensive error handling
3. Add API endpoints with proper documentation
4. Update this README with new features
5. Add tests to the demo script

## 📄 License

This project is part of PetPlantr and follows the same licensing terms.
