from pymongo import MongoClient
from pymongo.collection import Collection
from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger("database")


class Database:
    def __init__(self):
        self._client: MongoClient | None = None
        self._db = None
        self.releases: Collection | None = None
        self.files: Collection | None = None
        self.jobs: Collection | None = None
        self.users: Collection | None = None

    def connect(self):
        logger.info("Connecting to MongoDB...")
        self._client = MongoClient(
            Config.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        self._client.admin.command("ping")
        self._db = self._client[Config.DATABASE_NAME]
        self.releases = self._db["releases"]
        self.files = self._db["files"]
        self.jobs = self._db["jobs"]
        self.users = self._db["users"]
        self._create_indexes()
        logger.info("MongoDB connected")

    def _create_indexes(self):
        self.releases.create_index("processed")
        self.releases.create_index([("release_date", -1)])
        self.files.create_index("encoded_link")
        self.files.create_index([("message_id", 1), ("channel_id", 1)])
        self.users.create_index("_id")
        self.jobs.create_index([("status", 1), ("priority", -1), ("created_at", 1)])
        self.jobs.create_index([("type", 1), ("status", 1)])

    def close(self):
        if self._client:
            self._client.close()

    @property
    def is_connected(self) -> bool:
        try:
            if self._client:
                self._client.admin.command("ping")
                return True
        except Exception:
            return False
        return False


db = Database()
