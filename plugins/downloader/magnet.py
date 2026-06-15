import asyncio
import subprocess
from pathlib import Path
from typing import Callable, Optional

from plugins.downloader.base import BaseDownloader
from utils.helpers import ensure_download_dir
from utils.logger import setup_logger

logger = setup_logger("magnet_downloader")


class MagnetDownloader(BaseDownloader):
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False

    async def download(
        self,
        source: str,
        dest: Optional[Path] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Path:
        self._cancelled = False
        out_dir = dest or ensure_download_dir()
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting download: {source[:60]}...")

        cmd = [
            "aria2c",
            "--dir", str(out_dir),
            "--max-connection-per-server=16",
            "--split=16",
            "--seed-time=0",
            "--summary-interval=0",
            "--console-log-level=error",
            source,
        ]

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = await self._process.communicate()

        if self._cancelled:
            raise asyncio.CancelledError("Download cancelled")

        if self._process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"aria2c failed: {error_msg}")
            raise RuntimeError(f"Download failed: {error_msg}")

        files = list(out_dir.iterdir())
        if not files:
            raise RuntimeError("No files downloaded")

        video_files = [f for f in files if f.suffix in (".mkv", ".mp4", ".avi", ".mov")]
        if video_files:
            downloaded = video_files[0]
        else:
            downloaded = files[0]

        logger.info(f"Downloaded: {downloaded.name} ({downloaded.stat().st_size} bytes)")
        return downloaded

    async def cancel(self) -> None:
        self._cancelled = True
        if self._process and self._process.returncode is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
