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
    now = utcnow()
    await db["vehicle_models"].insert_many(
        [
            {"_id": oid(), "tenant_id": tid, "make": "Ashok Leyland", "model": "1618", "status": "active", "is_deleted": False, "created_at": now, "updated_at": now},
            {"_id": oid(), "tenant_id": tid, "make": "Tata", "model": "407", "status": "active", "is_deleted": False, "created_at": now, "updated_at": now},
        ]
    )
    extra_vehicles = [
        {"vehicle_number": "MH40CM5129", "make": "Tata", "model": "407", "vehicle_type": "LCV", "status": "on_trip"},
        {"vehicle_number": "MH40AB4455", "make": "Ashok Leyland", "model": "1618", "vehicle_type": "Truck", "status": "available"},
        {"vehicle_number": "MH31DE9021", "make": "Tata", "model": "407", "vehicle_type": "LCV", "status": "maintenance"},
    ]
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
        "created_at": now,
        "updated_at": now,
    }
    await db["vehicles"].insert_one(vehicle)
    for v in extra_vehicles:
        await db["vehicles"].insert_one({**vehicle, "_id": oid(), **v, "status": v["status"]})
    extra_drivers = [
        ("Ramesh", "9000000002"),
        ("Ranbid Chaudhari", "8668275499"),
        ("Yaseen Khan", "7000660167"),
        ("Suresh Manohar Fusate", "9270502676"),
        ("SK Yusuf", "9765622917"),
    ]
    driver = None
    for name, mobile in extra_drivers:
        d = {
            "_id": oid(),
            "tenant_id": tid,
            "name": name,
            "mobile": mobile,
            "role_name": "Driver",
            "licence_number": "MH14 20110012345",
            "status": "active",
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
            "created_by_name": "Demo Owner",
        }
        await db["drivers"].insert_one(d)
        if driver is None:
            driver = d
    extra_parties = [
        ("Prakash Food", "7020385327", "Hinganghat"),
        ("Kochar Polypack Private Limited", "2222222222", "Nagpur"),
        ("RJ Polychem Private Limited", "1111111111", "Nagpur"),
        ("Naidu Garage NGP", "7304047399", "Nagpur"),
        ("Mandhaniya Industries", "7020874205", "Wadi"),
        ("Hira Food Products", "9049958211", "Hinganghat"),
        ("A.R. Pulses", "9096569848", "Hinganghat"),
        ("Chainkunwar", "9827172360", "Nagpur"),
    ]
    party = None
    for name, mobile, city in extra_parties:
        p = {
            "_id": oid(),
            "tenant_id": tid,
            "name": name,
            "mobile": mobile,
            "city": city,
            "role_name": "Party",
            "status": "active",
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
            "created_by_name": "Demo Owner",
        }
        await db["parties"].insert_one(p)
        if party is None:
            party = p
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
    await FinanceOpsService(db).record_expense(
        tid,
        {"category": "Toll", "amount": 350, "payment_mode": "Cash", "remarks": "Hinganghat checkpost"},
        uid,
    )
