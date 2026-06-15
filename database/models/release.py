import time
from typing import Optional


class ReleaseModel:
    def __init__(
        self,
        release_id: str,
        title: str,
        episode: str,
        quality: str,
        source: str = "subsplease",
        release_date: Optional[str] = None,
        file_name: Optional[str] = None,
        magnet_uri: Optional[str] = None,
        is_batch: bool = False,
        processed: bool = False,
        metadata: Optional[dict] = None,
    ):
        self._id = release_id
        self.title = title
        self.episode = episode
        self.quality = quality
        self.source = source
        self.release_date = release_date
        self.file_name = file_name
        self.magnet_uri = magnet_uri
        self.is_batch = is_batch
        self.processed = processed
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.updated_at = time.time()

    def to_dict(self) -> dict:
        return {
            "_id": self._id,
            "title": self.title,
            "episode": self.episode,
            "quality": self.quality,
            "source": self.source,
            "release_date": self.release_date,
            "file_name": self.file_name,
            "magnet_uri": self.magnet_uri,
            "is_batch": self.is_batch,
            "processed": self.processed,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReleaseModel":
        obj = cls(
            release_id=data.get("_id", ""),
            title=data.get("title", ""),
            episode=data.get("episode", ""),
            quality=data.get("quality", ""),
            source=data.get("source", "subsplease"),
        )
        obj.release_date = data.get("release_date")
        obj.file_name = data.get("file_name")
        obj.magnet_uri = data.get("magnet_uri")
        obj.is_batch = data.get("is_batch", False)
        obj.processed = data.get("processed", False)
        obj.metadata = data.get("metadata", {})
        obj.created_at = data.get("created_at", time.time())
        obj.updated_at = data.get("updated_at", time.time())
        return obj
