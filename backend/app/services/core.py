from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.repositories.base import TenantRepository, oid, utcnow

ACTIVE_TRIP_STATUSES = {"new", "assigned", "started", "in_transit"}
TRIP_TRANSITIONS = {
    "draft": {"new", "cancelled"},
    "new": {"assigned", "cancelled"},
    "assigned": {"started", "cancelled"},
    "started": {"in_transit", "cancelled"},
    "in_transit": {"delivered", "cancelled"},
    "delivered": {"completed", "cancelled"},
    "completed": {"closed"},
    "closed": set(),
    "cancelled": set(),
}


def money(value: Any) -> float:
    return float(Decimal(str(value or 0)))


class SequenceService:
    def __init__(self, db):
        self.col = db["sequences"]

    async def next(self, tenant_id: str, key: str, prefix: str) -> str:
        from pymongo import ReturnDocument

        doc = await self.col.find_one_and_update(
            {"tenant_id": tenant_id, "key": key},
            {"$inc": {"value": 1}, "$setOnInsert": {"tenant_id": tenant_id, "key": key}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return f"{prefix}-{int(doc['value']):06d}"


class AuditService:
    def __init__(self, db):
        self.col = db["audit_logs"]

    async def record(
        self,
        *,
        tenant_id: str | None,
        user_id: str | None,
        entity: str,
        entity_id: str,
        action: str,
        before: dict | None = None,
        after: dict | None = None,
        ip: str | None = None,
    ) -> None:
        await self.col.insert_one(
            {
                "_id": oid(),
                "tenant_id": tenant_id,
                "user_id": user_id,
                "entity": entity,
                "entity_id": entity_id,
                "action": action,
                "before": before,
                "after": after,
                "ip": ip,
                "created_at": utcnow(),
            }
        )


class LedgerService:
    """Balances are derived from ledger_entries. Never store editable running balances."""

    def __init__(self, db):
        self.col = db["ledger_entries"]

    async def post(
        self,
        tenant_id: str,
        *,
        account_type: str,
        account_id: str,
        debit: float = 0,
        credit: float = 0,
        description: str,
        ref_type: str,
        ref_id: str,
        user_id: str | None,
        idempotency_key: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if debit and credit:
            raise AppError("LEDGER_INVALID", "An entry cannot debit and credit together")
        if debit < 0 or credit < 0:
            raise AppError("LEDGER_INVALID", "Amounts must be positive")
        if idempotency_key:
            existing = await self.col.find_one(
                {"tenant_id": tenant_id, "idempotency_key": idempotency_key, "voided": {"$ne": True}}
            )
            if existing:
                from app.repositories.base import serialize

                return serialize(existing)  # type: ignore[return-value]
        doc = {
            "_id": oid(),
            "tenant_id": tenant_id,
            "account_type": account_type,
            "account_id": account_id,
            "debit": money(debit),
            "credit": money(credit),
            "description": description,
            "ref_type": ref_type,
            "ref_id": ref_id,
            "created_by": user_id,
            "created_at": utcnow(),
            "voided": False,
            "idempotency_key": idempotency_key,
            **(extra or {}),
        }
        await self.col.insert_one(doc)
        from app.repositories.base import serialize

        return serialize(doc)  # type: ignore[return-value]

    async def balance(self, tenant_id: str, account_type: str, account_id: str) -> float:
        pipeline = [
            {
                "$match": {
                    "tenant_id": tenant_id,
                    "account_type": account_type,
                    "account_id": account_id,
                    "voided": {"$ne": True},
                }
            },
            {"$group": {"_id": None, "debit": {"$sum": "$debit"}, "credit": {"$sum": "$credit"}}},
        ]
        rows = await self.col.aggregate(pipeline).to_list(1)
        if not rows:
            return 0.0
        return money(rows[0]["debit"] - rows[0]["credit"])

    async def entries(self, tenant_id: str, account_type: str, account_id: str) -> list[dict[str, Any]]:
        from app.repositories.base import serialize

        cursor = self.col.find(
            {
                "tenant_id": tenant_id,
                "account_type": account_type,
                "account_id": account_id,
                "voided": {"$ne": True},
            }
        ).sort("created_at", 1)
        items = [serialize(d) for d in await cursor.to_list(1000)]
        running = 0.0
        out = []
        for item in items:
            running += money(item.get("debit")) - money(item.get("credit"))
            out.append({**item, "balance": running})
        return out

    async def sum_account_type(self, tenant_id: str, account_type: str) -> float:
        pipeline = [
            {"$match": {"tenant_id": tenant_id, "account_type": account_type, "voided": {"$ne": True}}},
            {"$group": {"_id": None, "debit": {"$sum": "$debit"}, "credit": {"$sum": "$credit"}}},
        ]
        rows = await self.col.aggregate(pipeline).to_list(1)
        if not rows:
            return 0.0
        return money(rows[0]["debit"] - rows[0]["credit"])

    async def void(self, tenant_id: str, entry_id: str, user_id: str | None) -> None:
        result = await self.col.update_one(
            {"_id": entry_id, "tenant_id": tenant_id, "voided": {"$ne": True}},
            {"$set": {"voided": True, "voided_at": utcnow(), "voided_by": user_id}},
        )
        if result.modified_count != 1:
            raise NotFoundError("Ledger entry not found")


class NotificationService:
    def __init__(self, db):
        self.repo = TenantRepository(db, "notifications")

    async def notify(self, tenant_id: str, user_id: str | None, title: str, body: str, kind: str = "info") -> None:
        await self.repo.insert(
            tenant_id,
            {"user_id": user_id, "title": title, "body": body, "kind": kind, "read": False, "status": "active"},
            user_id,
        )


class MasterService:
    SEARCH: dict[str, list[str]] = {
        "locations": ["name", "city", "address"],
        "routes": ["name", "origin_name", "destination_name"],
        "vehicles": ["vehicle_number", "make", "model"],
        "drivers": ["name", "mobile", "licence_number"],
        "employees": ["name", "mobile", "role_name"],
        "parties": ["name", "mobile", "city"],
        "fuel_providers": ["name", "location", "contact"],
        "partners": ["name", "mobile", "company"],
        "expenses": ["category", "remarks", "vendor"],
        "lrs": ["lr_number", "sender_name", "receiver_name", "vehicle_number"],
        "trips": ["trip_number", "origin_name", "destination_name"],
        "collections": ["party_name", "reference"],
    }

    def __init__(self, db, collection: str):
        self.repo = TenantRepository(db, collection)
        self.collection = collection
        self.audit = AuditService(db)

    async def list(self, tenant_id: str, **kwargs):
        return await self.repo.list(
            tenant_id,
            filters=kwargs.get("filters"),
            search_fields=self.SEARCH.get(self.collection, ["name"]),
            search=kwargs.get("search"),
            page=int(kwargs.get("page") or 1),
            limit=min(int(kwargs.get("limit") or 20), 100),
        )

    async def get(self, tenant_id: str, item_id: str):
        item = await self.repo.get(tenant_id, item_id)
        if not item:
            raise NotFoundError()
        return item

    async def create(self, tenant_id: str, data: dict, user_id: str | None, ip: str | None = None):
        item = await self.repo.insert(tenant_id, data, user_id)
        await self.audit.record(
            tenant_id=tenant_id, user_id=user_id, entity=self.collection, entity_id=item["id"], action="create", after=item, ip=ip
        )
        return item

    async def update(self, tenant_id: str, item_id: str, data: dict, user_id: str | None, ip: str | None = None):
        before = await self.get(tenant_id, item_id)
        item = await self.repo.update(tenant_id, item_id, data, user_id)
        await self.audit.record(
            tenant_id=tenant_id, user_id=user_id, entity=self.collection, entity_id=item_id, action="update", before=before, after=item, ip=ip
        )
        return item

    async def delete(self, tenant_id: str, item_id: str, user_id: str | None, ip: str | None = None):
        before = await self.get(tenant_id, item_id)
        ok = await self.repo.soft_delete(tenant_id, item_id, user_id)
        if not ok:
            raise NotFoundError()
        await self.audit.record(
            tenant_id=tenant_id, user_id=user_id, entity=self.collection, entity_id=item_id, action="archive", before=before, ip=ip
        )
        return {"success": True}
