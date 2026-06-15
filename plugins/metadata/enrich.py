from typing import Optional

from plugins.metadata.jikan import JikanProvider
from plugins.metadata.anilist import AniListProvider
from utils.logger import setup_logger

logger = setup_logger("metadata_enricher")


class MetadataEnricher:
    def __init__(self):
        self.providers = [JikanProvider(), AniListProvider()]

    def fetch(self, title: str) -> Optional[dict]:
        for provider in self.providers:
            result = provider.search(title)
            if result:
                logger.info(f"Found metadata via {provider.__class__.__name__}: {title}")
                return result
        logger.info(f"No metadata found for: {title}")
        return None

    def fetch_with_fallback(self, titles: list[str]) -> Optional[dict]:
        for t in titles:
            result = self.fetch(t)
            if result:
                return result
        return None
