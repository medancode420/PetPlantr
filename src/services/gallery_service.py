#!/usr/bin/env python3
"""
PetPlantr Model Gallery Service
Handles model sharing, gallery management, and community features
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ModelVisibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"

class ModelStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

@dataclass
class ModelMetadata:
    """Model metadata structure"""
    model_id: str
    user_id: str
    title: str
    description: str
    breed: str
    tags: List[str] = field(default_factory=list)
    visibility: ModelVisibility = ModelVisibility.PRIVATE
    status: ModelStatus = ModelStatus.ACTIVE
    created_at: str = ""
    updated_at: str = ""
    file_path: str = ""
    thumbnail_path: str = ""
    file_size: int = 0
    download_count: int = 0
    like_count: int = 0
    view_count: int = 0
    quality: str = "high"
    size: str = "medium"
    processing_time: float = 0.0
    generation_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()
        if self.updated_at == "":
            self.updated_at = datetime.now().isoformat()

    def update_stats(self, action: str):
        """Update model statistics"""
        if action == "view":
            self.view_count += 1
        elif action == "download":
            self.download_count += 1
        elif action == "like":
            self.like_count += 1
        self.updated_at = datetime.now().isoformat()

@dataclass
class GalleryComment:
    """Gallery comment structure"""
    comment_id: str
    model_id: str
    user_id: str
    username: str
    content: str
    created_at: str = ""
    likes: int = 0

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()

class ModelGalleryService:
    """Model gallery service for PetPlantr"""

    def __init__(self):
        self.models_file = "gallery_models.json"
        self.comments_file = "gallery_comments.json"
        self.models: Dict[str, ModelMetadata] = {}
        self.comments: Dict[str, GalleryComment] = {}
        self.load_data()

    def load_data(self):
        """Load gallery data from persistent storage"""
        try:
            # Load models
            if os.path.exists(self.models_file):
                with open(self.models_file, 'r') as f:
                    data = json.load(f)
                    for model_id, model_data in data.items():
                        # Convert string enums back to enum
                        model_data['visibility'] = ModelVisibility(model_data['visibility'])
                        model_data['status'] = ModelStatus(model_data['status'])
                        self.models[model_id] = ModelMetadata(**model_data)

            # Load comments
            if os.path.exists(self.comments_file):
                with open(self.comments_file, 'r') as f:
                    data = json.load(f)
                    for comment_id, comment_data in data.items():
                        self.comments[comment_id] = GalleryComment(**comment_data)

            logger.info(f"✅ Loaded {len(self.models)} models and {len(self.comments)} comments from gallery")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load gallery data: {e}")

    def save_data(self):
        """Save gallery data to persistent storage"""
        try:
            # Save models
            models_data = {}
            for model_id, model in self.models.items():
                model_dict = asdict(model)
                # Convert enums to strings for JSON serialization
                model_dict['visibility'] = model.visibility.value
                model_dict['status'] = model.status.value
                models_data[model_id] = model_dict

            with open(self.models_file, 'w') as f:
                json.dump(models_data, f, indent=2)

            # Save comments
            comments_data = {cid: asdict(comment) for cid, comment in self.comments.items()}
            with open(self.comments_file, 'w') as f:
                json.dump(comments_data, f, indent=2)

            logger.info("💾 Gallery data saved to persistent storage")
        except Exception as e:
            logger.error(f"❌ Failed to save gallery data: {e}")

    def add_model(self, user_id: str, title: str, description: str, breed: str,
                  file_path: str, thumbnail_path: str = "", quality: str = "high",
                  size: str = "medium", tags: Optional[List[str]] = None,
                  generation_params: Optional[Dict[str, Any]] = None,
                  processing_time: float = 0.0) -> ModelMetadata:
        """Add a new model to the gallery"""
        model_id = str(uuid.uuid4())

        model = ModelMetadata(
            model_id=model_id,
            user_id=user_id,
            title=title,
            description=description,
            breed=breed,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            quality=quality,
            size=size,
            tags=tags or [],
            generation_params=generation_params or {},
            processing_time=processing_time,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
        )

        self.models[model_id] = model
        self.save_data()

        logger.info(f"🖼️ Added new model to gallery: {title} by user {user_id}")
        return model

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model by ID"""
        model = self.models.get(model_id)
        if model and model.status == ModelStatus.ACTIVE:
            model.update_stats("view")
            self.save_data()
            return model
        return None

    def get_user_models(self, user_id: str, include_private: bool = True) -> List[ModelMetadata]:
        """Get all models by a user"""
        user_models = []
        for model in self.models.values():
            if model.user_id == user_id and model.status == ModelStatus.ACTIVE:
                if include_private or model.visibility == ModelVisibility.PUBLIC:
                    user_models.append(model)
        return user_models

    def get_public_models(self, limit: int = 50, offset: int = 0,
                         breed_filter: Optional[str] = None, tag_filter: Optional[str] = None) -> List[ModelMetadata]:
        """Get public models with optional filtering"""
        public_models = [
            model for model in self.models.values()
            if model.visibility == ModelVisibility.PUBLIC and model.status == ModelStatus.ACTIVE
        ]

        # Apply filters
        if breed_filter:
            public_models = [m for m in public_models if m.breed.lower() == breed_filter.lower()]

        if tag_filter:
            public_models = [m for m in public_models if tag_filter.lower() in [t.lower() for t in m.tags]]

        # Sort by creation date (newest first)
        public_models.sort(key=lambda x: x.created_at, reverse=True)

        return public_models[offset:offset + limit]

    def update_model(self, model_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update model metadata (owner only)"""
        model = self.models.get(model_id)
        if not model or model.user_id != user_id or model.status != ModelStatus.ACTIVE:
            return False

        # Update allowed fields
        allowed_fields = ['title', 'description', 'tags', 'visibility', 'thumbnail_path']
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'visibility':
                    value = ModelVisibility(value)
                setattr(model, field, value)

        model.updated_at = datetime.now().isoformat()
        self.save_data()
        logger.info(f"📝 Updated model {model_id}: {model.title}")
        return True

    def delete_model(self, model_id: str, user_id: str) -> bool:
        """Delete model from gallery (owner only)"""
        model = self.models.get(model_id)
        if not model or model.user_id != user_id:
            return False

        model.status = ModelStatus.DELETED
        model.updated_at = datetime.now().isoformat()
        self.save_data()

        # Optionally remove files
        try:
            if os.path.exists(model.file_path):
                os.remove(model.file_path)
            if model.thumbnail_path and os.path.exists(model.thumbnail_path):
                os.remove(model.thumbnail_path)
        except Exception as e:
            logger.warning(f"⚠️ Failed to remove model files: {e}")

        logger.info(f"🗑️ Deleted model {model_id}: {model.title}")
        return True

    def like_model(self, model_id: str, user_id: str) -> bool:
        """Like/unlike a model"""
        model = self.models.get(model_id)
        if not model or model.status != ModelStatus.ACTIVE:
            return False

        # In a real implementation, you'd track individual user likes
        # For now, just increment the counter
        model.update_stats("like")
        self.save_data()
        return True

    def download_model(self, model_id: str, user_id: str) -> Optional[str]:
        """Record model download and return file path"""
        model = self.models.get(model_id)
        if not model or model.status != ModelStatus.ACTIVE:
            return None

        # Check if user has access
        if model.visibility == ModelVisibility.PRIVATE and model.user_id != user_id:
            return None

        model.update_stats("download")
        self.save_data()
        return model.file_path

    def add_comment(self, model_id: str, user_id: str, username: str, content: str) -> Optional[GalleryComment]:
        """Add a comment to a model"""
        model = self.models.get(model_id)
        if not model or model.status != ModelStatus.ACTIVE:
            return None

        comment_id = str(uuid.uuid4())
        comment = GalleryComment(
            comment_id=comment_id,
            model_id=model_id,
            user_id=user_id,
            username=username,
            content=content
        )

        self.comments[comment_id] = comment
        self.save_data()

        logger.info(f"💬 Added comment to model {model_id} by {username}")
        return comment

    def get_model_comments(self, model_id: str) -> List[GalleryComment]:
        """Get all comments for a model"""
        model_comments = [
            comment for comment in self.comments.values()
            if comment.model_id == model_id
        ]
        # Sort by creation date (newest first)
        model_comments.sort(key=lambda x: x.created_at, reverse=True)
        return model_comments

    def get_popular_models(self, limit: int = 10) -> List[ModelMetadata]:
        """Get most popular models by download count"""
        popular_models = [
            model for model in self.models.values()
            if model.visibility == ModelVisibility.PUBLIC and model.status == ModelStatus.ACTIVE
        ]

        # Sort by download count, then by like count
        popular_models.sort(key=lambda x: (x.download_count, x.like_count), reverse=True)
        return popular_models[:limit]

    def get_recent_models(self, limit: int = 10) -> List[ModelMetadata]:
        """Get most recently added public models"""
        recent_models = [
            model for model in self.models.values()
            if model.visibility == ModelVisibility.PUBLIC and model.status == ModelStatus.ACTIVE
        ]

        recent_models.sort(key=lambda x: x.created_at, reverse=True)
        return recent_models[:limit]

    def search_models(self, query: str, limit: int = 20) -> List[ModelMetadata]:
        """Search models by title, description, breed, or tags"""
        query_lower = query.lower()
        matching_models = []

        for model in self.models.values():
            if model.status != ModelStatus.ACTIVE or model.visibility != ModelVisibility.PUBLIC:
                continue

            # Search in title, description, breed, and tags
            searchable_text = f"{model.title} {model.description} {model.breed} {' '.join(model.tags)}".lower()

            if query_lower in searchable_text:
                matching_models.append(model)

        # Sort by relevance (simple: creation date for now)
        matching_models.sort(key=lambda x: x.created_at, reverse=True)
        return matching_models[:limit]

    def get_gallery_stats(self) -> Dict[str, Any]:
        """Get gallery statistics"""
        total_models = len([m for m in self.models.values() if m.status == ModelStatus.ACTIVE])
        public_models = len([m for m in self.models.values()
                           if m.status == ModelStatus.ACTIVE and m.visibility == ModelVisibility.PUBLIC])
        total_comments = len(self.comments)

        breed_counts = {}
        for model in self.models.values():
            if model.status == ModelStatus.ACTIVE and model.visibility == ModelVisibility.PUBLIC:
                breed_counts[model.breed] = breed_counts.get(model.breed, 0) + 1

        return {
            'total_models': total_models,
            'public_models': public_models,
            'total_comments': total_comments,
            'breed_distribution': breed_counts,
            'total_downloads': sum(m.download_count for m in self.models.values()),
            'total_likes': sum(m.like_count for m in self.models.values()),
            'total_views': sum(m.view_count for m in self.models.values())
        }

# Global gallery instance
gallery_service = ModelGalleryService()

def get_gallery_service():
    """Get the global gallery service instance"""
    return gallery_service

# Convenience functions for easy integration
def add_model_to_gallery(user_id: str, title: str, description: str, breed: str,
                        file_path: str, **kwargs) -> ModelMetadata:
    """Add a model to the gallery"""
    return gallery_service.add_model(user_id, title, description, breed, file_path, **kwargs)

def get_public_models(limit: int = 20, **filters) -> List[ModelMetadata]:
    """Get public models with filters"""
    return gallery_service.get_public_models(limit=limit, **filters)

def search_gallery(query: str, limit: int = 20) -> List[ModelMetadata]:
    """Search the model gallery"""
    return gallery_service.search_models(query, limit)

if __name__ == "__main__":
    # Example usage
    print("🚀 PetPlantr Model Gallery Service")
    print("Testing gallery functionality...")

    try:
        # Add some test models
        model1 = add_model_to_gallery(
            "user_123", "Golden Retriever Planter", "Beautiful golden retriever planter",
            "Golden Retriever", "/tmp/model1.stl", quality="ultra", size="large",
            tags=["golden", "retriever", "planter"]
        )

        model2 = add_model_to_gallery(
            "user_456", "Labrador Planter", "Classic labrador planter design",
            "Labrador", "/tmp/model2.stl", quality="high", size="medium",
            tags=["labrador", "classic", "planter"]
        )

        print(f"🖼️ Added models: {model1.title}, {model2.title}")

        # Get public models
        public_models = get_public_models(limit=10)
        print(f"📚 Found {len(public_models)} public models")

        # Search models
        search_results = search_gallery("golden", limit=5)
        print(f"🔍 Search results for 'golden': {len(search_results)} models")

        # Get gallery stats
        stats = gallery_service.get_gallery_stats()
        print(f"📊 Gallery stats: {stats}")

        print("✅ Gallery service test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
