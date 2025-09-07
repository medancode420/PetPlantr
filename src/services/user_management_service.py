#!/usr/bin/env python3
"""
PetPlantr User Management Service
Handles user profiles, preferences, and account management
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class UserRole(Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class UserProfile:
    """User profile data structure"""
    user_id: str
    email: str
    username: str
    role: UserRole = UserRole.FREE
    subscription_status: SubscriptionStatus = SubscriptionStatus.INACTIVE
    created_at: str = ""
    last_login: str = ""
    preferences: Dict[str, Any] = field(default_factory=lambda: {
        'default_quality': 'high',
        'default_size': 'medium',
        'notifications_enabled': True,
        'auto_save': True,
        'theme': 'light'
    })
    usage_stats: Dict[str, Any] = field(default_factory=lambda: {
        'total_generations': 0,
        'successful_generations': 0,
        'failed_generations': 0,
        'total_processing_time': 0.0,
        'favorite_breeds': [],
        'last_generation': None
    })
    api_key: str = ""
    is_active: bool = True
    profile_image: Optional[str] = None

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()
        if self.api_key == "":
            self.api_key = self._generate_api_key()

    def _generate_api_key(self) -> str:
        """Generate a unique API key for the user"""
        return f"pk_{uuid.uuid4().hex}_{hashlib.md5(self.user_id.encode()).hexdigest()[:8]}"

    def update_usage_stats(self, generation_result: bool, processing_time: float = 0.0, breed: Optional[str] = None):
        """Update usage statistics after a generation"""
        self.usage_stats['total_generations'] += 1
        if generation_result:
            self.usage_stats['successful_generations'] += 1
        else:
            self.usage_stats['failed_generations'] += 1

        self.usage_stats['total_processing_time'] += processing_time
        self.usage_stats['last_generation'] = datetime.now().isoformat()

        if breed and breed not in self.usage_stats['favorite_breeds']:
            self.usage_stats['favorite_breeds'].append(breed)

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of user usage"""
        total = self.usage_stats['total_generations']
        successful = self.usage_stats['successful_generations']
        return {
            'total_generations': total,
            'success_rate': f"{(successful / total * 100) if total > 0 else 0:.1f}%",
            'average_processing_time': f"{(self.usage_stats['total_processing_time'] / successful) if successful > 0 else 0:.2f}s",
            'favorite_breeds': self.usage_stats['favorite_breeds'][:5],  # Top 5
            'last_generation': self.usage_stats['last_generation']
        }

class UserManagementService:
    """User management service for PetPlantr"""

    def __init__(self):
        self.users_file = "users_data.json"
        self.users: Dict[str, UserProfile] = {}
        self.load_users()

    def load_users(self):
        """Load users from persistent storage"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        # Convert string role/status back to enum
                        user_data['role'] = UserRole(user_data['role'])
                        user_data['subscription_status'] = SubscriptionStatus(user_data['subscription_status'])
                        self.users[user_id] = UserProfile(**user_data)
                logger.info(f"✅ Loaded {len(self.users)} users from persistent storage")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load users data: {e}")

    def save_users(self):
        """Save users to persistent storage"""
        try:
            data = {}
            for user_id, user in self.users.items():
                user_dict = asdict(user)
                # Convert enums to strings for JSON serialization
                user_dict['role'] = user.role.value
                user_dict['subscription_status'] = user.subscription_status.value
                data[user_id] = user_dict

            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("💾 Users data saved to persistent storage")
        except Exception as e:
            logger.error(f"❌ Failed to save users data: {e}")

    def create_user(self, email: str, username: str, password: Optional[str] = None) -> UserProfile:
        """Create a new user account"""
        user_id = str(uuid.uuid4())

        # Check if email or username already exists
        for user in self.users.values():
            if user.email == email:
                raise ValueError("Email already registered")
            if user.username == username:
                raise ValueError("Username already taken")

        user = UserProfile(
            user_id=user_id,
            email=email,
            username=username
        )

        self.users[user_id] = user
        self.save_users()

        logger.info(f"👤 Created new user: {username} ({email})")
        return user

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID"""
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def get_user_by_username(self, username: str) -> Optional[UserProfile]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def get_user_by_api_key(self, api_key: str) -> Optional[UserProfile]:
        """Get user by API key"""
        for user in self.users.values():
            if user.api_key == api_key:
                return user
        return None

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile information"""
        user = self.get_user(user_id)
        if not user:
            return False

        # Update allowed fields
        allowed_fields = ['username', 'preferences', 'profile_image']
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(user, field, value)

        self.save_users()
        logger.info(f"📝 Updated profile for user: {user.username}")
        return True

    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update user role (admin function)"""
        user = self.get_user(user_id)
        if not user:
            return False

        user.role = new_role
        self.save_users()
        logger.info(f"🔄 Updated role for user {user.username} to {new_role.value}")
        return True

    def update_subscription_status(self, user_id: str, status: SubscriptionStatus) -> bool:
        """Update user subscription status"""
        user = self.get_user(user_id)
        if not user:
            return False

        user.subscription_status = status
        self.save_users()
        logger.info(f"💳 Updated subscription for user {user.username} to {status.value}")
        return True

    def record_login(self, user_id: str):
        """Record user login"""
        user = self.get_user(user_id)
        if user:
            user.last_login = datetime.now().isoformat()
            self.save_users()

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        user = self.get_user(user_id)
        if not user:
            return False

        user.is_active = False
        self.save_users()
        logger.info(f"🚫 Deactivated user account: {user.username}")
        return True

    def get_all_users(self, active_only: bool = True) -> List[UserProfile]:
        """Get all users (admin function)"""
        users = list(self.users.values())
        if active_only:
            users = [u for u in users if u.is_active]
        return users

    def get_users_by_role(self, role: UserRole) -> List[UserProfile]:
        """Get users by role"""
        return [u for u in self.users.values() if u.role == role and u.is_active]

    def get_usage_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get usage leaderboard"""
        users_stats = []
        for user in self.users.values():
            if user.is_active:
                stats = user.get_usage_summary()
                users_stats.append({
                    'username': user.username,
                    'total_generations': stats['total_generations'],
                    'success_rate': stats['success_rate'],
                    'role': user.role.value
                })

        # Sort by total generations descending
        users_stats.sort(key=lambda x: x['total_generations'], reverse=True)
        return users_stats[:limit]

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide user statistics"""
        total_users = len([u for u in self.users.values() if u.is_active])
        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = len(self.get_users_by_role(role))

        subscription_counts = {}
        for status in SubscriptionStatus:
            subscription_counts[status.value] = len([
                u for u in self.users.values()
                if u.subscription_status == status and u.is_active
            ])

        return {
            'total_users': total_users,
            'role_distribution': role_counts,
            'subscription_distribution': subscription_counts,
            'active_users_24h': len([
                u for u in self.users.values()
                if u.is_active and u.last_login and
                (datetime.now() - datetime.fromisoformat(u.last_login)).days < 1
            ])
        }

# Global user management instance
user_service = UserManagementService()

def get_user_management_service():
    """Get the global user management service instance"""
    return user_service

# Convenience functions for easy integration
def create_user_account(email: str, username: str) -> UserProfile:
    """Create a new user account"""
    return user_service.create_user(email, username)

def get_user_profile(user_id: str) -> Optional[UserProfile]:
    """Get user profile by ID"""
    return user_service.get_user(user_id)

def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> bool:
    """Update user preferences"""
    return user_service.update_user_profile(user_id, {'preferences': preferences})

def record_generation_usage(user_id: str, success: bool, processing_time: float = 0.0, breed: Optional[str] = None):
    """Record generation usage for analytics"""
    user = user_service.get_user(user_id)
    if user:
        user.update_usage_stats(success, processing_time, breed)
        user_service.save_users()

if __name__ == "__main__":
    # Example usage
    print("🚀 PetPlantr User Management Service")
    print("Testing user management functionality...")

    # Create test users
    try:
        user1 = create_user_account("john@example.com", "john_doe")
        user2 = create_user_account("jane@example.com", "jane_smith")

        print(f"👤 Created users: {user1.username}, {user2.username}")

        # Update preferences
        update_user_preferences(user1.user_id, {'theme': 'dark', 'default_quality': 'ultra'})

        # Record some usage
        record_generation_usage(user1.user_id, True, 12.5, "Golden Retriever")
        record_generation_usage(user1.user_id, True, 15.2, "Labrador")
        record_generation_usage(user2.user_id, True, 10.8, "Golden Retriever")

        # Get user profile
        profile = get_user_profile(user1.user_id)
        if profile:
            print(f"📊 {profile.username} usage: {profile.get_usage_summary()}")

        # Get system stats
        stats = user_service.get_system_stats()
        print(f"📈 System stats: {stats}")

        print("✅ User management service test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
