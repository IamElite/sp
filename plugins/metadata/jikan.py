from typing import Optional

import httpx

from config.settings import Config
from plugins.metadata.base import BaseMetadataProvider
from utils.logger import setup_logger

logger = setup_logger("jikan_provider")


class JikanProvider(BaseMetadataProvider):
    def __init__(self):
        self._http = httpx.Client(timeout=15)

    def search(self, title: str) -> Optional[dict]:
        try:
            resp = self._http.get(
                f"{Config.JIKAN_API}/anime",
                params={"q": title, "limit": 1},
            )
            if resp.status_code != 200:
                return None
            data = resp.json().get("data", [])
            if not data:
                return None
            return self._extract(data[0])
        except Exception as e:
            logger.warning(f"Jikan search '{title}' failed: {e}")
            return None

    def get_details(self, source_id: str) -> Optional[dict]:
        try:
            resp = self._http.get(f"{Config.JIKAN_API}/anime/{source_id}")
            if resp.status_code != 200:
                return None
            return self._extract(resp.json().get("data", {}))
        except Exception as e:
            logger.warning(f"Jikan details {source_id} failed: {e}")
            return None

    def _extract(self, anime: dict) -> dict:
        titles = anime.get("titles", [])
        return {
            "source": "jikan",
            "source_id": anime.get("mal_id"),
            "title": anime.get("title"),
            "alternate_titles": [t["title"] for t in titles if t["type"] != "Default"],
            "synopsis": anime.get("synopsis"),
            "genres": [g["name"] for g in anime.get("genres", [])],
            "rating": anime.get("score"),
            "season": f"{anime.get('season', '')}-{anime.get('year', '')}",
            "episodes": anime.get("episodes"),
            "status": anime.get("status"),
            "poster_url": anime.get("images", {}).get("jpg", {}).get("large_image_url"),
            "url": anime.get("url"),
        }
