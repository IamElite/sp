import time
from typing import Optional


class JobModel:
    def __init__(
        self,
        type: str,
        status: str = "pending",
        payload: Optional[dict] = None,
        priority: int = 0,
    ):
        self._id = None
        self.type = type
        self.status = status
        self.payload = payload or {}
        self.priority = priority
        self.progress = 0.0
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "status": self.status,
            "payload": self.payload,
            "priority": self.priority,
            "progress": self.progress,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JobModel":
        obj = cls(
            type=data.get("type", ""),
            status=data.get("status", "pending"),
            payload=data.get("payload", {}),
            priority=data.get("priority", 0),
        )
        obj._id = data.get("_id")
        obj.progress = data.get("progress", 0.0)
        obj.error = data.get("error")
        obj.created_at = data.get("created_at", time.time())
        obj.started_at = data.get("started_at")
        obj.completed_at = data.get("completed_at")
        return obj
