import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import create_access_token, hash_password
from app.db.memory import FakeDB
from app.repositories.base import utcnow


@pytest.fixture
def client():
    db = FakeDB()
    for uid, tid, email in (("ua", "ta", "a@t.local"), ("ub", "tb", "b@t.local")):
        db["users"].docs.append(
            {
                "_id": uid,
                "email": email,
                "name": uid,
                "role": "TENANT_OWNER",
                "permissions": ROLE_PERMISSIONS["TENANT_OWNER"],
                "password_hash": hash_password("secret"),
                "status": "active",
                "tenant_id": tid,
                "is_deleted": False,
                "created_at": utcnow(),
            }
        )
        db["tenants"].docs.append({"_id": tid, "business_name": tid, "status": "active", "settings": {}, "branding": {}})

    async def fake_ping() -> bool:
        return True

    async def fake_close() -> None:
        return None

    import app.db.mongo as mongo
    import app.api.v1.router as routes
    import app.main as mainmod
    import app.api.deps as depsmod

    mongo.get_db = lambda: db
    routes.get_db = lambda: db
    depsmod.get_db = lambda: db
    mainmod.get_db = lambda: db
    mongo.ping_db = fake_ping
    routes.ping_db = fake_ping
    mongo.close_db = fake_close
    mainmod.close_db = fake_close
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c, db


def tok(tid, uid):
    return create_access_token({"sub": uid, "tenant_id": tid, "role": "TENANT_OWNER", "permissions": ROLE_PERMISSIONS["TENANT_OWNER"]})


def test_party_and_collection_isolation(client):
    c, _ = client
    a, b = tok("ta", "ua"), tok("tb", "ub")
    created = c.post("/api/v1/parties", json={"name": "A Foods", "mobile": "90000", "status": "active"}, headers={"Authorization": f"Bearer {a}"})
    assert created.status_code == 200
    pid = created.json()["data"]["id"]
    hidden = c.get(f"/api/v1/parties/{pid}", headers={"Authorization": f"Bearer {b}"})
    assert hidden.status_code in {403, 404}
    listed = c.get("/api/v1/parties", headers={"Authorization": f"Bearer {b}"})
    assert listed.json()["data"]["total"] == 0
    col = c.post(
        "/api/v1/finance/collections",
        json={"party_id": pid, "amount": 10, "payment_mode": "Cash"},
        headers={"Authorization": f"Bearer {b}"},
    )
    assert col.status_code >= 400
