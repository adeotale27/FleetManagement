from pymongo import ReturnDocument
from app.repositories.base import utcnow


class SequenceService:
    def __init__(self, db):
        self.col = db["sequences"]

    async def next(self, tenant_id: str, key: str, prefix: str) -> str:
        doc = await self.col.find_one_and_update(
            {"tenant_id": tenant_id, "key": key},
            {"$inc": {"value": 1}, "$setOnInsert": {"tenant_id": tenant_id, "key": key, "created_at": utcnow()}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return f"{prefix}-{int(doc['value']):06d}"
