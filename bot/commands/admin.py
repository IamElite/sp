import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message

from config.settings import Config
from database.mongo import db
from utils.logger import setup_logger
from utils.queue_manager import QueueManager

logger = setup_logger("admin_commands")


@Client.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def stats_command(client: Client, message: Message):
    qm = QueueManager()
    stats = qm.get_stats()
    total_users = db.users.count_documents({})
    text = (
        "**📊 Bot Stats**\n\n"
        f"Total Jobs: {stats['total']}\n"
        f"Pending: {stats['pending']}\n"
        f"Running: {stats['running']}\n"
        f"Done: {stats['done']}\n"
        f"Failed: {stats['failed']}\n"
        f"Users: {total_users}"
    )
    await message.reply_text(text)


@Client.on_message(filters.command("retry") & filters.user(Config.OWNER_ID))
async def retry_command(client: Client, message: Message):
    qm = QueueManager()
    count = qm.retry_failed()
    await message.reply_text(f"Re-queued {count} failed jobs.")


@Client.on_message(filters.command("log") & filters.user(Config.OWNER_ID))
async def log_command(client: Client, message: Message):
    await message.reply_document("bot.log")


@Client.on_message(filters.command("clean") & filters.user(Config.OWNER_ID))
async def clean_command(client: Client, message: Message):
    msg = await message.reply_text("Cleaning database...")

    qm = QueueManager()
    jobs = qm.cleanup_old_jobs()

    orphan_files = 0
    orphan_ids = []
    for f in db.files.find({"release_hash": ""}, {"_id": 1}):
        orphan_ids.append(f["_id"])
    if orphan_ids:
        result = db.files.delete_many({"_id": {"$in": orphan_ids}})
        orphan_files = result.deleted_count

    release_fields = db.releases.update_many(
        {"processed": True},
        {"$unset": {"file_name": "", "magnet_uri": ""}},
    )
    meta_fields = db.releases.update_many(
        {"processed": True, "metadata": {"$exists": True}},
        {"$unset": {
            "metadata.synopsis": "",
            "metadata.genres": "",
            "metadata.poster_url": "",
            "metadata.rating": "",
            "metadata.season": "",
            "metadata.episodes": "",
            "metadata.status": "",
            "metadata.url": "",
            "metadata.source": "",
            "metadata.source_id": "",
            "metadata.alternate_titles": "",
        }},
    )

    parts = []
    if jobs:
        parts.append(f"Jobs: {jobs}")
    if orphan_files:
        parts.append(f"Orphan files: {orphan_files}")
    if release_fields.modified_count:
        parts.append(f"Releases cleaned: {release_fields.modified_count}")
    if meta_fields.modified_count:
        parts.append(f"Metadata stripped: {meta_fields.modified_count}")

    text = "✅ DB Cleaned\n" + "\n".join(parts) if parts else "Nothing to clean."
    await msg.edit_text(text)


@Client.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast_command(client: Client, message: Message):
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return

    broadcast_msg = text[1]
    users = db.users.find({}, {"_id": 1})
    sent = 0
    failed = 0

    for user in users:
        try:
            await client.send_message(chat_id=user["_id"], text=broadcast_msg)
            await asyncio.sleep(0.05)
            sent += 1
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast to {user['_id']} failed: {e}")

    await message.reply_text(
        f"Broadcast done.\nSent: {sent}\nFailed: {failed}"
    )


@Client.on_message(filters.command("schedule") & filters.user(Config.OWNER_ID))
async def schedule_command(client: Client, message: Message):
    if not Config.TARGET_CHAT_ID:
        await message.reply_text("TARGET_CHAT_ID not set.")
        return

    from services.schedule_service import post_schedule

    ok = await post_schedule(client, Config.TARGET_CHAT_ID)
    if ok:
        await message.reply_text("Schedule posted + pinned.")
    else:
        await message.reply_text("Failed to fetch schedule.")
