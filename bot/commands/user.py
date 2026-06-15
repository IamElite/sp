from pyrogram import Client, filters
from pyrogram.types import Message

from config.settings import Config


@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    text = (
        "**How to use:**\n\n"
        "📥 **Download Files**\n"
        "Click any share link to get the file instantly.\n\n"
        "🔗 **Share Links**\n"
        "Links look like:\n"
        f"`t.me/{Config.BOT_TOKEN.split(':')[0]}?start=...`\n\n"
        "For support, contact the owner."
    )
    if Config.BOT_TOKEN:
        text = text.replace(f"`t.me/{Config.BOT_TOKEN.split(':')[0]}?start=...`",
                            "`t.me/BotUsername?start=...`")
    await message.reply_text(text)


@Client.on_message(filters.command("about"))
async def about_command(client: Client, message: Message):
    text = (
        "**🤖 SubsPlease Automation**\n\n"
        "Automated anime release tracking and file sharing system.\n"
        "Tracks SubsPlease releases and provides permanent share links."
    )
    await message.reply_text(text)
