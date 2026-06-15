import asyncio
from typing import Optional

from database.mongo import db
from plugins.fileshare.encoder import PayloadCodec
from utils.logger import setup_logger

logger = setup_logger("file_forwarder")


class FileForwarder:
    async def forward_to_user(
        self,
        client,
        user_id: int,
        encoded_param: str,
        db_channel_id: int,
    ) -> bool:
        decoded = PayloadCodec.decode(encoded_param, db_channel_id)
        if not decoded:
            return False

        for msg_id in decoded["message_ids"]:
            try:
                await asyncio.sleep(0.35)
                await client.copy_message(
                    chat_id=user_id,
                    from_chat_id=db_channel_id,
                    message_id=msg_id,
                )
            except Exception as e:
                logger.error(f"Forward {msg_id} to {user_id} failed: {e}")
                return False

        self._track_access(encoded_param)
        return True

    def _track_access(self, encoded_link: str) -> None:
        db.files.update_one(
            {"encoded_link": encoded_link},
            {"$inc": {"access_count": 1}},
        )
