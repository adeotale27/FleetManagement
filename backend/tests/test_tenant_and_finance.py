import pytest
from app.core.permissions import has_permission
from app.repositories.base import TenantRepository
from app.services.core import LedgerService, TRIP_TRANSITIONS
from app.services.ops import TripService
from app.db.memory import FakeDB


@pytest.fixture
def db():
    return FakeDB()


@pytest.mark.asyncio
async def test_tenant_isolation_vehicles(db):
    repo = TenantRepository(db, "vehicles")
    a = await repo.insert("tenant-a", {"vehicle_number": "MH01A1111", "status": "available"}, "u1")
    await repo.insert("tenant-b", {"vehicle_number": "MH02B2222", "status": "available"}, "u2")
    found = await repo.get("tenant-b", a["id"])
    assert found is None
    listed = await repo.list("tenant-b")
    assert listed["total"] == 1
    assert listed["items"][0]["vehicle_number"] == "MH02B2222"


@pytest.mark.asyncio
async def test_ledger_balance_from_transactions(db):
    ledger = LedgerService(db)
    await ledger.post("t1", account_type="party", account_id="p1", debit=10000, description="LR", ref_type="lr", ref_id="lr1", user_id="u")
    await ledger.post("t1", account_type="party", account_id="p1", credit=4000, description="collection", ref_type="collection", ref_id="c1", user_id="u")
    assert await ledger.balance("t1", "party", "p1") == 6000
    assert await ledger.balance("t2", "party", "p1") == 0


@pytest.mark.asyncio
async def test_idempotent_ledger_post(db):
    ledger = LedgerService(db)
    await ledger.post("t1", account_type="cash", account_id="default", debit=100, description="x", ref_type="collection", ref_id="c", user_id="u", idempotency_key="k1")
    await ledger.post("t1", account_type="cash", account_id="default", debit=100, description="x", ref_type="collection", ref_id="c", user_id="u", idempotency_key="k1")
    assert await ledger.balance("t1", "cash", "default") == 100


def test_trip_transitions_defined():
    assert "assigned" in TRIP_TRANSITIONS["new"]
    assert "cancelled" not in TRIP_TRANSITIONS["closed"]


def test_permission_check():
    assert has_permission(["trip:create"], "trip:create")
    assert not has_permission(["trip:read"], "trip:create")
    assert has_permission(["trip:*"], "trip:delete")


@pytest.mark.asyncio
async def test_cross_tenant_trip_lookup(db):
    svc = TripService(db)
    await db["routes"].insert_one(
        {
            "_id": "r1",
            "tenant_id": "a",
            "name": "H -> N",
            "origin_name": "Hinganghat",
            "destination_name": "Nagpur",
            "is_deleted": False,
        }
    )
    await db["vehicles"].insert_one(
        {"_id": "v1", "tenant_id": "a", "vehicle_number": "MH40AB1234", "status": "available", "is_deleted": False}
    )
    trip = await svc.create(
        "a",
        {"trip_kind": "indoor", "route_id": "r1", "journey_type": "one_way", "vehicle_id": "v1"},
        "u",
        {"settings": {"trip_prefix": "TRIP"}},
    )
    missing = await svc.trips.repo.get("b", trip["id"])
    assert missing is None
