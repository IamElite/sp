import base64
import time
from typing import Optional

from database.mongo import db
from utils.logger import setup_logger

logger = setup_logger("fileshare_service")


class PayloadEncoder:
    PREFIX = "get-"

    @staticmethod
    def encode(message_id: int, channel_id: int, is_batch: bool = False, batch_ids: Optional[list[int]] = None) -> str:
        abs_ch = abs(channel_id)
        if is_batch and batch_ids:
            ids = "-".join(str(mid * abs_ch) for mid in batch_ids)
            raw = f"{PayloadEncoder.PREFIX}{ids}"
        else:
            raw = f"{PayloadEncoder.PREFIX}{message_id * abs_ch}"

        encoded = base64.urlsafe_b64encode(raw.encode("ascii")).decode("ascii").rstrip("=")
        return encoded

    @staticmethod
    def decode(encoded: str) -> Optional[dict]:
        try:
            padded = encoded + "=" * (-len(encoded) % 4)
            raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("ascii")
            if not raw.startswith(PayloadEncoder.PREFIX):
                return None
            parts = raw[len(PayloadEncoder.PREFIX):].split("-")
            return {"parts": parts}
        except Exception as e:
            logger.error(f"Decode failed: {e}")
            return None


class FileShareService:
    def __init__(self):
        self.encoder = PayloadEncoder()

    def generate_share_link(
        self,
        message_id: int,
        channel_id: int,
        bot_username: str,
        is_batch: bool = False,
        batch_ids: Optional[list[int]] = None,
    ) -> str:
        encoded = self.encoder.encode(message_id, channel_id, is_batch, batch_ids)
        link = f"https://t.me/{bot_username}?start={encoded}"
        return link

    def resolve_share_link(self, encoded: str, db_channel_id: int) -> Optional[dict]:
        decoded = self.encoder.decode(encoded)
        if not decoded:
            return None

        abs_ch = abs(db_channel_id)
        parts = decoded["parts"]
        msg_ids = [int(p) // abs_ch for p in parts]

        return {
            "message_ids": msg_ids,
            "channel_id": db_channel_id,
        }

    def increment_access(self, encoded_link: str) -> None:
        db.files.update_one(
            {"encoded_link": encoded_link},
            {"$inc": {"access_count": 1}},
        )
