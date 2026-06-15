import time
from typing import Optional


class FileModel:
    def __init__(
        self,
        release_hash: str,
        message_id: int,
        channel_id: int,
        telegram_file_id: str,
        file_name: str,
        file_size: int = 0,
        mime_type: Optional[str] = None,
        encoded_link: Optional[str] = None,
        batch_ids: Optional[list] = None,
    ):
        self.release_hash = release_hash
        self.message_id = message_id
        self.channel_id = channel_id
        self.telegram_file_id = telegram_file_id
        self.file_name = file_name
        self.file_size = file_size
        self.mime_type = mime_type
        self.encoded_link = encoded_link
        self.batch_ids = batch_ids
        self.access_count = 0
        self.uploaded_at = time.time()

    def to_dict(self) -> dict:
        return {
            "release_hash": self.release_hash,
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "telegram_file_id": self.telegram_file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "encoded_link": self.encoded_link,
            "batch_ids": self.batch_ids,
            "access_count": self.access_count,
            "uploaded_at": self.uploaded_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileModel":
        obj = cls(
            release_hash=data.get("release_hash", ""),
            message_id=data.get("message_id", 0),
            channel_id=data.get("channel_id", 0),
            telegram_file_id=data.get("telegram_file_id", ""),
            file_name=data.get("file_name", ""),
        )
        obj.file_size = data.get("file_size", 0)
        obj.mime_type = data.get("mime_type")
        obj.encoded_link = data.get("encoded_link")
        obj.batch_ids = data.get("batch_ids")
        obj.access_count = data.get("access_count", 0)
        obj.uploaded_at = data.get("uploaded_at", time.time())
        return obj
