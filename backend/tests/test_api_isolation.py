import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.mongo import get_db
from app.db.memory import FakeDB
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import create_access_token, hash_password
from app.repositories.base import utcnow


@pytest.fixture
def client():
    db = FakeDB()
    db["users"].docs.append(
        {
            "_id": "ua",
            "email": "a@t.local",
            "name": "A",
            "role": "TENANT_OWNER",
            "permissions": ROLE_PERMISSIONS["TENANT_OWNER"],
            "password_hash": hash_password("secret"),
            "status": "active",
            "tenant_id": "ta",
            "is_deleted": False,
            "created_at": utcnow(),
        }
    )
    db["users"].docs.append(
        {
            "_id": "ub",
            "email": "b@t.local",
            "name": "B",
            "role": "TENANT_OWNER",
            "permissions": ROLE_PERMISSIONS["TENANT_OWNER"],
            "password_hash": hash_password("secret"),
            "status": "active",
            "tenant_id": "tb",
            "is_deleted": False,
        }
    )
    db["tenants"].docs.append({"_id": "ta", "business_name": "A", "status": "active", "settings": {}, "branding": {}})
    db["tenants"].docs.append({"_id": "tb", "business_name": "B", "status": "active", "settings": {}, "branding": {}})

    async def _db():
        return db

    app.dependency_overrides[get_db] = _db
    # get_db is imported directly in routes; patch module function
    import app.db.mongo as mongo
    import app.api.v1.router as routes
    import app.main as mainmod
    import app.api.deps as depsmod

    async def fake_ping() -> bool:
        return True

    async def fake_close() -> None:
        return None

    mongo.get_db = lambda: db  # type: ignore
    routes.get_db = lambda: db  # type: ignore
    depsmod.get_db = lambda: db  # type: ignore
    mainmod.get_db = lambda: db  # type: ignore
    mongo.ping_db = fake_ping  # type: ignore
    routes.ping_db = fake_ping  # type: ignore
    mongo.close_db = fake_close  # type: ignore
    mainmod.close_db = fake_close  # type: ignore

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c, db
    app.dependency_overrides.clear()


def auth(tenant, uid):
    return create_access_token(
        {"sub": uid, "tenant_id": tenant, "role": "TENANT_OWNER", "permissions": ROLE_PERMISSIONS["TENANT_OWNER"]}
    )


def test_health(client):
    c, _ = client
    res = c.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_cross_tenant_vehicle_hidden(client):
    c, db = client
    token_a = auth("ta", "ua")
    token_b = auth("tb", "ub")
    created = c.post(
        "/api/v1/vehicles",
        json={"vehicle_number": "MH01ISO001", "status": "available"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert created.status_code == 200
    vid = created.json()["data"]["id"]
    denied = c.get(f"/api/v1/vehicles/{vid}", headers={"Authorization": f"Bearer {token_b}"})
    assert denied.status_code in {403, 404}
    listed = c.get("/api/v1/vehicles", headers={"Authorization": f"Bearer {token_b}"})
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 0
