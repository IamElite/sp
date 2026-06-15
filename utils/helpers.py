import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from config.settings import Config


def ensure_download_dir() -> Path:
    path = Path(Config.DOWNLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_file(path: Path) -> None:
    try:
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


def get_temp_path(suffix: str = ".mkv") -> Path:
    fd, path = tempfile.mkstemp(suffix=suffix, dir=Config.DOWNLOAD_DIR)
    os.close(fd)
    return Path(path)


def format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def parse_episode_range(episode: str) -> Optional[tuple[int, int]]:
    if "-" in episode:
        parts = episode.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])
    return None


def truncate_text(text: str, max_len: int = 500) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
