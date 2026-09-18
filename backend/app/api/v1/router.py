from typing import Any
from fastapi import APIRouter, Depends, Query, Request
from app.api.deps import get_current_user, require_permission, require_tenant
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.config import get_settings
from app.db.mongo import get_db, ping_db
from app.repositories.base import GlobalRepository, TenantRepository
from app.services.auth import AuthService, TenantService
from app.services.core import LedgerService, MasterService
from app.services.finance import FinanceOpsService
from app.services.ops import LrService, TripService

router = APIRouter()

RESOURCES = {
    "locations": "location",
    "routes": "route",
    "vehicle-models": ("vehicle_models", "vehicle"),
    "vehicles": "vehicle",
    "vehicle-documents": ("vehicle_documents", "vehicle"),
    "maintenance": ("vehicle_maintenance", "vehicle"),
    "drivers": "driver",
    "employees": "employee",
    "parties": "party",
    "fuel-providers": ("fuel_providers", "fuel"),
    "fuel-entries": ("fuel_entries", "fuel"),
    "partners": ("partners", "partner"),
    "partner-trips": ("partner_trips", "partner"),
    "expenses": "expense",
    "collections": "collection",
    "handovers": ("handovers", "collection"),
    "lrs": "lr",
    "trips": "trip",
    "templates": "template",
    "notifications": "notification",
}


def _map(slug: str) -> tuple[str, str]:
    spec = RESOURCES[slug]
    if isinstance(spec, tuple):
        return spec
    return slug, spec


@router.get("/health")
async def health():
    return {"success": True, "status": "ok"}


@router.get("/health/db")
async def health_db():
    ok = await ping_db()
    return {"success": ok, "status": "ok" if ok else "down"}


@router.get("/public-config")
async def public_config():
    s = get_settings()
    return {"success": True, "data": {"login": "hidden" if s.login_hidden else "required", "app_name": s.app_name}}


PERSONAS = {
    "platform": "platform@oi-pulse.local",
    "owner": "owner@demo.local",
    "deewanji": "deewanji@demo.local",
}


@router.post("/auth/dev-session")
async def dev_session(body: dict[str, Any] | None = None):
    from app.core.config import get_settings
    from app.seed import seed_demo

    if not get_settings().login_hidden or get_settings().is_production:
        raise ForbiddenError("Login bypass is disabled")
    persona = (body or {}).get("persona") or "owner"
    email = PERSONAS.get(persona)
    if not email:
        raise NotFoundError("Unknown persona")
    db = get_db()
    user = await db["users"].find_one({"email": email, "is_deleted": {"$ne": True}})
    if not user:
        await seed_demo(db)
        user = await db["users"].find_one({"email": email})
    if not user:
        raise NotFoundError("Demo user missing")
    result = await AuthService(db).authenticate(email, {
        "platform": "Platform@123",
        "owner": "Owner@123",
        "deewanji": "Deewanji@123",
    }[persona])
    return {"success": True, "data": result}


@router.get("/auth/me")
async def me(user=Depends(get_current_user)):
    return {"success": True, "data": user}


@router.get("/platform/tenants")
async def list_tenants(page: int = 1, limit: int = 20, user=Depends(require_permission("platform:tenants"))):
    data = await GlobalRepository(get_db(), "tenants").list(page=page, limit=limit)
    return {"success": True, "data": data}


@router.post("/platform/tenants")
async def create_tenant(body: dict[str, Any], user=Depends(require_permission("platform:tenants"))):
    tenant = await TenantService(get_db()).create_tenant(body, user["id"])
    return {"success": True, "data": tenant}


@router.get("/platform/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, user=Depends(require_permission("platform:tenants"))):
    item = await GlobalRepository(get_db(), "tenants").get(tenant_id)
    if not item:
        raise NotFoundError("Tenant not found")
    return {"success": True, "data": item}


@router.patch("/platform/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, body: dict[str, Any], user=Depends(require_permission("platform:tenants"))):
    item = await GlobalRepository(get_db(), "tenants").update(tenant_id, body)
    return {"success": True, "data": item}


@router.post("/platform/tenants/{tenant_id}/support-access")
async def support_access(tenant_id: str, user=Depends(require_permission("platform:support"))):
    data = await TenantService(get_db()).support_token(tenant_id, user)
    return {"success": True, "data": data}


@router.get("/platform/overview")
async def platform_overview(user=Depends(require_permission("platform:health"))):
    db = get_db()
    tenants = db["tenants"]
    users = db["users"]
    total = await tenants.count_documents({"is_deleted": {"$ne": True}})
    active = await tenants.count_documents({"status": {"$in": ["active", "trial"]}, "is_deleted": {"$ne": True}})
    return {
        "success": True,
        "data": {
            "total_tenants": total,
            "active_tenants": active,
            "inactive_tenants": total - active,
            "active_users": await users.count_documents({"status": "active", "is_deleted": {"$ne": True}}),
            "system_health": "ok" if await ping_db() else "down",
        },
    }


@router.get("/platform/audit")
async def platform_audit(page: int = 1, limit: int = 50, user=Depends(require_permission("platform:audit"))):
    db = get_db()
    total = await db["audit_logs"].count_documents({})
    items = await db["audit_logs"].find({}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    from app.repositories.base import serialize

    return {
        "success": True,
        "data": {
            "items": [serialize(i) for i in items],
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": page * limit < total,
        },
    }


@router.get("/settings")
async def get_settings(user=Depends(require_tenant)):
    return {"success": True, "data": user.get("tenant")}


@router.patch("/settings")
async def patch_settings(body: dict[str, Any], user=Depends(require_permission("settings:update"))):
    item = await GlobalRepository(get_db(), "tenants").update(user["tenant_id"], body)
    return {"success": True, "data": item}


@router.get("/users")
async def list_users(user=Depends(require_permission("settings:read"))):
    db = get_db()
    items = await db["users"].find({"tenant_id": user["tenant_id"], "is_deleted": {"$ne": True}}).to_list(200)
    from app.repositories.base import serialize

    return {"success": True, "data": {"items": [serialize({**i, "password_hash": None}) for i in items]}}


@router.post("/users")
async def create_user(body: dict[str, Any], user=Depends(require_permission("settings:update"))):
    from app.core.permissions import ROLE_PERMISSIONS
    from app.core.security import hash_password
    from app.repositories.base import oid, utcnow

    db = get_db()
    doc = {
        "_id": oid(),
        "tenant_id": user["tenant_id"],
        "email": body["email"].lower(),
        "name": body.get("name"),
        "mobile": body.get("mobile"),
        "role": body.get("role") or "OPERATIONS_USER",
        "permissions": body.get("permissions") or ROLE_PERMISSIONS.get(body.get("role") or "OPERATIONS_USER", []),
        "password_hash": hash_password(body.get("password") or "ChangeMe@123"),
        "status": "active",
        "is_deleted": False,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await db["users"].insert_one(doc)
    from app.repositories.base import serialize

    return {"success": True, "data": serialize({**doc, "password_hash": None})}


@router.get("/dashboard/owner")
async def owner_dashboard(user=Depends(require_tenant)):
    if not user.get("tenant_id"):
        raise ForbiddenError("Tenant context required")
    data = await FinanceOpsService(get_db()).dashboard(user["tenant_id"])
    return {"success": True, "data": data}


@router.get("/search")
async def search(q: str = Query(min_length=2), user=Depends(require_tenant)):
    db = get_db()
    tenant_id = user["tenant_id"]
    groups = {}
    for coll, fields in {
        "vehicles": ["vehicle_number"],
        "drivers": ["name", "mobile"],
        "parties": ["name", "mobile"],
        "trips": ["trip_number"],
        "lrs": ["lr_number"],
    }.items():
        query = {"tenant_id": tenant_id, "is_deleted": {"$ne": True}, "$or": [{f: {"$regex": q, "$options": "i"}} for f in fields]}
        items = await db[coll].find(query).limit(8).to_list(8)
        from app.repositories.base import serialize

        groups[coll] = [serialize(i) for i in items]
    return {"success": True, "data": groups}


@router.get("/finance/ledger/{account_type}/{account_id}")
async def ledger(account_type: str, account_id: str, user=Depends(require_permission("finance:read"))):
    svc = LedgerService(get_db())
    entries = await svc.entries(user["tenant_id"], account_type, account_id)
    balance = await svc.balance(user["tenant_id"], account_type, account_id)
    return {"success": True, "data": {"entries": entries, "balance": balance}}


@router.get("/finance/receivables")
async def receivables(user=Depends(require_permission("finance:read"))):
    items = await FinanceOpsService(get_db()).party_outstanding_list(user["tenant_id"])
    return {"success": True, "data": {"items": items}}


@router.post("/finance/collections")
async def create_collection(body: dict[str, Any], request: Request, user=Depends(require_permission("collection:create"))):
    if user.get("idempotency_key"):
        body["idempotency_key"] = user["idempotency_key"]
    data = await FinanceOpsService(get_db()).record_collection(user["tenant_id"], body, user["id"], user.get("tenant") or {})
    return {"success": True, "data": data}


@router.post("/finance/handovers")
async def create_handover(body: dict[str, Any], user=Depends(require_permission("collection:create"))):
    data = await FinanceOpsService(get_db()).handover(user["tenant_id"], body, user["id"])
    return {"success": True, "data": data}


@router.post("/finance/expenses")
async def create_expense(body: dict[str, Any], user=Depends(require_permission("expense:create"))):
    data = await FinanceOpsService(get_db()).record_expense(user["tenant_id"], body, user["id"])
    return {"success": True, "data": data}


@router.post("/finance/advances")
async def create_advance(body: dict[str, Any], user=Depends(require_permission("finance:create"))):
    data = await FinanceOpsService(get_db()).advance(user["tenant_id"], body, user["id"])
    return {"success": True, "data": data}


@router.post("/fuel/entries")
async def create_fuel(body: dict[str, Any], user=Depends(require_permission("fuel:create"))):
    data = await FinanceOpsService(get_db()).fuel_entry(user["tenant_id"], body, user["id"])
    return {"success": True, "data": data}


@router.post("/fuel/payments")
async def fuel_pay(body: dict[str, Any], user=Depends(require_permission("fuel:create"))):
    data = await FinanceOpsService(get_db()).fuel_payment(user["tenant_id"], body, user["id"])
    return {"success": True, "data": data}


@router.post("/partners/trips")
async def partner_trip(body: dict[str, Any], user=Depends(require_permission("partner:create"))):
    data = await FinanceOpsService(get_db()).partner_trip(user["tenant_id"], body, user["id"])
    return {"success": True, "data": data}


@router.post("/trips")
async def create_trip(body: dict[str, Any], user=Depends(require_permission("trip:create"))):
    data = await TripService(get_db()).create(user["tenant_id"], body, user["id"], user.get("tenant") or {})
    return {"success": True, "data": data}


@router.post("/trips/{trip_id}/status")
async def trip_status(trip_id: str, body: dict[str, Any], user=Depends(require_permission("trip:update"))):
    data = await TripService(get_db()).transition(user["tenant_id"], trip_id, body.get("status"), user["id"])
    return {"success": True, "data": data}


@router.post("/lrs")
async def create_lr(body: dict[str, Any], user=Depends(require_permission("lr:create"))):
    data = await LrService(get_db()).create(user["tenant_id"], body, user["id"], user.get("tenant") or {})
    return {"success": True, "data": data}


@router.get("/lrs/{item_id}/print")
async def print_lr(item_id: str, user=Depends(require_permission("lr:read"))):
    lr = await MasterService(get_db(), "lrs").get(user["tenant_id"], item_id)
    tmpl = await LrService(get_db()).template(user["tenant_id"])
    tenant = user.get("tenant") or {}
    branding = tenant.get("branding") or {}
    html = f"""<!doctype html><html><head><title>{lr.get('lr_number')}</title>
    <style>body{{font-family:sans-serif;padding:24px}} table{{width:100%;border-collapse:collapse}}
    td,th{{border:1px solid #ccc;padding:8px}} .head{{display:flex;justify-content:space-between}}</style></head>
    <body><div class="head"><div><h1>{branding.get('company_name') or tenant.get('business_name') or 'LR'}</h1>
    <p>{(tenant.get('profile') or {}).get('address','')}</p></div><div><strong>{lr.get('lr_number')}</strong></div></div>
    <p>Sender: {lr.get('sender_name')} &nbsp; Receiver: {lr.get('receiver_name')}</p>
    <p>From: {lr.get('from_location')} &nbsp; To: {lr.get('to_location')}</p>
    <p>Vehicle: {lr.get('vehicle_number')} &nbsp; Driver: {lr.get('driver_name')}</p>
    <p>Freight: {lr.get('freight_amount')} ({lr.get('freight_type')}) &nbsp; Balance: {lr.get('balance')}</p>
    <p>{tmpl.get('terms','')}</p><p>{tmpl.get('footer','')}</p>
    <script>window.print()</script></body></html>"""
    from fastapi.responses import HTMLResponse

    return HTMLResponse(html)


@router.get("/reports/{name}")
async def reports(name: str, user=Depends(require_permission("report:read")), format: str = "json"):
    db = get_db()
    mapping = {
        "trips": "trips",
        "vehicles": "vehicles",
        "drivers": "drivers",
        "lrs": "lrs",
        "parties": "parties",
        "collections": "collections",
        "expenses": "expenses",
        "fuel": "fuel_entries",
        "maintenance": "vehicle_maintenance",
        "partners": "partner_trips",
    }
    coll = mapping.get(name)
    if not coll:
        raise NotFoundError("Unknown report")
    items = await db[coll].find({"tenant_id": user["tenant_id"], "is_deleted": {"$ne": True}}).limit(2000).to_list(2000)
    from app.repositories.base import serialize

    rows = [serialize(i) for i in items]
    if format == "csv":
        import csv
        import io

        buf = io.StringIO()
        if rows:
            writer = csv.DictWriter(buf, fieldnames=sorted(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(buf.getvalue(), media_type="text/csv")
    return {"success": True, "data": {"items": rows, "total": len(rows)}}


@router.get("/{resource}")
async def list_resource(
    resource: str,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    status: str | None = None,
    user=Depends(require_tenant),
):
    if resource not in RESOURCES:
        raise NotFoundError("Unknown resource")
    collection, perm = _map(resource)
    from app.core.permissions import has_permission

    if not has_permission(user["permissions"], f"{perm}:read"):
        raise ForbiddenError("You do not have permission for this action")
    filters = {}
    if status:
        filters["status"] = status
    data = await MasterService(get_db(), collection).list(user["tenant_id"], filters=filters or None, search=search, page=page, limit=limit)
    return {"success": True, "data": data}


@router.get("/{resource}/{item_id}")
async def get_resource(resource: str, item_id: str, user=Depends(require_tenant)):
    if resource not in RESOURCES:
        raise NotFoundError("Unknown resource")
    collection, perm = _map(resource)
    from app.core.permissions import has_permission

    if not has_permission(user["permissions"], f"{perm}:read"):
        raise ForbiddenError("You do not have permission for this action")
    item = await MasterService(get_db(), collection).get(user["tenant_id"], item_id)
    extra = {}
    if resource == "parties":
        extra["ledger_balance"] = await LedgerService(get_db()).balance(user["tenant_id"], "party", item_id)
    if resource == "drivers":
        extra["advance_outstanding"] = await LedgerService(get_db()).balance(user["tenant_id"], "driver", item_id)
    if resource == "employees":
        extra["advance_outstanding"] = await LedgerService(get_db()).balance(user["tenant_id"], "employee", item_id)
    if resource == "fuel-providers":
        extra["outstanding"] = await LedgerService(get_db()).balance(user["tenant_id"], "fuel_pump", item_id)
    if resource == "partners":
        extra["outstanding"] = await LedgerService(get_db()).balance(user["tenant_id"], "partner", item_id)
    return {"success": True, "data": {**item, **extra}}


@router.post("/{resource}")
async def create_resource(resource: str, body: dict[str, Any], user=Depends(require_tenant)):
    if resource not in RESOURCES:
        raise NotFoundError("Unknown resource")
    collection, perm = _map(resource)
    from app.core.permissions import has_permission

    if not has_permission(user["permissions"], f"{perm}:create"):
        raise ForbiddenError("You do not have permission for this action")
    if resource == "trips":
        data = await TripService(get_db()).create(user["tenant_id"], body, user["id"], user.get("tenant") or {})
        return {"success": True, "data": data}
    if resource == "lrs":
        data = await LrService(get_db()).create(user["tenant_id"], body, user["id"], user.get("tenant") or {})
        return {"success": True, "data": data}
    item = await MasterService(get_db(), collection).create(user["tenant_id"], body, user["id"], user.get("ip"))
    return {"success": True, "data": item}


@router.patch("/{resource}/{item_id}")
async def update_resource(resource: str, item_id: str, body: dict[str, Any], user=Depends(require_tenant)):
    if resource not in RESOURCES:
        raise NotFoundError("Unknown resource")
    collection, perm = _map(resource)
    from app.core.permissions import has_permission

    if not has_permission(user["permissions"], f"{perm}:update"):
        raise ForbiddenError("You do not have permission for this action")
    item = await MasterService(get_db(), collection).update(user["tenant_id"], item_id, body, user["id"])
    return {"success": True, "data": item}


@router.delete("/{resource}/{item_id}")
async def delete_resource(resource: str, item_id: str, user=Depends(require_tenant)):
    if resource not in RESOURCES:
        raise NotFoundError("Unknown resource")
    collection, perm = _map(resource)
    from app.core.permissions import has_permission

    if not has_permission(user["permissions"], f"{perm}:delete"):
        raise ForbiddenError("You do not have permission for this action")
    data = await MasterService(get_db(), collection).delete(user["tenant_id"], item_id, user["id"])
    return {"success": True, "data": data}
