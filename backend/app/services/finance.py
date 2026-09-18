from datetime import datetime, timedelta, timezone
from app.core.exceptions import AppError, NotFoundError
from app.repositories.base import TenantRepository
from app.services.core import LedgerService, MasterService, SequenceService, money


class FinanceOpsService:
    def __init__(self, db):
        self.db = db
        self.ledger = LedgerService(db)
        self.collections = MasterService(db, "collections")
        self.handovers = MasterService(db, "handovers")
        self.expenses = MasterService(db, "expenses")
        self.parties = TenantRepository(db, "parties")
        self.seq = SequenceService(db)
        self.fuel = MasterService(db, "fuel_entries")
        self.lrs = TenantRepository(db, "lrs")

    async def record_collection(self, tenant_id: str, data: dict, user_id: str, tenant: dict) -> dict:
        party = await self.parties.get(tenant_id, data["party_id"])
        if not party:
            raise NotFoundError("Party not found")
        amount = money(data.get("amount"))
        if amount <= 0:
            raise AppError("AMOUNT_REQUIRED", "Collection amount must be greater than zero")
        prefix = (tenant.get("settings") or {}).get("receipt_prefix", "REC")
        number = await self.seq.next(tenant_id, "receipt", prefix)
        rec = await self.collections.create(
            tenant_id,
            {
                **data,
                "receipt_number": number,
                "party_name": party.get("name"),
                "status": "collected",
                "handover_status": "pending",
                "collected_by": data.get("collected_by") or user_id,
            },
            user_id,
        )
        key = data.get("idempotency_key") or f"col:{tenant_id}:{number}"
        await self.ledger.post(
            tenant_id,
            account_type="party",
            account_id=party["id"],
            credit=amount,
            description=f"Collection {number}",
            ref_type="collection",
            ref_id=rec["id"],
            user_id=user_id,
            idempotency_key=key,
        )
        mode = (data.get("payment_mode") or "Cash").lower()
        cash_account = "cash" if mode == "cash" else "bank"
        await self.ledger.post(
            tenant_id,
            account_type=cash_account,
            account_id="default",
            debit=amount,
            description=f"Collection {number}",
            ref_type="collection",
            ref_id=rec["id"],
            user_id=user_id,
            idempotency_key=f"{key}:{cash_account}",
        )
        if data.get("deewanji_id") and mode == "cash":
            await self.ledger.post(
                tenant_id,
                account_type="deewanji",
                account_id=data["deewanji_id"],
                debit=amount,
                description=f"Cash collected {number}",
                ref_type="collection",
                ref_id=rec["id"],
                user_id=user_id,
                idempotency_key=f"{key}:deewanji",
            )
        outstanding = await self.ledger.balance(tenant_id, "party", party["id"])
        rec["outstanding"] = outstanding
        return rec

    async def handover(self, tenant_id: str, data: dict, user_id: str) -> dict:
        amount = money(data.get("amount"))
        deewanji_id = data["deewanji_id"]
        available = await self.ledger.balance(tenant_id, "deewanji", deewanji_id)
        if amount > available + 0.01:
            raise AppError("INSUFFICIENT_CASH", "Handover exceeds cash with Deewanji")
        item = await self.handovers.create(
            tenant_id,
            {**data, "status": "handed_over", "handed_to": data.get("handed_to") or "owner"},
            user_id,
        )
        await self.ledger.post(
            tenant_id,
            account_type="deewanji",
            account_id=deewanji_id,
            credit=amount,
            description="Handover",
            ref_type="handover",
            ref_id=item["id"],
            user_id=user_id,
        )
        dest = "bank" if data.get("handed_to") == "bank" else "cash"
        await self.ledger.post(
            tenant_id,
            account_type=dest,
            account_id="default",
            debit=amount,
            description="Deewanji handover",
            ref_type="handover",
            ref_id=item["id"],
            user_id=user_id,
        )
        item["cash_with_deewanji"] = await self.ledger.balance(tenant_id, "deewanji", deewanji_id)
        return item

    async def record_expense(self, tenant_id: str, data: dict, user_id: str) -> dict:
        amount = money(data.get("amount"))
        item = await self.expenses.create(tenant_id, {**data, "status": "posted", "amount": amount}, user_id)
        await self.ledger.post(
            tenant_id,
            account_type="expense",
            account_id=data.get("category") or "Other",
            debit=amount,
            description=data.get("remarks") or data.get("category") or "Expense",
            ref_type="expense",
            ref_id=item["id"],
            user_id=user_id,
            extra={"vehicle_id": data.get("vehicle_id"), "trip_id": data.get("trip_id")},
        )
        mode = (data.get("payment_mode") or "Cash").lower()
        account = "cash" if mode == "cash" else "bank"
        await self.ledger.post(
            tenant_id,
            account_type=account,
            account_id="default",
            credit=amount,
            description=f"Expense {item['id']}",
            ref_type="expense",
            ref_id=item["id"],
            user_id=user_id,
        )
        return item

    async def advance(self, tenant_id: str, data: dict, user_id: str) -> dict:
        amount = money(data.get("amount"))
        account_type = data["account_type"]
        account_id = data["account_id"]
        kind = data.get("kind") or "advance"
        await self.ledger.post(
            tenant_id,
            account_type=account_type,
            account_id=account_id,
            debit=amount if kind != "repayment" else 0,
            credit=amount if kind == "repayment" else 0,
            description=kind,
            ref_type="advance",
            ref_id=account_id,
            user_id=user_id,
        )
        if kind != "repayment":
            mode = (data.get("payment_mode") or "Cash").lower()
            await self.ledger.post(
                tenant_id,
                account_type="cash" if mode == "cash" else "bank",
                account_id="default",
                credit=amount,
                description=f"{account_type} {kind}",
                ref_type="advance",
                ref_id=account_id,
                user_id=user_id,
            )
        return {"outstanding": await self.ledger.balance(tenant_id, account_type, account_id)}

    async def fuel_entry(self, tenant_id: str, data: dict, user_id: str) -> dict:
        amount = money(data.get("amount") or (money(data.get("quantity")) * money(data.get("rate"))))
        item = await self.fuel.create(tenant_id, {**data, "amount": amount, "status": "posted"}, user_id)
        if data.get("provider_id"):
            await self.ledger.post(
                tenant_id,
                account_type="fuel_pump",
                account_id=data["provider_id"],
                debit=amount,
                description="Fuel purchase",
                ref_type="fuel",
                ref_id=item["id"],
                user_id=user_id,
            )
        return item

    async def fuel_payment(self, tenant_id: str, data: dict, user_id: str) -> dict:
        amount = money(data["amount"])
        await self.ledger.post(
            tenant_id,
            account_type="fuel_pump",
            account_id=data["provider_id"],
            credit=amount,
            description="Fuel payment",
            ref_type="fuel_payment",
            ref_id=data["provider_id"],
            user_id=user_id,
        )
        return {"outstanding": await self.ledger.balance(tenant_id, "fuel_pump", data["provider_id"])}

    async def partner_trip(self, tenant_id: str, data: dict, user_id: str) -> dict:
        repo = MasterService(self.db, "partner_trips")
        receivable = money(data.get("trip_amount"))
        payable = money(data.get("partner_amount"))
        item = await repo.create(
            tenant_id,
            {**data, "receivable": receivable, "payable": payable, "status": "open"},
            user_id,
        )
        if data.get("customer_id") and receivable:
            await self.ledger.post(
                tenant_id,
                account_type="party",
                account_id=data["customer_id"],
                debit=receivable,
                description="3PL trip receivable",
                ref_type="partner_trip",
                ref_id=item["id"],
                user_id=user_id,
            )
        if data.get("partner_id") and payable:
            await self.ledger.post(
                tenant_id,
                account_type="partner",
                account_id=data["partner_id"],
                debit=payable,
                description="3PL partner payable",
                ref_type="partner_trip",
                ref_id=item["id"],
                user_id=user_id,
            )
        return item

    async def dashboard(self, tenant_id: str) -> dict:
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        col = self.db["ledger_entries"]
        trips = self.db["trips"]
        vehicles = self.db["vehicles"]
        drivers = self.db["drivers"]
        lrs = self.db["lrs"]
        notes = self.db["notifications"]

        async def count(c, q):
            q = {"tenant_id": tenant_id, "is_deleted": {"$ne": True}, **q}
            return await c.count_documents(q)

        receivable = await self.ledger.sum_account_type(tenant_id, "party")
        payable_fuel = await self.ledger.sum_account_type(tenant_id, "fuel_pump")
        payable_partner = await self.ledger.sum_account_type(tenant_id, "partner")
        cash = await self.ledger.balance(tenant_id, "cash", "default")
        bank = await self.ledger.balance(tenant_id, "bank", "default")
        deewanji = await self.ledger.sum_account_type(tenant_id, "deewanji")
        advances_driver = await self.ledger.sum_account_type(tenant_id, "driver")
        advances_emp = await self.ledger.sum_account_type(tenant_id, "employee")
        expense_today_pipe = [
            {
                "$match": {
                    "tenant_id": tenant_id,
                    "account_type": "expense",
                    "voided": {"$ne": True},
                    "created_at": {"$gte": start},
                }
            },
            {"$group": {"_id": None, "amt": {"$sum": "$debit"}}},
        ]
        exp_rows = await col.aggregate(expense_today_pipe).to_list(1)
        collection_today = [
            {
                "$match": {
                    "tenant_id": tenant_id,
                    "ref_type": "collection",
                    "account_type": {"$in": ["cash", "bank"]},
                    "voided": {"$ne": True},
                    "created_at": {"$gte": start},
                }
            },
            {"$group": {"_id": None, "amt": {"$sum": "$debit"}}},
        ]
        col_rows = await col.aggregate(collection_today).to_list(1)
        money_in_pipe = [
            {"$match": {"tenant_id": tenant_id, "account_type": {"$in": ["cash", "bank"]}, "voided": {"$ne": True}}},
            {"$group": {"_id": None, "in": {"$sum": "$debit"}, "out": {"$sum": "$credit"}}},
        ]
        flow = (await col.aggregate(money_in_pipe).to_list(1) or [{}])[0]
        alerts = []
        soon = now + timedelta(days=30)
        expiring = await self.db["vehicle_documents"].find(
            {"tenant_id": tenant_id, "expiry_date": {"$lte": soon.isoformat()}, "is_deleted": {"$ne": True}}
        ).to_list(20)
        for doc in expiring:
            alerts.append(
                {"kind": "document", "title": f"{doc.get('doc_type')} expiring", "body": doc.get("vehicle_number") or ""}
            )
        return {
            "fleet": {
                "drivers": await count(drivers, {}),
                "vehicles": await count(vehicles, {}),
                "available_vehicles": await count(vehicles, {"status": "available"}),
                "active_trips": await count(trips, {"status": {"$in": ["new", "assigned", "started", "in_transit"]}}),
                "repair": await count(vehicles, {"status": "maintenance"}),
            },
            "trips": {
                "total": await count(trips, {}),
                "new": await count(trips, {"status": "new"}),
                "live": await count(trips, {"status": {"$in": ["assigned", "started", "in_transit"]}}),
                "completed": await count(trips, {"status": {"$in": ["completed", "closed"]}}),
                "cancelled": await count(trips, {"status": "cancelled"}),
            },
            "lrs": {
                "all": await count(lrs, {}),
                "booked": await count(lrs, {"status": "booked"}),
                "in_transit": await count(lrs, {"status": "in_transit"}),
                "delivered": await count(lrs, {"status": "delivered"}),
                "settled": await count(lrs, {"status": "settled"}),
            },
            "finance": {
                "money_in": money(flow.get("in")),
                "money_out": money(flow.get("out")),
                "receivable": money(receivable),
                "payable": money(payable_fuel + payable_partner),
                "cash_balance": money(cash),
                "bank_balance": money(bank),
                "today_collection": money((col_rows[0]["amt"] if col_rows else 0)),
                "today_expenses": money((exp_rows[0]["amt"] if exp_rows else 0)),
                "deewanji_cash": money(deewanji),
                "employee_advances": money(advances_emp),
                "driver_advances": money(advances_driver),
                "net_income": money(flow.get("in")) - money(flow.get("out")),
            },
            "alerts": alerts,
            "unread_notifications": await notes.count_documents(
                {"tenant_id": tenant_id, "read": {"$ne": True}, "is_deleted": {"$ne": True}}
            ),
        }

    async def party_outstanding_list(self, tenant_id: str) -> list[dict]:
        pipe = [
            {"$match": {"tenant_id": tenant_id, "account_type": "party", "voided": {"$ne": True}}},
            {"$group": {"_id": "$account_id", "debit": {"$sum": "$debit"}, "credit": {"$sum": "$credit"}, "name": {"$last": "$party_name"}}},
            {"$project": {"party_id": "$_id", "outstanding": {"$subtract": ["$debit", "$credit"]}, "name": 1}},
            {"$match": {"outstanding": {"$gt": 0}}},
            {"$sort": {"outstanding": -1}},
        ]
        return await self.db["ledger_entries"].aggregate(pipe).to_list(200)
