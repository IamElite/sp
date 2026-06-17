import re
from datetime import date, datetime, timezone

from config.settings import Config
from database.mongo import db
from plugins.metadata.enrich import MetadataEnricher
from plugins.release_tracker.api_poller import ApiPoller

TIME_BLOCKS = [
    (0, 5, "\U0001f305 Late Night / Morning"),
    (6, 11, "\u2600\ufe0f Day"),
    (12, 17, "\u2601\ufe0f Afternoon"),
    (18, 23, "\U0001f306 Night"),
]

DAYS_EMOJI = {
    "Monday": "\U0001f5d3",
    "Tuesday": "\U0001f5d3",
    "Wednesday": "\U0001f5d3",
    "Thursday": "\U0001f5d3",
    "Friday": "\U0001f5d3",
    "Saturday": "\U0001f5d3",
    "Sunday": "\U0001f5d3",
}


def _categorize_time(time_str: str) -> tuple[int, str]:
    hr = int(time_str.split(":")[0])
    for start, end, label in TIME_BLOCKS:
        if start <= hr <= end:
            return hr, label
    return hr, "\U0001f306 Night"


def _get_english_title(page: str, romaji_title: str) -> str:
    cached = db.title_cache.find_one({"page": page})
    if cached and cached.get("english"):
        return cached["english"]

    enricher = MetadataEnricher()
    meta = enricher.fetch(romaji_title)
    english = romaji_title
    if meta:
        english = (
            meta.get("title_english")
            or meta.get("alternate_titles", {}).get("english")
            or romaji_title
        )

    db.title_cache.update_one(
        {"page": page},
        {"$set": {"page": page, "english": english, "romaji": romaji_title, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return english


def fetch_schedule() -> dict | None:
    poller = ApiPoller()
    return poller.poll_schedule()


def build_schedule_text(day_data: list[dict], day_name: str) -> str:
    today = date.today()
    lines = []
    lines.append(f"\U0001f5d3 Today's Schedule [IST] \u2014 {day_name} ({today.strftime('%b %d')})")
    lines.append("")

    blocks: dict[str, list[tuple[str, str]]] = {}
    for entry in day_data:
        title_eng = _get_english_title(entry["page"], entry["title"])
        _, block_label = _categorize_time(entry["time"])
        if block_label not in blocks:
            blocks[block_label] = []
        blocks[block_label].append((entry["time"], title_eng))

    for block_label, items in blocks.items():
        lines.append(block_label)
        for t, name in items:
            lines.append(f"\U0001f550 {t}  \u2014 {name}")
        lines.append("")

    lines.append("Powered by @SyntaxRealm")
    return "\n".join(lines)


async def post_schedule(client, target_chat_id: int) -> bool:
    data = fetch_schedule()
    if not data or "schedule" not in data:
        return False

    today_name = date.today().strftime("%A")
    day_data = data["schedule"].get(today_name, [])
    if not day_data:
        return False

    text = build_schedule_text(day_data, today_name)
    today_str = date.today().isoformat()

    prev = db.schedule_meta.find_one({"type": "daily"})
    prev_msg_id = prev.get("message_id") if prev else None

    msg = await client.send_message(chat_id=target_chat_id, text=text)

    try:
        await client.pin_chat_message(chat_id=target_chat_id, message_id=msg.id)
    except Exception:
        pass

    if prev_msg_id:
        try:
            await client.unpin_chat_message(chat_id=target_chat_id, message_id=prev_msg_id)
        except Exception:
            pass

    db.schedule_meta.update_one(
        {"type": "daily"},
        {"$set": {"type": "daily", "date": today_str, "message_id": msg.id, "posted_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return True
