import time
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message

from config.settings import Config
from database.mongo import db
from plugins.fileshare.link import LinkBuilder
from plugins.uploader.telegram import TelegramUploader
from services.telegram_service import TelegramService as TG
from utils.helpers import get_temp_path
from utils.logger import setup_logger
from utils.parser import build_filename, detect_season

logger = setup_logger("upload_handler")


@Client.on_message(filters.document | filters.video)
async def file_upload_handler(client: Client, message: Message):
    user = message.from_user
    if user.id != Config.OWNER_ID:
        await message.reply_text("Unauthorized.")
        return

    doc = message.document or message.video
    if not doc:
        return

    reply = await message.reply_text("Downloading file...")

    tmp = get_temp_path()
    await client.download_media(message, file_name=str(tmp))

    await reply.edit_text("Renaming file...")

    season, _ = detect_season("")
    english_title = doc.file_name or "Unknown"
    quality = ""
    new_name = build_filename(season, "0", english_title, quality, Config.FILE_SUFFIX_TAG)
    new_path = tmp.with_name(new_name)
    tmp.rename(new_path)
    tmp = new_path

    await reply.edit_text("Uploading to DB Channel...")
    tg = TG()
    tg.client = client
    uploader = TelegramUploader(tg)

    try:
        result = await uploader.upload(tmp)
        link = LinkBuilder.build_share_link(
            bot_username=(await client.get_me()).username,
            message_id=result.message_id,
            channel_id=Config.DB_CHANNEL_ID,
        )

        db.files.insert_one({
            "release_hash": "",
            "message_id": result.message_id,
            "channel_id": Config.DB_CHANNEL_ID,
            "telegram_file_id": result.telegram_file_id,
            "file_name": result.file_name,
            "file_size": result.file_size,
            "mime_type": result.mime_type,
            "encoded_link": "",
            "access_count": 0,
            "uploaded_at": time.time(),
        })

        await reply.edit_text(f"✅ Uploaded!\n\n📥 {link}")
    except Exception as e:
        await reply.edit_text(f"❌ Failed: {e}")
        logger.error(f"Upload error: {e}")
    finally:
        tmp.unlink(missing_ok=True)
