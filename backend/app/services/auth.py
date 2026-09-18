from datetime import datetime, timezone
from typing import Any
from app.core.exceptions import AppError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.permissions import ROLE_PERMISSIONS, has_permission
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.base import GlobalRepository, TenantRepository, oid, utcnow
from app.services.core import AuditService, LedgerService, SequenceService


class AuthService:
    def __init__(self, db):
        self.users = db["users"]
        self.tenants = GlobalRepository(db, "tenants")
        self.audit = AuditService(db)

    async def authenticate(self, email: str, password: str) -> dict[str, Any]:
        user = await self.users.find_one({"email": email.lower().strip(), "is_deleted": {"$ne": True}})
        if not user or not verify_password(password, user.get("password_hash", "")):
            raise UnauthorizedError("Invalid email or password")
        if user.get("status") != "active":
            raise ForbiddenError("User is not active")
        tenant = None
        if user.get("tenant_id"):
            tenant = await self.tenants.get(user["tenant_id"])
            if tenant and tenant.get("status") not in {"active", "trial"}:
                raise ForbiddenError("Tenant is not active")
        token = create_access_token(
            {
                "sub": str(user["_id"]),
                "tenant_id": user.get("tenant_id"),
                "role": user.get("role"),
                "permissions": user.get("permissions") or ROLE_PERMISSIONS.get(user.get("role"), []),
            }
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": self.public_user(user, tenant),
        }

    def public_user(self, user: dict, tenant: dict | None = None) -> dict[str, Any]:
        return {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "name": user.get("name"),
            "mobile": user.get("mobile"),
            "role": user.get("role"),
            "permissions": user.get("permissions") or ROLE_PERMISSIONS.get(user.get("role"), []),
            "tenant_id": user.get("tenant_id"),
            "tenant": tenant,
        }


class TenantService:
    def __init__(self, db):
        self.db = db
        self.tenants = GlobalRepository(db, "tenants")
        self.users = db["users"]
        self.audit = AuditService(db)
        self.seq = SequenceService(db)
        self.templates = TenantRepository(db, "templates")

    async def create_tenant(self, data: dict[str, Any], actor_id: str | None) -> dict[str, Any]:
        slug = (data.get("slug") or data["business_name"]).lower().replace(" ", "-")
        existing = await self.tenants.find_one({"slug": slug})
        if existing:
            raise AppError("TENANT_EXISTS", "Tenant slug already exists")
        tenant = await self.tenants.insert(
            {
                "_id": oid(),
                "business_name": data["business_name"],
                "business_type": data.get("business_type", "transport"),
                "slug": slug,
                "status": "active",
                "plan": data.get("plan", "professional"),
                "limits": data.get("limits") or {"vehicles": 200, "users": 50, "trips": 10000},
                "feature_flags": data.get("feature_flags")
                or {
                    "finance": True,
                    "lr": True,
                    "fuel": True,
                    "third_party": True,
                    "collections": True,
                    "reports": True,
                },
                "branding": {
                    "logo": data.get("logo"),
                    "primary_color": data.get("primary_color", "#163a66"),
                    "company_name": data["business_name"],
                },
                "profile": {
                    "owner_name": data.get("owner_name"),
                    "mobile": data.get("mobile"),
                    "email": data.get("email"),
                    "address": data.get("address"),
                    "gstin": data.get("gstin"),
                    "pan": data.get("pan"),
                    "timezone": data.get("timezone", "Asia/Kolkata"),
                },
                "settings": {
                    "lr_prefix": data.get("lr_prefix", "LR"),
                    "trip_prefix": data.get("trip_prefix", "TRIP"),
                    "receipt_prefix": data.get("receipt_prefix", "REC"),
                    "payment_prefix": data.get("payment_prefix", "PAY"),
                    "expense_categories": [
                        "Fuel",
                        "Toll",
                        "Tea & Food",
                        "Loading",
                        "Unloading",
                        "Parking",
                        "Maintenance",
                        "Repair",
                        "Driver Advance",
                        "Employee Advance",
                        "Other",
                    ],
                    "payment_modes": ["Cash", "UPI", "Bank", "Cheque", "Other"],
                    "approval_thresholds": {"expense": 25000, "advance": 20000},
                },
                "is_deleted": False,
            }
        )
        owner_email = (data.get("owner_email") or data.get("email") or "").lower()
        if owner_email:
            await self.users.insert_one(
                {
                    "_id": oid(),
                    "tenant_id": tenant["id"],
                    "email": owner_email,
                    "name": data.get("owner_name") or "Owner",
                    "mobile": data.get("mobile"),
                    "role": "TENANT_OWNER",
                    "permissions": ROLE_PERMISSIONS["TENANT_OWNER"],
                    "password_hash": hash_password(data.get("owner_password") or "ChangeMe@123"),
                    "status": "active",
                    "is_deleted": False,
                    "created_at": utcnow(),
                    "updated_at": utcnow(),
                }
            )
        await self.templates.insert(
            tenant["id"],
            {
                "template_type": "lr",
                "name": "Default LR",
                "version": 1,
                "is_default": True,
                "status": "active",
                "layout": "standard",
                "fields": ["sender", "receiver", "vehicle", "goods", "freight"],
                "footer": "Subject to local jurisdiction",
                "terms": "Goods booked at owner's risk unless insured.",
            },
            actor_id,
        )
        await self.audit.record(
            tenant_id=None, user_id=actor_id, entity="tenants", entity_id=tenant["id"], action="create", after=tenant
        )
        return tenant

    async def support_token(self, tenant_id: str, actor: dict) -> dict[str, Any]:
        tenant = await self.tenants.get(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found")
        token = create_access_token(
            {
                "sub": actor["id"],
                "tenant_id": tenant_id,
                "role": "TENANT_OWNER",
                "permissions": ROLE_PERMISSIONS["TENANT_OWNER"],
                "support": True,
                "impersonator_id": actor["id"],
            },
            minutes=60,
        )
        await self.audit.record(
            tenant_id=tenant_id,
            user_id=actor["id"],
            entity="tenants",
            entity_id=tenant_id,
            action="support_access",
        )
        return {"access_token": token, "tenant": tenant}
