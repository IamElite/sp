from typing import Optional

import httpx

from config.settings import Config
from plugins.metadata.base import BaseMetadataProvider
from utils.logger import setup_logger

logger = setup_logger("anilist_provider")

_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    id
    title { romaji english native }
    description(asHtml: false)
    genres
    averageScore
    season
    seasonYear
    episodes
    status
    coverImage { large }
    siteUrl
  }
}
"""


class AniListProvider(BaseMetadataProvider):
    def __init__(self):
        self._http = httpx.Client(timeout=15)

    def search(self, title: str) -> Optional[dict]:
        try:
            resp = self._http.post(
                Config.ANILIST_API,
                json={"query": _QUERY, "variables": {"search": title}},
            )
            if resp.status_code != 200:
                return None
            media = resp.json().get("data", {}).get("Media")
            if not media:
                return None
            return self._extract(media)
        except Exception as e:
            logger.warning(f"AniList search '{title}' failed: {e}")
            return None

    def get_details(self, source_id: str) -> Optional[dict]:
        query = """
        query ($id: Int) {
          Media(id: $id, type: ANIME) {
            id
            title { romaji english native }
            description(asHtml: false)
            genres
            averageScore
            season
            seasonYear
            episodes
            status
            coverImage { large }
            siteUrl
          }
        }
        """
        try:
            resp = self._http.post(
                Config.ANILIST_API,
                json={"query": query, "variables": {"id": int(source_id)}},
            )
            if resp.status_code != 200:
                return None
            media = resp.json().get("data", {}).get("Media")
            if not media:
                return None
            return self._extract(media)
        except Exception as e:
            logger.warning(f"AniList details {source_id} failed: {e}")
            return None

    def _extract(self, media: dict) -> dict:
        t = media.get("title", {})
        alt = []
        for val in [t.get("english"), t.get("native")]:
            if val and val != t.get("romaji"):
                alt.append(val)
        return {
            "source": "anilist",
            "source_id": media.get("id"),
            "title": t.get("romaji"),
            "alternate_titles": alt,
            "synopsis": media.get("description"),
            "genres": media.get("genres", []),
            "rating": (
                media.get("averageScore", 0) / 10
                if media.get("averageScore") else None
            ),
            "season": f"{media.get('season', '')}-{media.get('seasonYear', '')}",
            "episodes": media.get("episodes"),
            "status": media.get("status"),
            "poster_url": media.get("coverImage", {}).get("large"),
            "url": media.get("siteUrl"),
        }
