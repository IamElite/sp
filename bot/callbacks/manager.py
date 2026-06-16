from pyrogram import Client
from pyrogram.types import CallbackQuery

from database.mongo import db
from utils.logger import setup_logger

logger = setup_logger("callback_manager")


@Client.on_callback_query()
async def callback_router(client: Client, query: CallbackQuery):
    data = query.data
    if data.startswith("dl:"):
        await handle_quality_callback(client, query)
    else:
        await query.answer("Unknown action", show_alert=True)


async def handle_quality_callback(client: Client, query: CallbackQuery):
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer("Invalid request", show_alert=True)
        return

    action = parts[1]
    group_id = parts[2]

    pending = db.pending_posts.find_one({"group_id": group_id})
    if not pending:
        await query.answer("Link expired", show_alert=True)
        return

    qualities = pending.get("qualities", [])

    if action == "all":
        lines = []
        for q in qualities:
            lines.append(f"📥 {q['quality']}: {q['link']}")
        text = "\n\n".join(lines)
        await query.answer("Sending all links...")
        await query.message.reply_text(text)
        return

    for q in qualities:
        if q["quality"] == action:
            await query.answer(f"Sending {action} link...")
            await query.message.reply_text(f"📥 {action}: {q['link']}")
            return

    await query.answer("Quality not available", show_alert=True)
