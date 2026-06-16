import asyncio
import re
import time
from pathlib import Path

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import Config
from database.mongo import db
from database.models.release import ReleaseModel
from database.models.file import FileModel
from plugins.downloader.magnet import MagnetDownloader
from plugins.encoder.manager import EncodeJob
from plugins.encoder.presets import resolve_quality_key
from plugins.fileshare.link import LinkBuilder
from plugins.metadata.enrich import MetadataEnricher
from plugins.release_tracker.rss_poller import RSSPoller
from plugins.release_tracker.parser import (
    parse_rss_item,
    extract_info_hash,
    extract_magnet,
)
from plugins.uploader.telegram import TelegramUploader
from services.release_service import ReleaseService
from services.telegram_service import TelegramService
from services.metadata_service import get_english_title
from utils.helpers import cleanup_file, ensure_download_dir, format_size
from utils.parser import build_filename, detect_season
from utils.logger import setup_logger
from utils.queue_manager import QueueManager

logger = setup_logger("worker")

QUALITY_ORDER = ["480p", "720p", "1080p", "HDRip"]


def _get_group_id(title: str, episode: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{slug}-{episode}"


def _build_caption(pending: dict) -> str:
    qualities = pending.get("qualities", [])
    quality_list = " • ".join(q["quality"] for q in qualities)
    return (
        f'<blockquote><b>➲ {pending["anime_name"]}</b></blockquote>\n'
        f'╭──────────────\n'
        f'◈ Season   : {pending["season"]}\n'
        f'◈ Episodes : {pending["episode"]} [ #NEW ]\n'
        f'◈ Audio    : Jap Dub [ #ESUB ]\n'
        f'◈ Quality  : {quality_list}\n'
        f'◈ Genre    : {pending["genre"]}\n'
        f'╰──────────────\n'
        f'<blockquote>❖ 𝐌ᴧᴅє 𝐁ɣ ➛ ˹ SyntaxRealm.t.me ˼</b></blockquote>'
    )


def _build_buttons(pending: dict) -> InlineKeyboardMarkup:
    qualities = pending.get("qualities", [])
    uploaded = {q["quality"] for q in qualities}
    buttons = []
    row = []
    for label in QUALITY_ORDER:
        if label in uploaded:
            row.append(InlineKeyboardButton(label, callback_data=f"dl:{label}:{pending['group_id']}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    if len(uploaded) >= 4:
        buttons.append([InlineKeyboardButton("Get All", callback_data=f"dl:all:{pending['group_id']}")])
    return InlineKeyboardMarkup(buttons)


class Worker:
    def __init__(self):
        self.tg = TelegramService()
        self.queue = QueueManager()
        self.release_svc = ReleaseService()
        self.poller = RSSPoller()
        self.enricher = MetadataEnricher()
        self.downloader = MagnetDownloader()
        self.running = True

    async def start(self):
        await self.tg.start()
        logger.info("Worker started")

    async def stop(self):
        self.running = False
        await self.tg.stop()
        logger.info("Worker stopped")

    async def poll_releases(self):
        items = self.poller.poll()
        for item in items:
            parsed = parse_rss_item(item)
            if not parsed:
                continue

            release_id = extract_info_hash(item.get("guid", ""))
            if self.release_svc.is_new(release_id):
                if parsed.is_batch:
                    logger.info(f"Skipping batch: {parsed.raw_title}")
                    continue

                magnet = extract_magnet(item)
                release = ReleaseModel(
                    release_id=release_id,
                    title=parsed.title,
                    episode=parsed.episode,
                    quality=parsed.quality,
                    release_date=item.get("pub_date"),
                    file_name=parsed.raw_title,
                    magnet_uri=magnet,
                    is_batch=False,
                )

                meta = self.enricher.fetch(parsed.title)
                if meta:
                    release.metadata = meta

                self.release_svc.save_release(release)

                self.queue.enqueue("download", {
                    "release_hash": release_id,
                    "magnet_uri": magnet,
                    "quality": parsed.quality,
                    "file_name": parsed.raw_title,
                })
                logger.info(f"Queued download: {parsed.title} - {parsed.episode}")

    async def process_queue(self):
        job = self.queue.dequeue()
        if not job:
            return

        try:
            if job.type == "download":
                await self._process_download(job)
            elif job.type == "encode":
                await self._process_encode(job)
            elif job.type == "upload":
                await self._process_upload(job)
            elif job.type == "post":
                await self._process_post(job)
        except Exception as e:
            self.queue.update_status(job._id, "failed", str(e))
            logger.error(f"Job {job._id} failed: {e}")

    async def _process_download(self, job):
        self.queue.update_progress(job._id, 10)
        ensure_download_dir()

        magnet = job.payload.get("magnet_uri")
        if not magnet:
            raise ValueError("No magnet URI in job payload")

        file_path = await self.downloader.download(magnet)
        self.queue.update_progress(job._id, 100)

        rss_quality = job.payload.get("quality", "1080")

        if Config.ENCODING_ENABLED:
            if rss_quality == "1080" and Config.ENCODE_QUALITY == "auto":
                self.queue.enqueue("encode", {
                    "release_hash": job.payload["release_hash"],
                    "file_path": str(file_path),
                    "quality": "1080",
                })
                self.queue.enqueue("encode", {
                    "release_hash": job.payload["release_hash"],
                    "file_path": str(file_path),
                    "quality": "hdrip",
                })
            else:
                quality = resolve_quality_key(rss_quality, Config.ENCODE_QUALITY)
                self.queue.enqueue("encode", {
                    "release_hash": job.payload["release_hash"],
                    "file_path": str(file_path),
                    "quality": quality,
                })
        else:
            cleanup_file(file_path)
            logger.info(f"Skipped upload (encoding disabled): {file_path.name}")

        self.queue.update_status(job._id, "done")
        self.release_svc.mark_processed(job.payload["release_hash"])

    async def _process_encode(self, job):
        file_path = Path(job.payload["file_path"])
        quality = job.payload["quality"]
        enc = EncodeJob(file_path, quality)
        output = await enc.run()

        self.queue.update_progress(job._id, 100)

        self.queue.enqueue("upload", {
            "release_hash": job.payload["release_hash"],
            "file_path": str(output),
            "quality": quality,
        })
        self.queue.update_status(job._id, "done")

    async def _process_upload(self, job):
        file_path = Path(job.payload["file_path"])
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        quality = job.payload.get("quality", "")
        release_hash = job.payload.get("release_hash", "")
        release = db.releases.find_one({"_id": release_hash}) if release_hash else None

        if release:
            season, _ = detect_season(release["title"])
            meta = release.get("metadata") or {}
            english_title = get_english_title(meta) or release["title"]
            tag = Config.FILE_SUFFIX_TAG
            new_name = build_filename(season, release["episode"], english_title, quality, tag)
            new_path = file_path.with_name(new_name)
            file_path.rename(new_path)
            file_path = new_path

        uploader = TelegramUploader(self.tg)
        result = await uploader.upload(file_path)

        bot_info = await self.tg.client.get_me()
        link = LinkBuilder.build_share_link(
            bot_username=bot_info.username,
            message_id=result.message_id,
            channel_id=Config.DB_CHANNEL_ID,
        )

        file_record = FileModel(
            release_hash=release_hash,
            message_id=result.message_id,
            channel_id=Config.DB_CHANNEL_ID,
            telegram_file_id=result.telegram_file_id,
            file_name=result.file_name,
            file_size=result.file_size,
            mime_type=result.mime_type,
            encoded_link=link,
        )
        db.files.insert_one(file_record.to_dict())

        cleanup_file(file_path)
        self.queue.update_progress(job._id, 100)

        if release:
            meta = release.get("metadata") or {}
            season, _ = detect_season(release["title"])
            group_id = _get_group_id(release["title"], release["episode"])

            quality_label = f"{quality}p" if quality and not quality.endswith("p") else quality
            if quality == "hdrip":
                quality_label = "HDRip"

            db.pending_posts.update_one(
                {"group_id": group_id},
                {
                    "$setOnInsert": {
                        "group_id": group_id,
                        "anime_name": get_english_title(meta) or release["title"],
                        "season": f"S{season:02d}",
                        "episode": release["episode"],
                        "genre": ", ".join(meta.get("genres", [])) or "N/A",
                        "poster_url": meta.get("poster_url", ""),
                        "all_done": False,
                        "post_message_id": None,
                    },
                    "$push": {
                        "qualities": {
                            "quality": quality_label,
                            "link": link,
                            "release_hash": release_hash,
                        }
                    },
                },
                upsert=True,
            )

            if Config.AUTO_POST and Config.TARGET_CHAT_ID:
                self.queue.enqueue("post", {
                    "group_id": group_id,
                    "target_chat_id": Config.TARGET_CHAT_ID,
                })

        self.queue.update_status(job._id, "done")
        logger.info(f"Upload complete: {link}")

    async def _process_post(self, job):
        group_id = job.payload["group_id"]
        target = job.payload["target_chat_id"]

        pending = db.pending_posts.find_one({"group_id": group_id})
        if not pending:
            logger.warning(f"No pending post for group {group_id}")
            self.queue.update_status(job._id, "done")
            return

        caption = _build_caption(pending)
        reply_markup = _build_buttons(pending)
        poster_url = pending.get("poster_url", "")
        msg_id = pending.get("post_message_id")

        try:
            if msg_id:
                await self.tg.client.edit_message_caption(
                    chat_id=target,
                    message_id=msg_id,
                    caption=caption,
                    parse_mode="html",
                )
                await self.tg.client.edit_message_reply_markup(
                    chat_id=target,
                    message_id=msg_id,
                    reply_markup=reply_markup,
                )
            elif poster_url:
                msg = await self.tg.client.send_photo(
                    chat_id=target,
                    photo=poster_url,
                    caption=caption,
                    parse_mode="html",
                    reply_markup=reply_markup,
                )
                db.pending_posts.update_one(
                    {"group_id": group_id},
                    {"$set": {"post_message_id": msg.id}},
                )
            else:
                msg = await self.tg.client.send_message(
                    chat_id=target,
                    text=caption,
                    parse_mode="html",
                    reply_markup=reply_markup,
                )
                db.pending_posts.update_one(
                    {"group_id": group_id},
                    {"$set": {"post_message_id": msg.id}},
                )
        except Exception as e:
            logger.error(f"Post to target failed: {e}")

        self.queue.update_status(job._id, "done")

    async def run_cycle(self):
        await self.poll_releases()
        await self.process_queue()

    async def worker_loop(self):
        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Worker cycle error: {e}")
            await asyncio.sleep(Config.POLL_INTERVAL)
