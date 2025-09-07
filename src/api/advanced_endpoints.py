#!/usr/bin/env python3
"""
PetPlantr Advanced API Endpoints
Additional API endpoints for analytics, user management, gallery, notifications, and batch processing
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.services.analytics_service import get_analytics_service, track_generation_started, track_generation_completed, track_generation_failed
from src.services.user_management_service import get_user_management_service, UserProfile, UserRole
from src.services.gallery_service import get_gallery_service, ModelMetadata, ModelVisibility
from src.services.notification_service import get_notification_service, Notification, NotificationType, NotificationPriority
from src.services.batch_service import get_batch_service, BatchRequest, BatchJob

logger = logging.getLogger(__name__)

# Create router
advanced_router = APIRouter(prefix="/api/v2", tags=["advanced"])

# Service instances
analytics = get_analytics_service()
user_service = get_user_management_service()
gallery = get_gallery_service()
notifications = get_notification_service()
batch_service = get_batch_service()

# ===== ANALYTICS ENDPOINTS =====

@advanced_router.get("/analytics/realtime", summary="Get real-time analytics")
async def get_realtime_analytics():
    """Get real-time system analytics and metrics"""
    try:
        metrics = analytics.get_realtime_metrics()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

@advanced_router.get("/analytics/user/{user_id}", summary="Get user insights")
async def get_user_insights(user_id: str):
    """Get analytics insights for a specific user"""
    try:
        insights = analytics.get_user_insights(user_id)
        return JSONResponse(content=insights)
    except Exception as e:
        logger.error(f"Error getting user insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user insights")

@advanced_router.get("/analytics/health", summary="Get system health")
async def get_system_health():
    """Get system health metrics and status"""
    try:
        health = analytics.get_system_health()
        return JSONResponse(content=health)
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")

@advanced_router.get("/analytics/performance", summary="Get performance insights")
async def get_performance_insights():
    """Get performance insights and recommendations"""
    try:
        insights = analytics.get_performance_insights()
        return JSONResponse(content=insights)
    except Exception as e:
        logger.error(f"Error getting performance insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance insights")

# ===== USER MANAGEMENT ENDPOINTS =====

@advanced_router.post("/users", summary="Create user account")
async def create_user(email: str, username: str, password: Optional[str] = None):
    """Create a new user account"""
    try:
        user = user_service.create_user(email, username, password)
        return JSONResponse(content={
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "created_at": user.created_at
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@advanced_router.get("/users/{user_id}", summary="Get user profile")
async def get_user_profile(user_id: str):
    """Get user profile information"""
    try:
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse(content={
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "subscription_status": user.subscription_status.value,
            "preferences": user.preferences,
            "usage_stats": user.get_usage_summary(),
            "created_at": user.created_at,
            "last_login": user.last_login,
            "is_active": user.is_active
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")

@advanced_router.put("/users/{user_id}", summary="Update user profile")
async def update_user_profile(user_id: str, updates: Dict[str, Any]):
    """Update user profile information"""
    try:
        success = user_service.update_user_profile(user_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse(content={"message": "Profile updated successfully"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@advanced_router.get("/users/{user_id}/usage", summary="Get user usage stats")
async def get_user_usage_stats(user_id: str):
    """Get detailed usage statistics for a user"""
    try:
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return JSONResponse(content=user.get_usage_summary())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve usage stats")

@advanced_router.get("/users/leaderboard", summary="Get usage leaderboard")
async def get_usage_leaderboard(limit: int = 10):
    """Get usage leaderboard"""
    try:
        leaderboard = user_service.get_usage_leaderboard(limit)
        return JSONResponse(content=leaderboard)
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve leaderboard")

# ===== GALLERY ENDPOINTS =====

@advanced_router.post("/gallery/models", summary="Add model to gallery")
async def add_model_to_gallery(
    user_id: str,
    title: str,
    description: str,
    breed: str,
    file_path: str,
    quality: str = "high",
    size: str = "medium",
    tags: Optional[List[str]] = None
):
    """Add a new model to the gallery"""
    try:
        model = gallery.add_model(
            user_id=user_id,
            title=title,
            description=description,
            breed=breed,
            file_path=file_path,
            quality=quality,
            size=size,
            tags=tags
        )

        return JSONResponse(content={
            "model_id": model.model_id,
            "title": model.title,
            "breed": model.breed,
            "created_at": model.created_at,
            "visibility": model.visibility.value
        })
    except Exception as e:
        logger.error(f"Error adding model to gallery: {e}")
        raise HTTPException(status_code=500, detail="Failed to add model to gallery")

@advanced_router.get("/gallery/models", summary="Get public models")
async def get_public_models(
    limit: int = 20,
    offset: int = 0,
    breed_filter: Optional[str] = None,
    tag_filter: Optional[str] = None
):
    """Get public models with optional filtering"""
    try:
        models = gallery.get_public_models(
            limit=limit,
            offset=offset,
            breed_filter=breed_filter,
            tag_filter=tag_filter
        )

        return JSONResponse(content=[
            {
                "model_id": model.model_id,
                "title": model.title,
                "description": model.description,
                "breed": model.breed,
                "tags": model.tags,
                "quality": model.quality,
                "size": model.size,
                "download_count": model.download_count,
                "like_count": model.like_count,
                "view_count": model.view_count,
                "created_at": model.created_at,
                "user_id": model.user_id
            }
            for model in models
        ])
    except Exception as e:
        logger.error(f"Error getting public models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve models")

@advanced_router.get("/gallery/models/{model_id}", summary="Get model details")
async def get_model_details(model_id: str):
    """Get detailed information about a specific model"""
    try:
        model = gallery.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return JSONResponse(content={
            "model_id": model.model_id,
            "title": model.title,
            "description": model.description,
            "breed": model.breed,
            "tags": model.tags,
            "quality": model.quality,
            "size": model.size,
            "download_count": model.download_count,
            "like_count": model.like_count,
            "view_count": model.view_count,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "user_id": model.user_id,
            "visibility": model.visibility.value,
            "file_size": model.file_size,
            "processing_time": model.processing_time
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model details")

@advanced_router.get("/gallery/search", summary="Search models")
async def search_models(query: str, limit: int = 20):
    """Search models by title, description, breed, or tags"""
    try:
        models = gallery.search_models(query, limit=limit)

        return JSONResponse(content=[
            {
                "model_id": model.model_id,
                "title": model.title,
                "description": model.description,
                "breed": model.breed,
                "tags": model.tags,
                "download_count": model.download_count,
                "like_count": model.like_count,
                "created_at": model.created_at
            }
            for model in models
        ])
    except Exception as e:
        logger.error(f"Error searching models: {e}")
        raise HTTPException(status_code=500, detail="Failed to search models")

@advanced_router.get("/gallery/popular", summary="Get popular models")
async def get_popular_models(limit: int = 10):
    """Get most popular models by download count"""
    try:
        models = gallery.get_popular_models(limit)

        return JSONResponse(content=[
            {
                "model_id": model.model_id,
                "title": model.title,
                "breed": model.breed,
                "download_count": model.download_count,
                "like_count": model.like_count,
                "view_count": model.view_count
            }
            for model in models
        ])
    except Exception as e:
        logger.error(f"Error getting popular models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve popular models")

@advanced_router.post("/gallery/models/{model_id}/like", summary="Like a model")
async def like_model(model_id: str, user_id: str):
    """Like a model"""
    try:
        success = gallery.like_model(model_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")

        return JSONResponse(content={"message": "Model liked successfully"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error liking model: {e}")
        raise HTTPException(status_code=500, detail="Failed to like model")

# ===== NOTIFICATION ENDPOINTS =====

@advanced_router.get("/notifications/{user_id}", summary="Get user notifications")
async def get_user_notifications(
    user_id: str,
    include_read: bool = False,
    limit: int = 20
):
    """Get notifications for a user"""
    try:
        notifications_list = notifications.get_user_notifications(
            user_id,
            include_read=include_read,
            limit=limit
        )

        return JSONResponse(content=[
            {
                "notification_id": notif.notification_id,
                "type": notif.type.value,
                "title": notif.title,
                "message": notif.message,
                "priority": notif.priority.value,
                "created_at": notif.created_at,
                "read_at": notif.read_at,
                "is_read": notif.is_read(),
                "action_url": notif.action_url
            }
            for notif in notifications_list
        ])
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve notifications")

@advanced_router.get("/notifications/{user_id}/unread/count", summary="Get unread count")
async def get_unread_notification_count(user_id: str):
    """Get count of unread notifications for a user"""
    try:
        count = notifications.get_unread_count(user_id)
        return JSONResponse(content={"unread_count": count})
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")

@advanced_router.put("/notifications/{notification_id}/read", summary="Mark notification as read")
async def mark_notification_as_read(notification_id: str, user_id: str):
    """Mark a notification as read"""
    try:
        success = notifications.mark_as_read(notification_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return JSONResponse(content={"message": "Notification marked as read"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@advanced_router.put("/notifications/{user_id}/read-all", summary="Mark all notifications as read")
async def mark_all_notifications_as_read(user_id: str):
    """Mark all notifications as read for a user"""
    try:
        count = notifications.mark_all_as_read(user_id)
        return JSONResponse(content={
            "message": f"Marked {count} notifications as read"
        })
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")

@advanced_router.put("/notifications/preferences/{user_id}", summary="Update notification preferences")
async def update_notification_preferences(user_id: str, preferences: Dict[str, bool]):
    """Update notification preferences for a user"""
    try:
        notifications.update_user_preferences(user_id, preferences)
        return JSONResponse(content={"message": "Notification preferences updated"})
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

# ===== BATCH PROCESSING ENDPOINTS =====

@advanced_router.post("/batch", summary="Create batch request")
async def create_batch(
    user_id: str,
    title: str,
    description: str = "",
    priority: int = 1,
    max_concurrent_jobs: int = 3
):
    """Create a new batch processing request"""
    try:
        batch = batch_service.create_batch(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            max_concurrent_jobs=max_concurrent_jobs
        )

        return JSONResponse(content={
            "batch_id": batch.batch_id,
            "title": batch.title,
            "status": batch.status.value,
            "created_at": batch.created_at,
            "total_jobs": batch.total_jobs
        })
    except Exception as e:
        logger.error(f"Error creating batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to create batch")

@advanced_router.post("/batch/{batch_id}/jobs", summary="Add job to batch")
async def add_job_to_batch(
    batch_id: str,
    breed: str,
    quality: str = "high",
    size: str = "medium",
    custom_params: Optional[Dict[str, Any]] = None
):
    """Add a job to an existing batch"""
    try:
        job = batch_service.add_job_to_batch(
            batch_id=batch_id,
            breed=breed,
            quality=quality,
            size=size,
            custom_params=custom_params
        )

        if not job:
            raise HTTPException(status_code=404, detail="Batch not found or not accepting jobs")

        return JSONResponse(content={
            "job_id": job.job_id,
            "batch_id": job.batch_id,
            "breed": job.breed,
            "quality": job.quality,
            "size": job.size,
            "status": job.status.value
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding job to batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to add job to batch")

@advanced_router.post("/batch/{batch_id}/start", summary="Start batch processing")
async def start_batch_processing(batch_id: str):
    """Start processing a batch"""
    try:
        success = batch_service.start_batch_processing(batch_id)
        if not success:
            raise HTTPException(status_code=404, detail="Batch not found or cannot be started")

        return JSONResponse(content={"message": "Batch processing started"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting batch processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start batch processing")

@advanced_router.get("/batch/{batch_id}", summary="Get batch status")
async def get_batch_status(batch_id: str):
    """Get detailed status of a batch"""
    try:
        status = batch_service.get_batch_status(batch_id)
        if not status:
            raise HTTPException(status_code=404, detail="Batch not found")

        return JSONResponse(content=status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get batch status")

@advanced_router.get("/batch/{batch_id}/jobs/{job_id}", summary="Get job status")
async def get_job_status(batch_id: str, job_id: str):
    """Get detailed status of a job"""
    try:
        status = batch_service.get_job_status(batch_id, job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")

        return JSONResponse(content=status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job status")

@advanced_router.get("/batch/user/{user_id}", summary="Get user batches")
async def get_user_batches(user_id: str, limit: int = 20):
    """Get all batches for a user"""
    try:
        batches = batch_service.get_user_batches(user_id, limit=limit)

        return JSONResponse(content=[
            {
                "batch_id": batch.batch_id,
                "title": batch.title,
                "description": batch.description,
                "status": batch.status.value,
                "progress_percentage": batch.get_progress_percentage(),
                "total_jobs": batch.total_jobs,
                "completed_jobs": batch.completed_jobs,
                "failed_jobs": batch.failed_jobs,
                "created_at": batch.created_at,
                "started_at": batch.started_at,
                "completed_at": batch.completed_at
            }
            for batch in batches
        ])
    except Exception as e:
        logger.error(f"Error getting user batches: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user batches")

@advanced_router.delete("/batch/{batch_id}", summary="Cancel batch")
async def cancel_batch(batch_id: str, user_id: str):
    """Cancel a batch processing request"""
    try:
        success = batch_service.cancel_batch(batch_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Batch not found or cannot be cancelled")

        return JSONResponse(content={"message": "Batch cancelled successfully"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel batch")

# ===== SYSTEM ENDPOINTS =====

@advanced_router.get("/system/stats", summary="Get system statistics")
async def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        analytics_stats = analytics.get_realtime_metrics()
        user_stats = user_service.get_system_stats()
        gallery_stats = gallery.get_gallery_stats()
        notification_stats = notifications.get_notification_stats()
        batch_stats = batch_service.get_system_stats()

        return JSONResponse(content={
            "analytics": analytics_stats,
            "users": user_stats,
            "gallery": gallery_stats,
            "notifications": notification_stats,
            "batch_processing": batch_stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")

# Export the router
__all__ = ["advanced_router"]
