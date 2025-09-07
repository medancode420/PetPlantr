#!/usr/bin/env python3
"""
PetPlantr Advanced Analytics Service
Provides comprehensive analytics, monitoring, and insights for the platform
"""

import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsMetrics:
    """Core analytics metrics data structure"""
    total_users: int = 0
    active_users_24h: int = 0
    active_users_7d: int = 0
    total_generations: int = 0
    successful_generations: int = 0
    failed_generations: int = 0
    average_processing_time: float = 0.0
    popular_breeds: Dict[str, int] = field(default_factory=dict)
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    size_distribution: Dict[str, int] = field(default_factory=dict)
    peak_usage_hours: List[int] = field(default_factory=list)
    api_response_times: Dict[str, float] = field(default_factory=dict)
    error_rates: Dict[str, float] = field(default_factory=dict)
    storage_usage: Dict[str, int] = field(default_factory=dict)
    revenue_metrics: Dict[str, float] = field(default_factory=dict)

class AdvancedAnalytics:
    """Advanced analytics service for PetPlantr"""

    def __init__(self):
        self.metrics = AnalyticsMetrics()
        self.events_buffer = []
        self.max_buffer_size = 10000
        self.analytics_file = "analytics_data.json"
        self.load_persistent_data()

    def load_persistent_data(self):
        """Load analytics data from persistent storage"""
        try:
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r') as f:
                    data = json.load(f)
                    # Convert dict back to AnalyticsMetrics
                    for key, value in data.items():
                        if hasattr(self.metrics, key):
                            setattr(self.metrics, key, value)
                logger.info("✅ Analytics data loaded from persistent storage")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load analytics data: {e}")

    def save_persistent_data(self):
        """Save analytics data to persistent storage"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(asdict(self.metrics), f, indent=2)
            logger.info("💾 Analytics data saved to persistent storage")
        except Exception as e:
            logger.error(f"❌ Failed to save analytics data: {e}")

    def track_event(self, event_type: str, user_id: str, data: Dict[str, Any]):
        """Track an analytics event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'data': data
        }

        self.events_buffer.append(event)

        # Process event immediately for real-time metrics
        self._process_event(event)

        # Maintain buffer size
        if len(self.events_buffer) > self.max_buffer_size:
            # Save oldest events to file and clear buffer
            self._archive_old_events()
            self.events_buffer = self.events_buffer[-self.max_buffer_size//2:]

    def _process_event(self, event: Dict[str, Any]):
        """Process an event for real-time analytics"""
        event_type = event['event_type']
        data = event['data']

        if event_type == 'generation_started':
            self.metrics.total_generations += 1
        elif event_type == 'generation_completed':
            self.metrics.successful_generations += 1
            if 'processing_time' in data:
                # Update rolling average
                current_avg = self.metrics.average_processing_time
                total_processed = self.metrics.successful_generations
                self.metrics.average_processing_time = (
                    (current_avg * (total_processed - 1)) + data['processing_time']
                ) / total_processed

            # Track breed popularity
            if 'breed' in data:
                breed = data['breed']
                self.metrics.popular_breeds[breed] = self.metrics.popular_breeds.get(breed, 0) + 1

            # Track quality distribution
            if 'quality' in data:
                quality = data['quality']
                self.metrics.quality_distribution[quality] = self.metrics.quality_distribution.get(quality, 0) + 1

            # Track size distribution
            if 'size' in data:
                size = data['size']
                self.metrics.size_distribution[size] = self.metrics.size_distribution.get(size, 0) + 1

        elif event_type == 'generation_failed':
            self.metrics.failed_generations += 1

        elif event_type == 'user_login':
            self.metrics.total_users = max(self.metrics.total_users, int(event['user_id'].split('_')[-1]) if '_' in event['user_id'] else 1)

        # Track peak usage hours
        current_hour = datetime.now().hour
        if current_hour not in self.metrics.peak_usage_hours:
            self.metrics.peak_usage_hours.append(current_hour)
            self.metrics.peak_usage_hours.sort()

    def _archive_old_events(self):
        """Archive old events to file for historical analysis"""
        try:
            archive_file = f"analytics_archive_{int(time.time())}.json"
            with open(archive_file, 'w') as f:
                json.dump(self.events_buffer[:self.max_buffer_size//2], f, indent=2)
            logger.info(f"📦 Archived {len(self.events_buffer[:self.max_buffer_size//2])} events to {archive_file}")
        except Exception as e:
            logger.error(f"❌ Failed to archive events: {e}")

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time analytics metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'metrics': asdict(self.metrics),
            'buffer_size': len(self.events_buffer),
            'uptime': time.time()  # Could be enhanced with actual service uptime
        }

    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights for a specific user"""
        user_events = [e for e in self.events_buffer if e['user_id'] == user_id]

        insights = {
            'total_generations': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'favorite_breed': None,
            'preferred_quality': None,
            'average_processing_time': 0.0,
            'last_activity': None
        }

        if user_events:
            insights['last_activity'] = max(e['timestamp'] for e in user_events)

            for event in user_events:
                if event['event_type'] == 'generation_started':
                    insights['total_generations'] += 1
                elif event['event_type'] == 'generation_completed':
                    insights['successful_generations'] += 1
                    if 'processing_time' in event['data']:
                        insights['average_processing_time'] = (
                            (insights['average_processing_time'] * (insights['successful_generations'] - 1)) +
                            event['data']['processing_time']
                        ) / insights['successful_generations']
                elif event['event_type'] == 'generation_failed':
                    insights['failed_generations'] += 1

        return insights

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        total_generations = self.metrics.successful_generations + self.metrics.failed_generations
        success_rate = (
            self.metrics.successful_generations / total_generations * 100
            if total_generations > 0 else 0
        )

        return {
            'overall_health': 'healthy' if success_rate > 95 else 'warning' if success_rate > 85 else 'critical',
            'success_rate': f"{success_rate:.1f}%",
            'total_requests': total_generations,
            'active_users': self.metrics.active_users_24h,
            'average_response_time': f"{self.metrics.average_processing_time:.2f}s",
            'error_rate': f"{(self.metrics.failed_generations / total_generations * 100) if total_generations > 0 else 0:.1f}%",
            'storage_status': 'normal',  # Could be enhanced with actual storage monitoring
            'last_updated': datetime.now().isoformat()
        }

    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        insights = {
            'bottlenecks': [],
            'recommendations': [],
            'trends': [],
            'optimization_opportunities': []
        }

        # Analyze processing times
        if self.metrics.average_processing_time > 30:
            insights['bottlenecks'].append('High average processing time detected')
            insights['recommendations'].append('Consider upgrading to GPU-accelerated processing')

        # Analyze error rates
        total = self.metrics.successful_generations + self.metrics.failed_generations
        if total > 0:
            error_rate = self.metrics.failed_generations / total
            if error_rate > 0.1:
                insights['bottlenecks'].append('High error rate detected')
                insights['recommendations'].append('Review error handling and add retry mechanisms')

        # Analyze popular breeds
        if self.metrics.popular_breeds:
            top_breed = max(self.metrics.popular_breeds.items(), key=lambda x: x[1])
            insights['trends'].append(f"'{top_breed[0]}' is the most popular breed with {top_breed[1]} generations")

        # Storage optimization
        if len(self.events_buffer) > self.max_buffer_size * 0.8:
            insights['optimization_opportunities'].append('Consider increasing analytics buffer size or implementing data archiving')

        return insights

# Global analytics instance
analytics = AdvancedAnalytics()

def get_analytics_service():
    """Get the global analytics service instance"""
    return analytics

# Convenience functions for easy integration
def track_generation_started(user_id: str, breed: Optional[str] = None, quality: Optional[str] = None, size: Optional[str] = None):
    """Track generation started event"""
    analytics.track_event('generation_started', user_id, {
        'breed': breed,
        'quality': quality,
        'size': size,
        'timestamp': datetime.now().isoformat()
    })

def track_generation_completed(user_id: str, processing_time: float, breed: Optional[str] = None, quality: Optional[str] = None, size: Optional[str] = None):
    """Track generation completed event"""
    analytics.track_event('generation_completed', user_id, {
        'processing_time': processing_time,
        'breed': breed,
        'quality': quality,
        'size': size,
        'timestamp': datetime.now().isoformat()
    })

def track_generation_failed(user_id: str, error: str, breed: Optional[str] = None):
    """Track generation failed event"""
    analytics.track_event('generation_failed', user_id, {
        'error': error,
        'breed': breed,
        'timestamp': datetime.now().isoformat()
    })

def track_user_login(user_id: str):
    """Track user login event"""
    analytics.track_event('user_login', user_id, {
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    # Example usage
    print("🚀 PetPlantr Advanced Analytics Service")
    print("Testing analytics functionality...")

    # Simulate some events
    track_user_login("user_123")
    track_generation_started("user_123", "Golden Retriever", "high", "medium")
    track_generation_completed("user_123", 15.5, "Golden Retriever", "high", "medium")

    # Get metrics
    metrics = analytics.get_realtime_metrics()
    print(f"📊 Total generations: {metrics['metrics']['total_generations']}")
    print(f"✅ Successful generations: {metrics['metrics']['successful_generations']}")
    print(f"⏱️  Average processing time: {metrics['metrics']['average_processing_time']:.2f}s")

    # Get system health
    health = analytics.get_system_health()
    print(f"🏥 System health: {health['overall_health']}")
    print(f"📈 Success rate: {health['success_rate']}")

    print("✅ Analytics service test completed!")
