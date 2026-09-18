from typing import Annotated, Any
from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.permissions import has_permission
from app.core.security import decode_token
from app.db.mongo import get_db
from app.repositories.base import serialize

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    x_idempotency_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not creds:
        raise UnauthorizedError("Authentication required")
    try:
        payload = decode_token(creds.credentials)
    except ValueError as exc:
        raise UnauthorizedError("Invalid token") from exc
    db = get_db()
    user = await db["users"].find_one({"_id": payload.get("sub"), "is_deleted": {"$ne": True}})
    if not user and payload.get("support"):
        user = {
            "_id": payload.get("sub"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions") or [],
            "tenant_id": payload.get("tenant_id"),
            "name": "Support",
            "email": "support@platform",
            "status": "active",
        }
    if not user or user.get("status") not in {None, "active"}:
        raise UnauthorizedError("User not found")
    tenant_id = payload.get("tenant_id") or user.get("tenant_id")
    tenant = None
    if tenant_id:
        tenant = serialize(await db["tenants"].find_one({"_id": tenant_id}))
    request.state.tenant_id = tenant_id
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": payload.get("role") or user.get("role"),
        "permissions": payload.get("permissions") or user.get("permissions") or [],
        "tenant_id": tenant_id,
        "tenant": tenant,
        "support": bool(payload.get("support")),
        "idempotency_key": x_idempotency_key,
        "ip": request.client.host if request.client else None,
    }


def require_permission(permission: str):
    async def _inner(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if not has_permission(user.get("permissions") or [], permission):
            raise ForbiddenError("You do not have permission for this action")
        return user

    return _inner


def require_tenant(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if not user.get("tenant_id"):
        raise ForbiddenError("Tenant context required")
    return user
