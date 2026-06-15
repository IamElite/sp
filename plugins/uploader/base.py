from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class UploadResult:
    message_id: int
    channel_id: int
    telegram_file_id: str
    file_name: str
    file_size: int
    mime_type: Optional[str] = None


class BaseUploader(ABC):
    @abstractmethod
    async def upload(
        self,
        file_path: Path,
        caption: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> UploadResult:
        ...
