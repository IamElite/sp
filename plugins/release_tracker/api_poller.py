from typing import Optional

import httpx

from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger("api_poller")


class ApiPoller:
    def __init__(self):
        self._http = httpx.Client(timeout=30)

    def poll_latest(self, page: int = 1) -> Optional[dict]:
        try:
            resp = self._http.get(
                Config.API_BASE_URL,
                params={"f": "latest", "tz": "Asia/Tokyo", "p": page},
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"API poll failed: {e}")
        return None

    def poll_schedule(self) -> Optional[dict]:
        try:
            resp = self._http.get(
                Config.API_BASE_URL,
                params={"f": "schedule", "tz": "Asia/Tokyo"},
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Schedule poll failed: {e}")
        return None

    def search(self, query: str) -> Optional[dict]:
        try:
            resp = self._http.get(
                Config.API_BASE_URL,
                params={"f": "search", "tz": "Asia/Tokyo", "s": query},
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"API search '{query}' failed: {e}")
        return None
