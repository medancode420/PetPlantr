#!/usr/bin/env python3
"""
PetPlantr Notification Service
Handles real-time notifications, alerts, and user communications
"""

import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    GENERATION_COMPLETE = "generation_complete"
    GENERATION_FAILED = "generation_failed"
    MODEL_LIKED = "model_liked"
    MODEL_COMMENTED = "model_commented"
    SYSTEM_MAINTENANCE = "system_maintenance"
    NEW_FEATURE = "new_feature"
    ACCOUNT_UPDATE = "account_update"
    SUBSCRIPTION_UPDATE = "subscription_update"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Notification:
    """Notification data structure"""
    notification_id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    created_at: str = ""
    read_at: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    action_url: Optional[str] = None

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()

    def mark_as_read(self):
        """Mark notification as read"""
        self.read_at = datetime.now().isoformat()

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if not self.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)

    def is_read(self) -> bool:
        """Check if notification has been read"""
        return self.read_at is not None

class NotificationService:
    """Notification service for PetPlantr"""

    def __init__(self):
        self.notifications_file = "notifications_data.json"
        self.notifications: Dict[str, Notification] = {}
        self.user_preferences: Dict[str, Dict[str, bool]] = {}
        self.load_data()

    def load_data(self):
        """Load notification data from persistent storage"""
        try:
            if os.path.exists(self.notifications_file):
                with open(self.notifications_file, 'r') as f:
                    data = json.load(f)
                    for notif_id, notif_data in data.items():
                        # Convert string enums back to enum
                        notif_data['type'] = NotificationType(notif_data['type'])
                        notif_data['priority'] = NotificationPriority(notif_data['priority'])
                        self.notifications[notif_id] = Notification(**notif_data)

            logger.info(f"✅ Loaded {len(self.notifications)} notifications")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load notification data: {e}")

    def save_data(self):
        """Save notification data to persistent storage"""
        try:
            notifications_data = {}
            for notif_id, notif in self.notifications.items():
                notif_dict = asdict(notif)
                # Convert enums to strings for JSON serialization
                notif_dict['type'] = notif.type.value
                notif_dict['priority'] = notif.priority.value
                notifications_data[notif_id] = notif_dict

            with open(self.notifications_file, 'w') as f:
                json.dump(notifications_data, f, indent=2)

            logger.info("💾 Notification data saved to persistent storage")
        except Exception as e:
            logger.error(f"❌ Failed to save notification data: {e}")

    def create_notification(self, user_id: str, type: NotificationType, title: str, message: str,
                           priority: NotificationPriority = NotificationPriority.MEDIUM,
                           metadata: Optional[Dict[str, Any]] = None,
                           action_url: Optional[str] = None,
                           expires_in_hours: Optional[int] = None) -> Notification:
        """Create a new notification"""
        notification_id = str(uuid.uuid4())

        expires_at = None
        if expires_in_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()

        notification = Notification(
            notification_id=notification_id,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            priority=priority,
            metadata=metadata or {},
            action_url=action_url,
            expires_at=expires_at
        )

        self.notifications[notification_id] = notification
        self.save_data()

        logger.info(f"📬 Created notification for user {user_id}: {title}")
        return notification

    def get_user_notifications(self, user_id: str, include_read: bool = True,
                              limit: int = 50) -> List[Notification]:
        """Get notifications for a user"""
        user_notifications = [
            notif for notif in self.notifications.values()
            if notif.user_id == user_id and not notif.is_expired()
        ]

        if not include_read:
            user_notifications = [n for n in user_notifications if not n.is_read()]

        # Sort by creation date (newest first)
        user_notifications.sort(key=lambda x: x.created_at, reverse=True)

        return user_notifications[:limit]

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        return len([
            notif for notif in self.notifications.values()
            if notif.user_id == user_id and not notif.is_read() and not notif.is_expired()
        ])

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        notification = self.notifications.get(notification_id)
        if not notification or notification.user_id != user_id:
            return False

        notification.mark_as_read()
        self.save_data()
        return True

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        count = 0
        for notification in self.notifications.values():
            if (notification.user_id == user_id and
                not notification.is_read() and
                not notification.is_expired()):
                notification.mark_as_read()
                count += 1

        if count > 0:
            self.save_data()
        return count

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        notification = self.notifications.get(notification_id)
        if not notification or notification.user_id != user_id:
            return False

        del self.notifications[notification_id]
        self.save_data()
        return True

    def cleanup_expired_notifications(self) -> int:
        """Remove expired notifications"""
        expired_ids = [
            notif_id for notif_id, notif in self.notifications.items()
            if notif.is_expired()
        ]

        for notif_id in expired_ids:
            del self.notifications[notif_id]

        if expired_ids:
            self.save_data()

        logger.info(f"🧹 Cleaned up {len(expired_ids)} expired notifications")
        return len(expired_ids)

    def update_user_preferences(self, user_id: str, preferences: Dict[str, bool]):
        """Update notification preferences for a user"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id].update(preferences)
        logger.info(f"⚙️ Updated notification preferences for user {user_id}")

    def get_user_preferences(self, user_id: str) -> Dict[str, bool]:
        """Get notification preferences for a user"""
        return self.user_preferences.get(user_id, {
            'generation_complete': True,
            'generation_failed': True,
            'model_liked': True,
            'model_commented': True,
            'system_maintenance': True,
            'new_feature': True,
            'account_update': True,
            'subscription_update': True
        })

    def should_send_notification(self, user_id: str, notification_type: NotificationType) -> bool:
        """Check if user wants to receive this type of notification"""
        preferences = self.get_user_preferences(user_id)
        return preferences.get(notification_type.value, True)

    # Convenience methods for common notifications
    def notify_generation_complete(self, user_id: str, model_title: str, download_url: str):
        """Notify user of completed generation"""
        if not self.should_send_notification(user_id, NotificationType.GENERATION_COMPLETE):
            return

        self.create_notification(
            user_id=user_id,
            type=NotificationType.GENERATION_COMPLETE,
            title="🎉 Generation Complete!",
            message=f"Your {model_title} planter has been generated successfully!",
            priority=NotificationPriority.HIGH,
            metadata={'model_title': model_title},
            action_url=download_url,
            expires_in_hours=168  # 7 days
        )

    def notify_generation_failed(self, user_id: str, model_title: str, error_message: str):
        """Notify user of failed generation"""
        if not self.should_send_notification(user_id, NotificationType.GENERATION_FAILED):
            return

        self.create_notification(
            user_id=user_id,
            type=NotificationType.GENERATION_FAILED,
            title="❌ Generation Failed",
            message=f"Sorry, we couldn't generate your {model_title} planter. {error_message}",
            priority=NotificationPriority.HIGH,
            metadata={'model_title': model_title, 'error': error_message},
            expires_in_hours=72
        )

    def notify_model_liked(self, user_id: str, liker_username: str, model_title: str, model_url: str):
        """Notify user when their model is liked"""
        if not self.should_send_notification(user_id, NotificationType.MODEL_LIKED):
            return

        self.create_notification(
            user_id=user_id,
            type=NotificationType.MODEL_LIKED,
            title="👍 Model Liked!",
            message=f"{liker_username} liked your {model_title} model!",
            priority=NotificationPriority.LOW,
            metadata={'liker_username': liker_username, 'model_title': model_title},
            action_url=model_url,
            expires_in_hours=24
        )

    def notify_model_commented(self, user_id: str, commenter_username: str, model_title: str,
                              comment: str, model_url: str):
        """Notify user when their model is commented on"""
        if not self.should_send_notification(user_id, NotificationType.MODEL_COMMENTED):
            return

        # Truncate comment if too long
        short_comment = comment[:100] + "..." if len(comment) > 100 else comment

        self.create_notification(
            user_id=user_id,
            type=NotificationType.MODEL_COMMENTED,
            title="💬 New Comment!",
            message=f"{commenter_username} commented on your {model_title}: \"{short_comment}\"",
            priority=NotificationPriority.MEDIUM,
            metadata={
                'commenter_username': commenter_username,
                'model_title': model_title,
                'comment': comment
            },
            action_url=model_url,
            expires_in_hours=48
        )

    def notify_system_maintenance(self, user_id: str, maintenance_time: str, duration: str):
        """Notify user of system maintenance"""
        if not self.should_send_notification(user_id, NotificationType.SYSTEM_MAINTENANCE):
            return

        self.create_notification(
            user_id=user_id,
            type=NotificationType.SYSTEM_MAINTENANCE,
            title="🔧 System Maintenance",
            message=f"Scheduled maintenance on {maintenance_time} for {duration}. Service may be temporarily unavailable.",
            priority=NotificationPriority.MEDIUM,
            metadata={'maintenance_time': maintenance_time, 'duration': duration},
            expires_in_hours=6
        )

    def notify_new_feature(self, user_id: str, feature_name: str, feature_description: str):
        """Notify user of new features"""
        if not self.should_send_notification(user_id, NotificationType.NEW_FEATURE):
            return

        self.create_notification(
            user_id=user_id,
            type=NotificationType.NEW_FEATURE,
            title="✨ New Feature Available!",
            message=f"Check out our new {feature_name}: {feature_description}",
            priority=NotificationPriority.LOW,
            metadata={'feature_name': feature_name, 'description': feature_description},
            expires_in_hours=168  # 7 days
        )

    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification system statistics"""
        total_notifications = len(self.notifications)
        unread_count = len([n for n in self.notifications.values() if not n.is_read()])
        expired_count = len([n for n in self.notifications.values() if n.is_expired()])

        type_counts = {}
        for notification in self.notifications.values():
            type_counts[notification.type.value] = type_counts.get(notification.type.value, 0) + 1

        return {
            'total_notifications': total_notifications,
            'unread_notifications': unread_count,
            'expired_notifications': expired_count,
            'type_distribution': type_counts,
            'active_users_with_notifications': len(set(
                n.user_id for n in self.notifications.values()
                if not n.is_expired()
            ))
        }

# Global notification instance
notification_service = NotificationService()

def get_notification_service():
    """Get the global notification service instance"""
    return notification_service

# Convenience functions for easy integration
def send_generation_complete_notification(user_id: str, model_title: str, download_url: str):
    """Send generation complete notification"""
    notification_service.notify_generation_complete(user_id, model_title, download_url)

def send_generation_failed_notification(user_id: str, model_title: str, error_message: str):
    """Send generation failed notification"""
    notification_service.notify_generation_failed(user_id, model_title, error_message)

def get_user_notifications(user_id: str, limit: int = 20) -> List[Notification]:
    """Get user notifications"""
    return notification_service.get_user_notifications(user_id, limit=limit)

def get_unread_notification_count(user_id: str) -> int:
    """Get unread notification count"""
    return notification_service.get_unread_count(user_id)

if __name__ == "__main__":
    # Example usage
    print("🚀 PetPlantr Notification Service")
    print("Testing notification functionality...")

    try:
        # Create some test notifications
        notif1 = notification_service.create_notification(
            "user_123",
            NotificationType.GENERATION_COMPLETE,
            "Generation Complete!",
            "Your Golden Retriever planter is ready!",
            priority=NotificationPriority.HIGH,
            metadata={'model_id': 'model_123'},
            action_url='/download/model_123'
        )

        notif2 = notification_service.create_notification(
            "user_123",
            NotificationType.NEW_FEATURE,
            "New Feature: Ultra Quality",
            "Try our new ultra-high quality generation!",
            priority=NotificationPriority.LOW,
            expires_in_hours=168
        )

        print(f"📬 Created notifications: {notif1.title}, {notif2.title}")

        # Get user notifications
        user_notifications = get_user_notifications("user_123", limit=10)
        print(f"📚 User has {len(user_notifications)} notifications")

        # Get unread count
        unread_count = get_unread_notification_count("user_123")
        print(f"📧 User has {unread_count} unread notifications")

        # Mark one as read
        notification_service.mark_as_read(notif1.notification_id, "user_123")
        print("✅ Marked notification as read")

        # Get stats
        stats = notification_service.get_notification_stats()
        print(f"📊 Notification stats: {stats}")

        print("✅ Notification service test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
