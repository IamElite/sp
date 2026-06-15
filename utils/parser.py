import re
from dataclasses import dataclass
from typing import Optional
from plugins.encoder.presets import quality_display


@dataclass
class ParsedRelease:
    title: str
    episode: str
    quality: str
    crc: Optional[str]
    is_batch: bool
    raw_title: str


def parse_filename(filename: str) -> Optional[ParsedRelease]:
    raw = filename.strip()

    # Pattern 1: [SubsPlease] Show Name - XX (RESp) [CRC].mkv  (standard episode)
    m = re.match(
        r"^\[SubsPlease\]\s+(.+?)\s+-\s+(\d+(?:-\d+)?)"
        r"\s+\((\d+)(?:p)?\)\s*(?:\[([A-Fa-f0-9]{8}|Batch)\])?"
        r"(?:\.\w+)?$",
        raw,
    )
    if m:
        return ParsedRelease(
            title=m.group(1).strip(),
            episode=m.group(2),
            quality=m.group(3),
            crc=None if m.group(4) in (None, "Batch") else m.group(4),
            is_batch=(m.group(4) == "Batch" or "-" in m.group(2)),
            raw_title=raw,
        )

    # Pattern 2: [SubsPlease] Show Name (XX-YY) (RESp) [Batch]  (batch = no dash before ep)
    m = re.match(
        r"^\[SubsPlease\]\s+(.+?)\s+\((\d+-\d+)\)"
        r"\s+\((\d+)(?:p)?\)\s*(?:\[([^\]]*)\])?"
        r"(?:\.\w+)?$",
        raw,
    )
    if m:
        return ParsedRelease(
            title=m.group(1).strip(),
            episode=m.group(2),
            quality=m.group(3),
            crc=None,
            is_batch=True,
            raw_title=raw,
        )

    # Pattern 3: [SubsPlease] Show Name - XX (RES) [CRC]  (alt format)
    m = re.match(
        r"^\[SubsPlease\]\s+(.+?)\s+-\s+(\d+(?:-\d+)?)"
        r"\s+\((\d+p)\)\s*\[([^\]]+)\].*$",
        raw,
    )
    if m:
        return ParsedRelease(
            title=m.group(1).strip(),
            episode=m.group(2),
            quality=m.group(3).replace("p", ""),
            crc=None if m.group(4) == "Batch" else m.group(4),
            is_batch=(m.group(4) == "Batch" or "-" in m.group(2)),
            raw_title=raw,
        )

    # Fallback: extract [SubsPlease] prefix, return raw title
    title = raw.replace("[SubsPlease] ", "").strip()
    if not title:
        return None
    return ParsedRelease(
        title=title, episode="", quality="", crc=None, is_batch=False, raw_title=raw,
    )


def clean_title(title: str) -> str:
    title = re.sub(r"\s+S\d+", "", title)
    title = re.sub(r"\s+-\s+.*$", "", title)
    title = re.sub(r"\s+\(\d+p\)", "", title)
    title = re.sub(r"\s+\[.*?\]", "", title)
    return title.strip()


def detect_season(title: str) -> tuple[int, str]:
    m = re.search(r"\s+S(\d+)$", title)
    if m:
        season = int(m.group(1))
        clean = title[: m.start()].strip()
        return season, clean
    return 1, title


def build_filename(
    season: int, episode: str, english_title: str, quality: str, suffix_tag: str
) -> str:
    quality_tag = quality_display(quality)
    return (
        f"[S{season:02d}-E{episode}] {english_title} "
        f"[{quality_tag}] [ESUB] {suffix_tag}.mkv"
    )
