import asyncio
from pathlib import Path
from typing import Callable, Optional

from pyrogram import Client
from pyrogram.types import Message

from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger("telegram_service")


class TelegramService:
    def __init__(self):
        self.client: Optional[Client] = None

    async def start(self):
        self.client = Client(
            "subsplease_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            in_memory=True,
        )
        await self.client.start()
        logger.info("Telegram client started")

    async def stop(self):
        if self.client:
            await self.client.stop()
            logger.info("Telegram client stopped")

    async def upload_file(
        self,
        file_path: Path,
        caption: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> Optional[Message]:
        try:
            msg = await self.client.send_document(
                chat_id=Config.DB_CHANNEL_ID,
                document=str(file_path),
                caption=caption,
                progress=progress_callback,
            )
            logger.info(f"Uploaded {file_path.name} to DB Channel (msg_id={msg.id})")
            return msg
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    async def copy_message(
        self, from_chat_id: int, msg_id: int, to_chat_id: int
    ) -> Optional[Message]:
        try:
            return await self.client.copy_message(
                chat_id=to_chat_id,
                from_chat_id=from_chat_id,
                message_id=msg_id,
            )
        except Exception as e:
            logger.error(f"Copy message failed: {e}")
            return None

    async def forward_message(
        self, from_chat_id: int, msg_id: int, to_chat_id: int
    ) -> Optional[Message]:
        try:
            return await self.client.forward_message(
                chat_id=to_chat_id,
                from_chat_id=from_chat_id,
                message_id=msg_id,
            )
        except Exception as e:
            logger.error(f"Forward message failed: {e}")
            return None

    async def send_message(
        self, chat_id: int, text: str, **kwargs
    ) -> Optional[Message]:
        try:
            return await self.client.send_message(
                chat_id=chat_id, text=text, **kwargs
            )
        except Exception as e:
            logger.error(f"Send message failed: {e}")
            return None

    async def get_message(self, chat_id: int, msg_id: int) -> Optional[Message]:
        try:
            return await self.client.get_messages(chat_id=chat_id, message_ids=msg_id)
        except Exception as e:
            logger.error(f"Get message failed: {e}")
            return None

    async def handle_start_param(
        self, user_id: int, encoded_param: str, db_channel_id: int
    ) -> bool:
        from services.fileshare_service import FileShareService

        fs = FileShareService()
        result = fs.resolve_share_link(encoded_param, db_channel_id)
        if not result:
            return False

        msg_ids = result["message_ids"]
        for mid in msg_ids:
            await asyncio.sleep(0.3)
            try:
                await self.client.copy_message(
                    chat_id=user_id,
                    from_chat_id=db_channel_id,
                    message_id=mid,
                )
            except Exception as e:
                logger.error(f"Failed to send file to user {user_id}: {e}")
                return False

        fs.increment_access(encoded_param)
        return True
