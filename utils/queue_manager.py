import time
from typing import Optional

from database.models.job import JobModel
from database.mongo import db
from utils.logger import setup_logger

logger = setup_logger("queue_manager")


class QueueManager:
    def __init__(self):
        self.collection = db.jobs
        self._poller_active = False

    def enqueue(
        self,
        job_type: str,
        payload: dict,
        priority: int = 0,
    ) -> JobModel:
        job = JobModel(
            type=job_type,
            status="pending",
            payload=payload,
            priority=priority,
        )
        result = self.collection.insert_one(job.to_dict())
        job._id = result.inserted_id
        logger.info(f"Enqueued {job_type} job: {result.inserted_id}")
        return job

    def dequeue(self, job_type: Optional[str] = None) -> Optional[JobModel]:
        query = {"status": "pending"}
        if job_type:
            query["type"] = job_type

        doc = self.collection.find_one_and_update(
            query,
            {"$set": {"status": "running", "started_at": time.time()}},
            sort=[("priority", -1), ("created_at", 1)],
        )
        if doc:
            return JobModel.from_dict(doc)
        return None

    def update_progress(self, job_id, progress: float) -> None:
        self.collection.update_one(
            {"_id": job_id},
            {"$set": {"progress": progress}},
        )

    def update_status(
        self, job_id, status: str, error: Optional[str] = None
    ) -> None:
        update = {
            "status": status,
            "completed_at": time.time() if status in ("done", "failed") else None,
        }
        if error:
            update["error"] = error
        self.collection.update_one({"_id": job_id}, {"$set": update})

    def get_stats(self) -> dict:
        total = self.collection.count_documents({})
        pending = self.collection.count_documents({"status": "pending"})
        running = self.collection.count_documents({"status": "running"})
        done = self.collection.count_documents({"status": "done"})
        failed = self.collection.count_documents({"status": "failed"})
        return {
            "total": total,
            "pending": pending,
            "running": running,
            "done": done,
            "failed": failed,
        }

    def retry_failed(self, max_retries: int = 3) -> int:
        failed_jobs = self.collection.find({
            "status": "failed",
            "payload.retry_count": {"$lt": max_retries},
        })
        count = 0
        for job in failed_jobs:
            retries = job.get("payload", {}).get("retry_count", 0) + 1
            self.collection.update_one(
                {"_id": job["_id"]},
                {
                    "$set": {
                        "status": "pending",
                        "progress": 0,
                        "payload.retry_count": retries,
                    }
                },
            )
            count += 1
        return count

    def cleanup_old_jobs(self, hours: int = 24) -> int:
        cutoff = time.time() - hours * 3600
        result = self.collection.delete_many({
            "status": {"$in": ["done", "failed"]},
            "completed_at": {"$lt": cutoff},
        })
        if result.deleted_count:
            logger.info(f"Cleaned {result.deleted_count} old jobs")
        return result.deleted_count
