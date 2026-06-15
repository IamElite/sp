import time
from typing import Optional

import httpx

from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger("metadata_service")

_cache: dict[str, dict] = {}
_CACHE_TTL = 86400


class MetadataService:
    def __init__(self):
        self._http = httpx.Client(timeout=15)

    def fetch_metadata(self, title: str) -> Optional[dict]:
        cache_key = title.lower().strip()
        cached = _cache.get(cache_key)
        if cached and (time.time() - cached["ts"]) < _CACHE_TTL:
            return cached["data"]

        data = self._try_jikan(title)
        if not data:
            data = self._try_anilist(title)

        if data:
            _cache[cache_key] = {"data": data, "ts": time.time()}

        return data

    def _try_jikan(self, title: str) -> Optional[dict]:
        try:
            resp = self._http.get(
                f"{Config.JIKAN_API}/anime",
                params={"q": title, "limit": 1},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            results = data.get("data", [])
            if not results:
                return None

            anime = results[0]
            titles = anime.get("titles", [])
            alt_titles = [t["title"] for t in titles if t["type"] != "Default"]

            return {
                "source": "jikan",
                "source_id": anime.get("mal_id"),
                "title": anime.get("title"),
                "title_english": anime.get("title_english"),
                "alternate_titles": alt_titles,
                "synopsis": anime.get("synopsis"),
                "genres": [g["name"] for g in anime.get("genres", [])],
                "rating": anime.get("score"),
                "season": f"{anime.get('season', '')}-{anime.get('year', '')}",
                "episodes": anime.get("episodes"),
                "status": anime.get("status"),
                "poster_url": (anime.get("images", {}).get("jpg", {}).get("large_image_url")),
                "url": anime.get("url"),
            }
        except Exception as e:
            logger.warning(f"Jikan lookup failed for '{title}': {e}")
            return None

    def _try_anilist(self, title: str) -> Optional[dict]:
        query = """
        query ($search: String) {
            Media(search: $search, type: ANIME) {
                id
                title { romaji english native }
                description
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
                json={"query": query, "variables": {"search": title}},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            media = data.get("data", {}).get("Media")
            if not media:
                return None

            t = media.get("title", {})
            alt_titles = []
            for val in [t.get("english"), t.get("native")]:
                if val and val != t.get("romaji"):
                    alt_titles.append(val)

            return {
                "source": "anilist",
                "source_id": media.get("id"),
                "title": t.get("romaji"),
                "title_english": t.get("english"),
                "alternate_titles": alt_titles,
                "synopsis": media.get("description"),
                "genres": media.get("genres", []),
                "rating": (
                    media.get("averageScore", 0) / 10
                    if media.get("averageScore")
                    else None
                ),
                "season": f"{media.get('season', '')}-{media.get('seasonYear', '')}",
                "episodes": media.get("episodes"),
                "status": media.get("status"),
                "poster_url": (media.get("coverImage", {}).get("large")),
                "url": media.get("siteUrl"),
            }
        except Exception as e:
            logger.warning(f"AniList lookup failed for '{title}': {e}")
            return None

    def enrich_release(self, release_id: str, title: str) -> None:
        from database.mongo import db

        meta = self.fetch_metadata(title)
        if meta:
            db.releases.update_one(
                {"_id": release_id},
                {"$set": {"metadata": meta}},
            )
            logger.info(f"Enriched release {release_id} with metadata")


def get_english_title(metadata: dict) -> str:
    english = metadata.get("title_english") or metadata.get("title", "")
    return english.strip() if english else ""
