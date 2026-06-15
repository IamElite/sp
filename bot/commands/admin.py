from pyrogram import Client, filters
from pyrogram.types import Message

from config.settings import Config
from utils.logger import setup_logger
from utils.queue_manager import QueueManager

logger = setup_logger("admin_commands")


@Client.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def stats_command(client: Client, message: Message):
    qm = QueueManager()
    stats = qm.get_stats()
    text = (
        "**📊 Bot Stats**\n\n"
        f"Total Jobs: {stats['total']}\n"
        f"Pending: {stats['pending']}\n"
        f"Running: {stats['running']}\n"
        f"Done: {stats['done']}\n"
        f"Failed: {stats['failed']}"
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
