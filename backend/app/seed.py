from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import hash_password
from app.repositories.base import oid, utcnow
from app.services.auth import TenantService
from app.services.core import LedgerService
from app.services.finance import FinanceOpsService
from app.services.ops import LrService, TripService


async def seed_demo(db) -> None:
    existing = await db["users"].find_one({"email": "platform@oi-pulse.local"})
    if existing:
        return
    platform_id = oid()
    await db["users"].insert_one(
        {
            "_id": platform_id,
            "email": "platform@oi-pulse.local",
            "name": "Platform Super Admin",
            "role": "PLATFORM_SUPER_ADMIN",
            "permissions": ROLE_PERMISSIONS["PLATFORM_SUPER_ADMIN"],
            "password_hash": hash_password("Platform@123"),
            "status": "active",
            "tenant_id": None,
            "is_deleted": False,
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
    )
    tenant_svc = TenantService(db)
    tenant = await tenant_svc.create_tenant(
        {
            "business_name": "Demo Transport",
            "owner_name": "Demo Owner",
            "owner_email": "owner@demo.local",
            "owner_password": "Owner@123",
            "mobile": "9000000001",
            "address": "Hinganghat, Maharashtra",
            "gstin": "27AAAAA0000A1Z5",
        },
        platform_id,
    )
    tid = tenant["id"]
    loc_repo = db["locations"]
    hg = {
        "_id": oid(),
        "tenant_id": tid,
        "name": "Hinganghat",
        "city": "Hinganghat",
        "state": "Maharashtra",
        "type": "base",
        "status": "active",
        "is_deleted": False,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    nag = {**hg, "_id": oid(), "name": "Nagpur", "city": "Nagpur"}
    wadi = {**hg, "_id": oid(), "name": "Wadi", "city": "Wadi"}
    await loc_repo.insert_many([hg, nag, wadi])
    routes = []
    pairs = [(hg, nag), (nag, hg), (hg, wadi), (wadi, hg)]
    for origin, dest in pairs:
        routes.append(
            {
                "_id": oid(),
                "tenant_id": tid,
                "name": f"{origin['name']} -> {dest['name']}",
                "origin_id": origin["_id"],
                "destination_id": dest["_id"],
                "origin_name": origin["name"],
                "destination_name": dest["name"],
                "status": "active",
                "is_deleted": False,
                "created_at": utcnow(),
                "updated_at": utcnow(),
            }
        )
    await db["routes"].insert_many(routes)
    vehicle = {
        "_id": oid(),
        "tenant_id": tid,
        "vehicle_number": "MH40AB1234",
        "vehicle_type": "Truck",
        "make": "Tata",
        "model": "407",
        "year": 2021,
        "fuel_type": "Diesel",
        "status": "available",
        "base_location_id": hg["_id"],
        "is_temporary": False,
        "is_deleted": False,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db["vehicles"].insert_one(vehicle)
    driver = {
        "_id": oid(),
        "tenant_id": tid,
        "name": "Ramesh",
        "mobile": "9000000002",
        "licence_number": "MH14 20110012345",
        "status": "active",
        "is_deleted": False,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db["drivers"].insert_one(driver)
    party = {
        "_id": oid(),
        "tenant_id": tid,
        "name": "Prakash Food",
        "mobile": "7020385327",
        "city": "Hinganghat",
        "status": "active",
        "is_deleted": False,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db["parties"].insert_one(party)
    deewanji = {
        "_id": oid(),
        "tenant_id": tid,
        "email": "deewanji@demo.local",
        "name": "Deewanji",
        "mobile": "9000000003",
        "role": "DEEWANJI",
        "permissions": ROLE_PERMISSIONS["DEEWANJI"],
        "password_hash": hash_password("Deewanji@123"),
        "status": "active",
        "is_deleted": False,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db["users"].insert_one(deewanji)
    owner = await db["users"].find_one({"email": "owner@demo.local"})
    uid = str(owner["_id"]) if owner else platform_id
    trip = await TripService(db).create(
        tid,
        {
            "trip_kind": "indoor",
            "route_id": routes[0]["_id"],
            "journey_type": "one_way",
            "vehicle_id": vehicle["_id"],
            "driver_id": driver["_id"],
            "start_at": utcnow().isoformat(),
        },
        uid,
        tenant,
    )
    await LrService(db).create(
        tid,
        {
            "trip_id": trip["id"],
            "sender_id": party["_id"],
            "receiver_name": "Nagpur Depot",
            "freight_amount": 4500,
            "freight_type": "NOT_PAID",
            "articles": "Food items",
            "weight": 1200,
        },
        uid,
        tenant,
    )
    await LedgerService(db).post(
        tid,
        account_type="driver",
        account_id=driver["_id"],
        debit=5000,
        description="Opening advance",
        ref_type="opening",
        ref_id=driver["_id"],
        user_id=uid,
    )
    await FinanceOpsService(db).record_collection(
        tid,
        {"party_id": party["_id"], "amount": 1500, "payment_mode": "Cash", "deewanji_id": deewanji["_id"]},
        uid,
        tenant,
    )
