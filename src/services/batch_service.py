#!/usr/bin/env python3
"""
PetPlantr Batch Processing Service
Handles batch generation requests, queue management, and parallel processing
"""

import os
import json
import uuid
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class BatchStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchJob:
    """Individual job within a batch"""
    job_id: str
    batch_id: str
    user_id: str
    breed: str
    quality: str = "high"
    size: str = "medium"
    custom_params: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.QUEUED
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time: float = 0.0
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()

    def start_processing(self):
        """Mark job as started"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.now().isoformat()

    def complete(self, result_path: str, processing_time: float):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.processing_time = processing_time
        self.result_path = result_path

    def fail(self, error_message: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.error_message = error_message

    def cancel(self):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now().isoformat()

@dataclass
class BatchRequest:
    """Batch processing request"""
    batch_id: str
    user_id: str
    title: str
    description: str = ""
    jobs: List[BatchJob] = field(default_factory=list)
    status: BatchStatus = BatchStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    total_processing_time: float = 0.0
    priority: int = 1  # 1=low, 2=medium, 3=high
    max_concurrent_jobs: int = 3
    estimated_completion_time: Optional[str] = None

    def __post_init__(self):
        if self.created_at == "":
            self.created_at = datetime.now().isoformat()

    def add_job(self, breed: str, quality: str = "high", size: str = "medium",
                custom_params: Optional[Dict[str, Any]] = None) -> BatchJob:
        """Add a job to the batch"""
        job = BatchJob(
            job_id=str(uuid.uuid4()),
            batch_id=self.batch_id,
            user_id=self.user_id,
            breed=breed,
            quality=quality,
            size=size,
            custom_params=custom_params or {}
        )
        self.jobs.append(job)
        self.total_jobs = len(self.jobs)
        return job

    def start_processing(self):
        """Mark batch as started"""
        self.status = BatchStatus.PROCESSING
        self.started_at = datetime.now().isoformat()

    def update_progress(self):
        """Update batch progress"""
        self.completed_jobs = len([j for j in self.jobs if j.status == JobStatus.COMPLETED])
        self.failed_jobs = len([j for j in self.jobs if j.status == JobStatus.FAILED])

        if self.completed_jobs + self.failed_jobs == self.total_jobs:
            if self.failed_jobs == 0:
                self.status = BatchStatus.COMPLETED
            else:
                self.status = BatchStatus.FAILED
            self.completed_at = datetime.now().isoformat()

        # Update total processing time
        self.total_processing_time = sum(j.processing_time for j in self.jobs if j.processing_time > 0)

    def get_progress_percentage(self) -> float:
        """Get completion percentage"""
        if self.total_jobs == 0:
            return 0.0
        return ((self.completed_jobs + self.failed_jobs) / self.total_jobs) * 100

    def get_eta(self) -> Optional[str]:
        """Estimate time of completion"""
        if self.total_jobs == 0 or self.completed_jobs == 0:
            return None

        avg_time_per_job = self.total_processing_time / self.completed_jobs
        remaining_jobs = self.total_jobs - self.completed_jobs - self.failed_jobs
        eta_seconds = remaining_jobs * avg_time_per_job

        eta_time = datetime.now() + timedelta(seconds=eta_seconds)
        return eta_time.isoformat()

class BatchProcessingService:
    """Batch processing service for PetPlantr"""

    def __init__(self, max_workers: int = 5):
        self.batches_file = "batch_requests.json"
        self.batches: Dict[str, BatchRequest] = {}
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_lock = threading.Lock()
        self.load_data()

        # Start background cleanup task (will be started when event loop is available)
        self.cleanup_task = None

    def load_data(self):
        """Load batch data from persistent storage"""
        try:
            if os.path.exists(self.batches_file):
                with open(self.batches_file, 'r') as f:
                    data = json.load(f)
                    for batch_id, batch_data in data.items():
                        # Convert string enums back to enum
                        batch_data['status'] = BatchStatus(batch_data['status'])
                        # Reconstruct jobs
                        jobs_data = batch_data.pop('jobs', [])
                        batch = BatchRequest(**batch_data)
                        for job_data in jobs_data:
                            job_data['status'] = JobStatus(job_data['status'])
                            job = BatchJob(**job_data)
                            batch.jobs.append(job)
                        self.batches[batch_id] = batch

            logger.info(f"✅ Loaded {len(self.batches)} batch requests")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load batch data: {e}")

    def save_data(self):
        """Save batch data to persistent storage"""
        try:
            batches_data = {}
            for batch_id, batch in self.batches.items():
                batch_dict = asdict(batch)
                # Convert enums to strings for JSON serialization
                batch_dict['status'] = batch.status.value
                # Convert jobs
                jobs_data = []
                for job in batch.jobs:
                    job_dict = asdict(job)
                    job_dict['status'] = job.status.value
                    jobs_data.append(job_dict)
                batch_dict['jobs'] = jobs_data
                batches_data[batch_id] = batch_dict

            with open(self.batches_file, 'w') as f:
                json.dump(batches_data, f, indent=2)

            logger.info("💾 Batch data saved to persistent storage")
        except Exception as e:
            logger.error(f"❌ Failed to save batch data: {e}")

    def create_batch(self, user_id: str, title: str, description: str = "",
                    priority: int = 1, max_concurrent_jobs: int = 3) -> BatchRequest:
        """Create a new batch request"""
        batch_id = str(uuid.uuid4())

        batch = BatchRequest(
            batch_id=batch_id,
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            max_concurrent_jobs=max_concurrent_jobs
        )

        self.batches[batch_id] = batch
        self.save_data()

        logger.info(f"📦 Created batch {batch_id} for user {user_id}: {title}")
        return batch

    def add_job_to_batch(self, batch_id: str, breed: str, quality: str = "high",
                        size: str = "medium", custom_params: Optional[Dict[str, Any]] = None) -> Optional[BatchJob]:
        """Add a job to an existing batch"""
        batch = self.batches.get(batch_id)
        if not batch or batch.status != BatchStatus.PENDING:
            return None

        job = batch.add_job(breed, quality, size, custom_params)
        self.save_data()
        return job

    def start_batch_processing(self, batch_id: str) -> bool:
        """Start processing a batch"""
        batch = self.batches.get(batch_id)
        if not batch or batch.status != BatchStatus.PENDING:
            return False

        batch.start_processing()
        self.save_data()

        # Start processing jobs
        asyncio.create_task(self._process_batch(batch))

        logger.info(f"▶️ Started processing batch {batch_id}")
        return True

    async def _process_batch(self, batch: BatchRequest):
        """Process all jobs in a batch"""
        semaphore = asyncio.Semaphore(batch.max_concurrent_jobs)

        async def process_job(job: BatchJob):
            async with semaphore:
                await self._process_single_job(job)
                batch.update_progress()
                self.save_data()

        # Create tasks for all jobs
        tasks = [process_job(job) for job in batch.jobs]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Final update
        batch.update_progress()
        self.save_data()

        logger.info(f"✅ Completed processing batch {batch.batch_id}")

    async def _process_single_job(self, job: BatchJob):
        """Process a single job (placeholder for actual generation logic)"""
        try:
            job.start_processing()

            # Simulate processing time based on quality
            processing_times = {"low": 5, "medium": 10, "high": 20, "ultra": 40}
            base_time = processing_times.get(job.quality, 10)

            # Add some randomness
            import random
            actual_time = base_time * (0.8 + random.random() * 0.4)

            await asyncio.sleep(actual_time)

            # Simulate occasional failures
            if random.random() < 0.05:  # 5% failure rate
                raise Exception("Simulated generation failure")

            # Create mock result
            result_path = f"/generated/{job.job_id}.stl"
            job.complete(result_path, actual_time)

            logger.info(f"✅ Completed job {job.job_id} in {actual_time:.1f}s")

        except Exception as e:
            error_msg = str(e)
            job.fail(error_msg)
            logger.error(f"❌ Failed job {job.job_id}: {error_msg}")

    def get_batch(self, batch_id: str) -> Optional[BatchRequest]:
        """Get batch by ID"""
        return self.batches.get(batch_id)

    def get_user_batches(self, user_id: str, limit: int = 20) -> List[BatchRequest]:
        """Get all batches for a user"""
        user_batches = [
            batch for batch in self.batches.values()
            if batch.user_id == user_id
        ]

        # Sort by creation date (newest first)
        user_batches.sort(key=lambda x: x.created_at, reverse=True)
        return user_batches[:limit]

    def cancel_batch(self, batch_id: str, user_id: str) -> bool:
        """Cancel a batch (user must own it)"""
        batch = self.batches.get(batch_id)
        if not batch or batch.user_id != user_id:
            return False

        if batch.status not in [BatchStatus.PENDING, BatchStatus.PROCESSING]:
            return False

        batch.status = BatchStatus.CANCELLED
        batch.completed_at = datetime.now().isoformat()

        # Cancel all pending jobs
        for job in batch.jobs:
            if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                job.cancel()

        self.save_data()
        logger.info(f"🚫 Cancelled batch {batch_id}")
        return True

    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed batch status"""
        batch = self.batches.get(batch_id)
        if not batch:
            return None

        return {
            'batch_id': batch.batch_id,
            'title': batch.title,
            'status': batch.status.value,
            'progress_percentage': batch.get_progress_percentage(),
            'total_jobs': batch.total_jobs,
            'completed_jobs': batch.completed_jobs,
            'failed_jobs': batch.failed_jobs,
            'eta': batch.get_eta(),
            'created_at': batch.created_at,
            'started_at': batch.started_at,
            'completed_at': batch.completed_at,
            'total_processing_time': batch.total_processing_time
        }

    def get_job_status(self, batch_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed job status"""
        batch = self.batches.get(batch_id)
        if not batch:
            return None

        job = next((j for j in batch.jobs if j.job_id == job_id), None)
        if not job:
            return None

        return {
            'job_id': job.job_id,
            'batch_id': job.batch_id,
            'breed': job.breed,
            'quality': job.quality,
            'size': job.size,
            'status': job.status.value,
            'created_at': job.created_at,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
            'processing_time': job.processing_time,
            'result_path': job.result_path,
            'error_message': job.error_message
        }

    def start_cleanup_task(self):
        """Start the background cleanup task"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_completed_batches())

    async def _cleanup_completed_batches(self):
        """Background task to clean up old completed batches"""
        while True:
            try:
                # Clean up batches older than 30 days
                cutoff_date = datetime.now() - timedelta(days=30)
                old_batch_ids = []

                for batch_id, batch in self.batches.items():
                    if (batch.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED] and
                        batch.completed_at and
                        datetime.fromisoformat(batch.completed_at) < cutoff_date):
                        old_batch_ids.append(batch_id)

                for batch_id in old_batch_ids:
                    del self.batches[batch_id]

                if old_batch_ids:
                    self.save_data()
                    logger.info(f"🧹 Cleaned up {len(old_batch_ids)} old batches")

            except Exception as e:
                logger.error(f"❌ Error in cleanup task: {e}")

            # Run cleanup every 24 hours
            await asyncio.sleep(86400)

    def get_system_stats(self) -> Dict[str, Any]:
        """Get batch processing system statistics"""
        total_batches = len(self.batches)
        active_batches = len([b for b in self.batches.values() if b.status == BatchStatus.PROCESSING])
        completed_batches = len([b for b in self.batches.values() if b.status == BatchStatus.COMPLETED])

        total_jobs = sum(len(b.jobs) for b in self.batches.values())
        completed_jobs = sum(b.completed_jobs for b in self.batches.values())
        failed_jobs = sum(b.failed_jobs for b in self.batches.values())

        return {
            'total_batches': total_batches,
            'active_batches': active_batches,
            'completed_batches': completed_batches,
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            'average_batch_size': total_jobs / total_batches if total_batches > 0 else 0
        }

# Global batch processing instance
batch_service = BatchProcessingService()

def get_batch_service():
    """Get the global batch processing service instance"""
    return batch_service

# Convenience functions for easy integration
def create_batch_request(user_id: str, title: str, jobs_data: List[Dict[str, Any]]) -> BatchRequest:
    """Create a batch with multiple jobs"""
    batch = batch_service.create_batch(user_id, title)

    for job_data in jobs_data:
        batch_service.add_job_to_batch(
            batch.batch_id,
            job_data['breed'],
            job_data.get('quality', 'high'),
            job_data.get('size', 'medium'),
            job_data.get('custom_params', {})
        )

    return batch

def start_batch_processing(batch_id: str) -> bool:
    """Start processing a batch"""
    return batch_service.start_batch_processing(batch_id)

def get_batch_progress(batch_id: str) -> Optional[Dict[str, Any]]:
    """Get batch progress"""
    return batch_service.get_batch_status(batch_id)

if __name__ == "__main__":
    # Example usage
    print("🚀 PetPlantr Batch Processing Service")
    print("Testing batch processing functionality...")

    async def test_batch():
        try:
            # Create a test batch
            batch = create_batch_request(
                "user_123",
                "Test Batch: Popular Breeds",
                [
                    {"breed": "Golden Retriever", "quality": "high", "size": "large"},
                    {"breed": "Labrador", "quality": "high", "size": "medium"},
                    {"breed": "German Shepherd", "quality": "ultra", "size": "large"},
                    {"breed": "Bulldog", "quality": "medium", "size": "small"},
                    {"breed": "Poodle", "quality": "high", "size": "medium"}
                ]
            )

            print(f"📦 Created batch {batch.batch_id} with {batch.total_jobs} jobs")

            # Start processing
            success = start_batch_processing(batch.batch_id)
            if success:
                print("▶️ Started batch processing")

                # Monitor progress
                for i in range(10):
                    await asyncio.sleep(2)
                    status = get_batch_progress(batch.batch_id)
                    if status:
                        print(f"📊 Progress: {status['progress_percentage']:.1f}% "
                              f"({status['completed_jobs']}/{status['total_jobs']} jobs)")

                    if status and status['status'] in ['completed', 'failed']:
                        break

                # Final status
                final_status = get_batch_progress(batch.batch_id)
                if final_status:
                    print(f"🏁 Final status: {final_status['status']}")
                    print(f"⏱️ Total processing time: {final_status['total_processing_time']:.1f}s")

            # Get system stats
            stats = batch_service.get_system_stats()
            print(f"📊 System stats: {stats}")

            print("✅ Batch processing test completed!")

        except Exception as e:
            print(f"❌ Test failed: {e}")

    # Run the test
    asyncio.run(test_batch())
