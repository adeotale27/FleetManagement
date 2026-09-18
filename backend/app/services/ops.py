from datetime import datetime
from app.core.exceptions import AppError, NotFoundError
from app.repositories.base import TenantRepository
from app.services.core import ACTIVE_TRIP_STATUSES, TRIP_TRANSITIONS, AuditService, LedgerService, MasterService, SequenceService, money


class TripService:
    def __init__(self, db):
        self.db = db
        self.trips = MasterService(db, "trips")
        self.vehicles = TenantRepository(db, "vehicles")
        self.drivers = TenantRepository(db, "drivers")
        self.routes = TenantRepository(db, "routes")
        self.seq = SequenceService(db)
        self.ledger = LedgerService(db)
        self.audit = AuditService(db)

    async def create(self, tenant_id: str, data: dict, user_id: str | None, tenant: dict) -> dict:
        trip_kind = data.get("trip_kind")
        if trip_kind not in {"indoor", "outdoor"}:
            raise AppError("TRIP_KIND_REQUIRED", "Choose Indoor or Outdoor trip")
        payload = {**data, "status": data.get("status") or "new"}
        if trip_kind == "indoor":
            route = await self.routes.get(tenant_id, data.get("route_id") or "")
            if not route:
                raise AppError("ROUTE_REQUIRED", "Select a configured indoor route")
            payload["origin_name"] = route.get("origin_name")
            payload["destination_name"] = route.get("destination_name")
            payload["origin_location_id"] = route.get("origin_id")
            payload["destination_location_id"] = route.get("destination_id")
            payload["route_name"] = route.get("name")
        if data.get("journey_type") == "round_trip" and not data.get("expected_return_at"):
            raise AppError("RETURN_REQUIRED", "Round trips require expected return date/time")
        vehicle_id = data.get("vehicle_id")
        if data.get("vehicle_mode") == "temporary":
            temp = await self.vehicles.insert(
                tenant_id,
                {
                    "vehicle_number": data.get("temp_vehicle_number"),
                    "vehicle_type": data.get("temp_vehicle_type") or "Truck",
                    "status": "on_trip",
                    "is_temporary": True,
                    "owner": data.get("temp_vehicle_owner"),
                },
                user_id,
            )
            payload["vehicle_id"] = temp["id"]
            payload["vehicle_number"] = temp["vehicle_number"]
            payload["temporary_vehicle"] = True
        elif vehicle_id:
            vehicle = await self.vehicles.get(tenant_id, vehicle_id)
            if not vehicle:
                raise NotFoundError("Vehicle not found")
            if vehicle.get("status") not in {"available", "on_trip"} and not data.get("override_vehicle"):
                raise AppError("VEHICLE_NOT_AVAILABLE", "This vehicle is not available")
            conflict = await self.trips.repo.find_one(
                tenant_id, {"vehicle_id": vehicle_id, "status": {"$in": list(ACTIVE_TRIP_STATUSES)}}
            )
            if conflict and not data.get("override_vehicle"):
                raise AppError("VEHICLE_NOT_AVAILABLE", "This vehicle is already assigned to another active trip.")
            payload["vehicle_id"] = vehicle_id
            payload["vehicle_number"] = vehicle.get("vehicle_number")
            await self.vehicles.update(tenant_id, vehicle_id, {"status": "on_trip"}, user_id)
        driver_id = data.get("driver_id")
        if driver_id:
            driver = await self.drivers.get(tenant_id, driver_id)
            if not driver:
                raise NotFoundError("Driver not found")
            dconflict = await self.trips.repo.find_one(
                tenant_id, {"driver_id": driver_id, "status": {"$in": list(ACTIVE_TRIP_STATUSES)}}
            )
            if dconflict and not data.get("override_driver"):
                raise AppError("DRIVER_NOT_AVAILABLE", "This driver is already assigned to another active trip.")
            payload["driver_id"] = driver_id
            payload["driver_name"] = driver.get("name")
        prefix = (tenant.get("settings") or {}).get("trip_prefix", "TRIP")
        payload["trip_number"] = await self.seq.next(tenant_id, "trip", prefix)
        payload["amount"] = money(data.get("amount"))
        item = await self.trips.create(tenant_id, payload, user_id)
        return item

    async def transition(self, tenant_id: str, trip_id: str, to_status: str, user_id: str | None) -> dict:
        trip = await self.trips.get(tenant_id, trip_id)
        allowed = TRIP_TRANSITIONS.get(trip.get("status"), set())
        if to_status not in allowed:
            raise AppError("INVALID_TRANSITION", f"Cannot move from {trip.get('status')} to {to_status}")
        updated = await self.trips.update(tenant_id, trip_id, {"status": to_status}, user_id)
        if to_status in {"completed", "closed", "cancelled"} and trip.get("vehicle_id"):
            await self.vehicles.update(tenant_id, trip["vehicle_id"], {"status": "available"}, user_id)
        return updated


class LrService:
    def __init__(self, db):
        self.lrs = MasterService(db, "lrs")
        self.trips = TenantRepository(db, "trips")
        self.parties = TenantRepository(db, "parties")
        self.seq = SequenceService(db)
        self.ledger = LedgerService(db)
        self.templates = TenantRepository(db, "templates")

    async def create(self, tenant_id: str, data: dict, user_id: str | None, tenant: dict) -> dict:
        payload = {**data}
        trip = None
        if data.get("trip_id"):
            trip = await self.trips.get(tenant_id, data["trip_id"])
            if not trip:
                raise NotFoundError("Trip not found")
            payload.setdefault("date", trip.get("start_at") or datetime.utcnow().isoformat())
            payload.setdefault("vehicle_number", trip.get("vehicle_number"))
            payload.setdefault("driver_name", trip.get("driver_name"))
            payload.setdefault("from_location", trip.get("origin_name"))
            payload.setdefault("to_location", trip.get("destination_name"))
            payload.setdefault("trip_number", trip.get("trip_number"))
        if data.get("create_sender") and data.get("sender_name"):
            party = await self.parties.insert(
                tenant_id,
                {
                    "name": data["sender_name"],
                    "mobile": data.get("sender_mobile"),
                    "city": data.get("from_location"),
                    "status": "active",
                },
                user_id,
            )
            payload["sender_id"] = party["id"]
            payload["sender_name"] = party["name"]
        sender_id = payload.get("sender_id")
        if sender_id:
            sender = await self.parties.get(tenant_id, sender_id)
            if sender:
                payload["sender_name"] = sender.get("name")
                payload["sender_mobile"] = sender.get("mobile")
        items = data.get("items") or []
        freight = money(data.get("freight_amount"))
        if items:
            freight = sum(money(i.get("amount")) for i in items)
            payload["items"] = items
        hamali = money(data.get("hamali"))
        other = money(data.get("other_charges"))
        advance = money(data.get("advance"))
        collection = money(data.get("collection_amount"))
        total = freight + hamali + other
        payload.update(
            {
                "freight_amount": freight,
                "hamali": hamali,
                "other_charges": other,
                "advance": advance,
                "collection_amount": collection,
                "total": total,
                "amount_received": advance + collection,
                "balance": total - advance - collection,
                "freight_type": data.get("freight_type") or "NOT_PAID",
                "status": data.get("status") or "booked",
            }
        )
        prefix = (tenant.get("settings") or {}).get("lr_prefix", "LR")
        payload["lr_number"] = await self.seq.next(tenant_id, "lr", prefix)
        lr = await self.lrs.create(tenant_id, payload, user_id)
        if payload["freight_type"] == "NOT_PAID" and sender_id and payload["balance"] > 0:
            await self.ledger.post(
                tenant_id,
                account_type="party",
                account_id=sender_id,
                debit=payload["balance"],
                description=f"Receivable {lr['lr_number']}",
                ref_type="lr",
                ref_id=lr["id"],
                user_id=user_id,
                extra={"party_name": payload.get("sender_name")},
            )
        return lr

    async def template(self, tenant_id: str) -> dict:
        item = await self.templates.find_one(tenant_id, {"template_type": "lr", "is_default": True})
        return item or {"name": "Default LR", "layout": "standard"}
