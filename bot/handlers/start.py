from pyrogram import Client, filters
from pyrogram.types import Message

from config.settings import Config
from database.mongo import db
from plugins.fileshare.forwarder import FileForwarder
from utils.logger import setup_logger

logger = setup_logger("start_handler")


@Client.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user = message.from_user

    db.users.update_one(
        {"_id": user.id},
        {"$set": {"_id": user.id}, "$currentDate": {"last_active": True}},
        upsert=True,
    )

    text = message.text or ""
    param = text.split(maxsplit=1)[-1] if len(text.split()) > 1 else None

    if not param:
        await message.reply_text(
            "Welcome! Send me a file to get a share link, "
            "or click a share link to download."
        )
        return

    forwarder = FileForwarder()
    success = await forwarder.forward_to_user(
        client=client,
        user_id=user.id,
        encoded_param=param,
        db_channel_id=Config.DB_CHANNEL_ID,
    )

    if not success:
        await message.reply_text("Invalid or expired link.")
