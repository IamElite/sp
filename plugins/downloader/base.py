from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional


class BaseDownloader(ABC):
    @abstractmethod
    async def download(
        self,
        source: str,
        dest: Path,
        progress_callback: Optional[Callable] = None,
    ) -> Path:
        ...

    @abstractmethod
    async def cancel(self) -> None:
        ...
