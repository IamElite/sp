import asyncio
from pathlib import Path

from config.settings import Config
from plugins.encoder.manager import EncodeJob
from utils.logger import setup_logger

logger = setup_logger("encode_queue")


class EncodeQueue:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()

    async def add(self, input_path: Path, quality: str = "1080"):
        await self._queue.put((input_path, quality))
        logger.info(f"Encode queued: {input_path.name} ({quality}p)")

    async def process_all(self) -> list[Path]:
        results = []
        while not self._queue.empty():
            input_path, quality = await self._queue.get()
            if not Config.ENCODING_ENABLED:
                results.append(input_path)
                continue

            job = EncodeJob(input_path, quality)
            try:
                output = await job.run()
                results.append(output)
            except Exception as e:
                logger.error(f"Encode job failed: {e}")
                results.append(input_path)

        return results
