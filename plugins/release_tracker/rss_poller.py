import xml.etree.ElementTree as ET
from typing import Optional

import httpx

from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger("rss_poller")

NS = {"subsplease": "https://subsplease.org/rss"}


class RSSPoller:
    def __init__(self):
        self._http = httpx.Client(timeout=30, follow_redirects=True)
        self._last_guid: Optional[str] = None

    def poll(self) -> list[dict]:
        try:
            resp = self._http.get(Config.RSS_FEED_URL)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"RSS poll failed: {e}")
            return []

        items = self._parse(resp.text)
        return items

    def _parse(self, xml_data: str) -> list[dict]:
        releases = []
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            logger.error(f"RSS parse error: {e}")
            return []

        for item in root.iter("item"):
            guid = item.findtext("guid", "")
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            category = item.findtext("category", "")
            size_el = item.find("subsplease:size", NS)
            size = size_el.text if size_el is not None else ""

            if not guid:
                continue

            releases.append({
                "guid": guid.strip(),
                "title": title.strip(),
                "link": link.strip(),
                "pub_date": pub_date.strip(),
                "category": category.strip(),
                "size": size.strip(),
            })

        if releases:
            self._last_guid = releases[0]["guid"]

        return releases
