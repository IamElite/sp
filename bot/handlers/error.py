from pyrogram import Client
from pyrogram.handlers import ErrorHandler

from utils.logger import setup_logger

logger = setup_logger("error_handler")


async def global_error_handler(client: Client, update, users, chats):
    logger.error(f"Unhandled update error")


def register_error_handler(client: Client):
    client.add_handler(ErrorHandler(global_error_handler))
