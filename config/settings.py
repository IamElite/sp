import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))

    DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", 0))
    TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
    if TARGET_CHAT_ID:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)

    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "subsplease_bot")

    ENCODING_ENABLED = os.getenv("ENCODING_ENABLED", "false").lower() == "true"
    AUTO_POST = os.getenv("AUTO_POST", "false").lower() == "true"

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://subsplease.org/rss/")
    API_BASE_URL = "https://subsplease.org/api/"
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))

    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/tmp/downloads")
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 2))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 2 * 1024 * 1024 * 1024))

    JIKAN_API = "https://api.jikan.moe/v4"
    ANILIST_API = "https://graphql.anilist.co"

    FILE_SUFFIX_TAG = os.getenv("FILE_SUFFIX_TAG", "@SyntaxRealm")

    UPSTREAM_REPO = os.getenv("UPSTREAM_REPO", "https://github.com/IamElite/sp")
    UPSTREAM_BRANCH = os.getenv("UPSTREAM_BRANCH", "main")

    ENCODE_QUALITY = os.getenv("ENCODE_QUALITY", "auto")

    PORT = int(os.getenv("PORT", 8080))
