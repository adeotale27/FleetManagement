from datetime import datetime, timezone
from typing import Any
from bson import ObjectId
from pymongo import ReturnDocument


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def oid() -> str:
    return str(ObjectId())


def serialize(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if not doc:
        return None
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    return out


class TenantRepository:
    def __init__(self, db, collection: str):
        self.col = db[collection]
        self.collection = collection

    def _scope(self, tenant_id: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        query: dict[str, Any] = {"tenant_id": tenant_id, "is_deleted": {"$ne": True}}
        if extra:
            query.update(extra)
        return query

    async def insert(self, tenant_id: str, data: dict[str, Any], user_id: str | None) -> dict[str, Any]:
        doc = {
            "_id": data.get("_id") or oid(),
            "tenant_id": tenant_id,
            "created_at": utcnow(),
            "updated_at": utcnow(),
            "created_by": user_id,
            "updated_by": user_id,
            "is_deleted": False,
            **{k: v for k, v in data.items() if k != "_id"},
        }
        await self.col.insert_one(doc)
        return serialize(doc)  # type: ignore[return-value]

    async def get(self, tenant_id: str, item_id: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one(self._scope(tenant_id, {"_id": item_id})))

    async def find_one(self, tenant_id: str, extra: dict[str, Any]) -> dict[str, Any] | None:
        return serialize(await self.col.find_one(self._scope(tenant_id, extra)))

    async def list(
        self,
        tenant_id: str,
        filters: dict[str, Any] | None = None,
        search_fields: list[str] | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
        sort: list[tuple[str, int]] | None = None,
    ) -> dict[str, Any]:
        query = self._scope(tenant_id, filters)
        if search and search_fields:
            query["$or"] = [
                {field: {"$regex": search, "$options": "i"}} for field in search_fields
            ]
        total = await self.col.count_documents(query)
        cursor = self.col.find(query).sort(sort or [("updated_at", -1)])
        skip = max(page - 1, 0) * limit
        items = [serialize(d) for d in await cursor.skip(skip).limit(limit).to_list(length=limit)]
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": skip + limit < total,
        }

    async def update(self, tenant_id: str, item_id: str, data: dict[str, Any], user_id: str | None) -> dict[str, Any] | None:
        payload = {k: v for k, v in data.items() if v is not None and k not in {"id", "tenant_id", "_id"}}
        payload["updated_at"] = utcnow()
        payload["updated_by"] = user_id
        doc = await self.col.find_one_and_update(
            self._scope(tenant_id, {"_id": item_id}),
            {"$set": payload},
            return_document=ReturnDocument.AFTER,
        )
        return serialize(doc)

    async def soft_delete(self, tenant_id: str, item_id: str, user_id: str | None) -> bool:
        result = await self.col.update_one(
            self._scope(tenant_id, {"_id": item_id}),
            {"$set": {"is_deleted": True, "deleted_at": utcnow(), "deleted_by": user_id, "status": "inactive"}},
        )
        return result.modified_count == 1


class GlobalRepository:
    def __init__(self, db, collection: str):
        self.col = db[collection]

    async def insert(self, data: dict[str, Any]) -> dict[str, Any]:
        doc = {"_id": data.get("_id") or oid(), "created_at": utcnow(), "updated_at": utcnow(), **data}
        await self.col.insert_one(doc)
        return serialize(doc)  # type: ignore[return-value]

    async def get(self, item_id: str) -> dict[str, Any] | None:
        return serialize(await self.col.find_one({"_id": item_id, "is_deleted": {"$ne": True}}))

    async def find_one(self, extra: dict[str, Any]) -> dict[str, Any] | None:
        query = {"is_deleted": {"$ne": True}, **extra}
        return serialize(await self.col.find_one(query))

    async def list(self, filters: dict[str, Any] | None = None, page: int = 1, limit: int = 20) -> dict[str, Any]:
        query = {"is_deleted": {"$ne": True}, **(filters or {})}
        total = await self.col.count_documents(query)
        items = [
            serialize(d)
            for d in await self.col.find(query)
            .sort("updated_at", -1)
            .skip(max(page - 1, 0) * limit)
            .limit(limit)
            .to_list(length=limit)
        ]
        return {"items": items, "total": total, "page": page, "limit": limit, "has_next": (page * limit) < total}

    async def update(self, item_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        payload = {**data, "updated_at": utcnow()}
        doc = await self.col.find_one_and_update(
            {"_id": item_id},
            {"$set": payload},
            return_document=ReturnDocument.AFTER,
        )
        return serialize(doc)
