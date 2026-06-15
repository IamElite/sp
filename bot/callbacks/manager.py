from pyrogram import Client
from pyrogram.types import CallbackQuery


@Client.on_callback_query()
async def callback_router(client: Client, query: CallbackQuery):
    data = query.data
    if data.startswith("dl_"):
        await handle_download_callback(client, query)
    elif data.startswith("info_"):
        await handle_info_callback(client, query)
    else:
        await query.answer("Unknown action", show_alert=True)


async def handle_download_callback(client: Client, query: CallbackQuery):
    await query.answer("Preparing download...")
    await query.message.reply_text("Use the share link to download.")


async def handle_info_callback(client: Client, query: CallbackQuery):
    await query.answer("Info", show_alert=True)
