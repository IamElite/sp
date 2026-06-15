from pathlib import Path
from typing import Callable, Optional

from pyrogram.types import Message

from config.settings import Config
from plugins.uploader.base import BaseUploader, UploadResult
from services.telegram_service import TelegramService
from utils.logger import setup_logger

logger = setup_logger("telegram_uploader")


class TelegramUploader(BaseUploader):
    def __init__(self, tg: TelegramService):
        self.tg = tg
        self._current_msg: Optional[Message] = None

    async def upload(
        self,
        file_path: Path,
        caption: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> UploadResult:
        doc = await self.tg.client.send_document(
            chat_id=Config.DB_CHANNEL_ID,
            document=str(file_path),
            caption=caption,
            progress=progress_callback,
            force_document=True,
        )

        if not doc:
            raise RuntimeError(f"Upload failed for {file_path.name}")

        file_id = doc.document.file_id if doc.document else ""
        mime = doc.document.mime_type if doc.document else None

        logger.info(f"Uploaded {file_path.name} → msg_id={doc.id}")

        return UploadResult(
            message_id=doc.id,
            channel_id=Config.DB_CHANNEL_ID,
            telegram_file_id=file_id,
            file_name=file_path.name,
            file_size=file_path.stat().st_size,
            mime_type=mime,
        )
