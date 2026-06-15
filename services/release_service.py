import time
from typing import Optional

from database.mongo import db
from database.models.release import ReleaseModel
from utils.logger import setup_logger

logger = setup_logger("release_service")


class ReleaseService:
    def is_new(self, release_id: str) -> bool:
        return db.releases.find_one({"_id": release_id}) is None

    def save_release(self, release: ReleaseModel) -> None:
        release.processed = False
        release.updated_at = time.time()
        db.releases.update_one(
            {"_id": release._id},
            {"$set": release.to_dict()},
            upsert=True,
        )

    def mark_processed(self, release_id: str) -> None:
        db.releases.update_one(
            {"_id": release_id},
            {"$set": {"processed": True, "updated_at": time.time()}},
        )

    def get_unprocessed(self, limit: int = 10) -> list[ReleaseModel]:
        docs = (
            db.releases.find({"processed": False})
            .sort("release_date", -1)
            .limit(limit)
        )
        return [ReleaseModel.from_dict(d) for d in docs]

    def search(self, query: str, limit: int = 20) -> list[ReleaseModel]:
        docs = (
            db.releases.find(
                {"title": {"$regex": query, "$options": "i"}}
            )
            .sort("release_date", -1)
            .limit(limit)
        )
        return [ReleaseModel.from_dict(d) for d in docs]

    def get_by_id(self, release_id: str) -> Optional[ReleaseModel]:
        doc = db.releases.find_one({"_id": release_id})
        if doc:
            return ReleaseModel.from_dict(doc)
        return None
