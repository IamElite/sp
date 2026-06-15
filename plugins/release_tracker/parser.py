import re
from typing import Optional

from utils.parser import ParsedRelease, parse_filename


def parse_rss_item(item: dict) -> Optional[ParsedRelease]:
    title = item.get("title", "")
    return parse_filename(title)


def parse_api_entry(key: str, entry: dict) -> Optional[ParsedRelease]:
    show = entry.get("show", "")
    episode = entry.get("episode", "")
    quality = extract_quality_from_entry(entry)
    if not quality:
        quality = ""

    is_batch = "-" in episode
    filename_like = f"[SubsPlease] {show} - {episode} ({quality}p)"
    return ParsedRelease(
        title=show,
        episode=episode,
        quality=quality,
        crc=None,
        is_batch=is_batch,
        raw_title=filename_like,
    )


def extract_quality_from_entry(entry: dict) -> str:
    downloads = entry.get("downloads", [])
    if downloads:
        res = downloads[0].get("res", "")
        return res
    return ""


def extract_info_hash(guid: str) -> str:
    guid = guid.strip()
    if guid.startswith("btih:"):
        return guid
    return f"btih:{guid}"


def extract_magnet(item: dict) -> Optional[str]:
    link = item.get("link", "")
    if link.startswith("magnet:?"):
        return link
    return None


def is_subsplease_release(item: dict) -> bool:
    title = item.get("title", "")
    return "[SubsPlease]" in title
