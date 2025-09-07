#!/usr/bin/env python3
"""
PetPlantr Advanced Features Demo
Demonstrates the new analytics, user management, gallery, notifications, and batch processing features
"""

import asyncio
import time
import json
from datetime import datetime

# Import our new services
from src.services.analytics_service import get_analytics_service, track_generation_started, track_generation_completed, track_generation_failed
from src.services.user_management_service import get_user_management_service
from src.services.gallery_service import get_gallery_service
from src.services.notification_service import get_notification_service, NotificationType, NotificationPriority
from src.services.batch_service import get_batch_service, create_batch_request

async def demo_analytics():
    """Demonstrate analytics service"""
    print("📊 ANALYTICS SERVICE DEMO")
    print("=" * 50)

    analytics = get_analytics_service()

    # Simulate some events
    print("🎯 Simulating user activity...")

    # Track generation events
    track_generation_started("user_123", "Golden Retriever", "high", "medium")
    await asyncio.sleep(0.1)
    track_generation_completed("user_123", 15.5, "Golden Retriever", "high", "medium")

    track_generation_started("user_456", "Labrador", "ultra", "large")
    await asyncio.sleep(0.1)
    track_generation_completed("user_456", 22.3, "Labrador", "ultra", "large")

    track_generation_started("user_789", "Poodle", "medium", "small")
    await asyncio.sleep(0.1)
    track_generation_failed("user_789", "Processing timeout", "Poodle")

    # Get real-time metrics
    metrics = analytics.get_realtime_metrics()
    print(f"📈 Total generations: {metrics['metrics']['total_generations']}")
    print(f"✅ Successful: {metrics['metrics']['successful_generations']}")
    print(f"❌ Failed: {metrics['metrics']['failed_generations']}")
    print(".2f")
    print(f"📊 Popular breeds: {dict(list(metrics['metrics']['popular_breeds'].items())[:3])}")

    # Get system health
    health = analytics.get_system_health()
    print(f"🏥 System health: {health['overall_health']}")
    print(f"📈 Success rate: {health['success_rate']}")

    print("✅ Analytics demo completed!\n")

async def demo_user_management():
    """Demonstrate user management service"""
    print("👥 USER MANAGEMENT SERVICE DEMO")
    print("=" * 50)

    user_service = get_user_management_service()

    # Create test users
    print("👤 Creating test users...")
    user1 = user_service.create_user("john@example.com", "john_doe")
    user2 = user_service.create_user("jane@example.com", "jane_smith")

    print(f"✅ Created users: {user1.username}, {user2.username}")

    # Update user preferences
    print("⚙️ Updating user preferences...")
    user_service.update_user_profile(user1.user_id, {
        'preferences': {'theme': 'dark', 'default_quality': 'ultra'}
    })

    # Record usage
    print("📊 Recording user activity...")
    from src.services.user_management_service import record_generation_usage
    record_generation_usage(user1.user_id, True, 15.5, "Golden Retriever")
    record_generation_usage(user1.user_id, True, 12.3, "Labrador")
    record_generation_usage(user2.user_id, True, 18.7, "Poodle")

    # Get user profile
    profile = user_service.get_user(user1.user_id)
    if profile:
        usage = profile.get_usage_summary()
        print(f"📈 {profile.username} stats: {usage}")

    # Get leaderboard
    leaderboard = user_service.get_usage_leaderboard(5)
    print("🏆 Usage Leaderboard:")
    for i, user in enumerate(leaderboard, 1):
        print(f"  {i}. {user['username']}: {user['total_generations']} generations")

    print("✅ User management demo completed!\n")

async def demo_gallery():
    """Demonstrate gallery service"""
    print("🖼️ GALLERY SERVICE DEMO")
    print("=" * 50)

    gallery = get_gallery_service()

    # Add models to gallery
    print("🖼️ Adding models to gallery...")
    model1 = gallery.add_model(
        "user_123", "Golden Retriever Planter", "Beautiful golden retriever planter",
        "Golden Retriever", "/tmp/model1.stl", quality="high", size="large",
        tags=["golden", "retriever", "planter"]
    )

    model2 = gallery.add_model(
        "user_456", "Labrador Planter", "Classic labrador planter design",
        "Labrador", "/tmp/model2.stl", quality="ultra", size="medium",
        tags=["labrador", "classic", "planter"]
    )

    print(f"✅ Added models: {model1.title}, {model2.title}")

    # Get public models
    public_models = gallery.get_public_models(limit=5)
    print(f"📚 Found {len(public_models)} public models")

    # Search models
    search_results = gallery.search_models("golden", limit=5)
    print(f"🔍 Search for 'golden': {len(search_results)} results")

    # Get popular models
    popular = gallery.get_popular_models(3)
    print("🔥 Popular models:")
    for model in popular:
        print(f"  • {model.title} ({model.download_count} downloads)")

    # Get gallery stats
    stats = gallery.get_gallery_stats()
    print(f"📊 Gallery stats: {stats['total_models']} models, {stats['total_downloads']} downloads")

    print("✅ Gallery demo completed!\n")

async def demo_notifications():
    """Demonstrate notification service"""
    print("📬 NOTIFICATION SERVICE DEMO")
    print("=" * 50)

    notifications = get_notification_service()

    # Create notifications
    print("📝 Creating notifications...")
    notif1 = notifications.create_notification(
        "user_123",
        NotificationType.GENERATION_COMPLETE,
        "Generation Complete!",
        "Your Golden Retriever planter is ready!",
        priority=NotificationPriority.HIGH,
        metadata={'model_id': 'model_123'},
        action_url='/download/model_123'
    )

    notif2 = notifications.create_notification(
        "user_123",
        NotificationType.NEW_FEATURE,
        "New Feature Available",
        "Try our new ultra quality generation!",
        priority=NotificationPriority.MEDIUM,
        expires_in_hours=168
    )

    print(f"✅ Created notifications: {notif1.title}, {notif2.title}")

    # Get user notifications
    user_notifications = notifications.get_user_notifications("user_123", limit=5)
    print(f"📚 User has {len(user_notifications)} notifications")

    unread_count = notifications.get_unread_count("user_123")
    print(f"📧 Unread notifications: {unread_count}")

    # Mark as read
    notifications.mark_as_read(notif1.notification_id, "user_123")
    print("✅ Marked notification as read")

    # Get notification stats
    stats = notifications.get_notification_stats()
    print(f"📊 Notification stats: {stats}")

    print("✅ Notification demo completed!\n")

async def demo_batch_processing():
    """Demonstrate batch processing service"""
    print("📦 BATCH PROCESSING SERVICE DEMO")
    print("=" * 50)

    batch_service = get_batch_service()
    batch_service.start_cleanup_task()  # Start the cleanup task now that we have an event loop

    # Create batch
    print("📦 Creating batch request...")
    batch = create_batch_request(
        "user_123",
        "Popular Breeds Collection",
        [
            {"breed": "Golden Retriever", "quality": "high", "size": "large"},
            {"breed": "Labrador", "quality": "high", "size": "medium"},
            {"breed": "German Shepherd", "quality": "ultra", "size": "large"},
            {"breed": "Poodle", "quality": "medium", "size": "small"},
            {"breed": "Bulldog", "quality": "high", "size": "medium"}
        ]
    )

    print(f"✅ Created batch {batch.batch_id} with {batch.total_jobs} jobs")

    # Start processing
    print("▶️ Starting batch processing...")
    success = batch_service.start_batch_processing(batch.batch_id)
    if success:
        print("✅ Batch processing started")

        # Monitor progress
        for i in range(6):
            await asyncio.sleep(1)
            status = batch_service.get_batch_status(batch.batch_id)
            if status:
                progress = status['progress_percentage']
                completed = status['completed_jobs']
                total = status['total_jobs']
                print(f"📊 Progress: {progress:.1f}% ({completed}/{total} jobs)")
                if status['status'] in ['completed', 'failed']:
                    break

        # Final status
        final_status = batch_service.get_batch_status(batch.batch_id)
        if final_status:
            print(f"🏁 Final status: {final_status['status']}")
            print(".1f")

    # Get system stats
    stats = batch_service.get_system_stats()
    print(f"📊 Batch system stats: {stats}")

    print("✅ Batch processing demo completed!\n")

async def demo_integration():
    """Demonstrate service integration"""
    print("🔗 SERVICE INTEGRATION DEMO")
    print("=" * 50)

    # Simulate a complete workflow
    print("🚀 Simulating complete PetPlantr workflow...")

    # 1. User creates account
    user_service = get_user_management_service()
    user = user_service.create_user("demo@example.com", "demo_user")
    print(f"👤 User {user.username} created")

    # 2. User starts generation
    analytics = get_analytics_service()
    track_generation_started(user.user_id, "Golden Retriever", "high", "medium")
    print("🎯 Generation started")

    # 3. Generation completes
    await asyncio.sleep(0.1)
    track_generation_completed(user.user_id, 15.5, "Golden Retriever", "high", "medium")
    print("✅ Generation completed")

    # 4. Record usage for user
    from src.services.user_management_service import record_generation_usage
    record_generation_usage(user.user_id, True, 15.5, "Golden Retriever")

    # 5. Add model to gallery
    gallery = get_gallery_service()
    model = gallery.add_model(
        user.user_id, "My Golden Retriever Planter", "Custom planter for my dog",
        "Golden Retriever", "/tmp/demo_model.stl", quality="high", size="medium"
    )
    print(f"🖼️ Model added to gallery: {model.title}")

    # 6. Send notification
    notifications = get_notification_service()
    notifications.notify_generation_complete(
        user.user_id, model.title, f"/download/{model.model_id}"
    )
    print("📬 Notification sent")

    # 7. Get user insights
    insights = analytics.get_user_insights(user.user_id)
    print(f"📊 User insights: {insights['total_generations']} generations")

    print("✅ Integration demo completed!\n")

async def main():
    """Run all demos"""
    print("🎉 PETPLANTR ADVANCED FEATURES DEMO")
    print("=" * 60)
    print("This demo showcases the new advanced features:")
    print("• 📊 Analytics Service")
    print("• 👥 User Management Service")
    print("• 🖼️ Gallery Service")
    print("• 📬 Notification Service")
    print("• 📦 Batch Processing Service")
    print("• 🔗 Service Integration")
    print("=" * 60)
    print()

    start_time = time.time()

    try:
        await demo_analytics()
        await demo_user_management()
        await demo_gallery()
        await demo_notifications()
        await demo_batch_processing()
        await demo_integration()

        total_time = time.time() - start_time
        print("🎊 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print(f"⏱️ Total time: {total_time:.1f} seconds")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run the demo
    asyncio.run(main())
