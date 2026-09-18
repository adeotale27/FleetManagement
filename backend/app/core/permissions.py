PLATFORM_PERMISSIONS = [
    "platform:tenants",
    "platform:users",
    "platform:audit",
    "platform:health",
    "platform:support",
    "platform:plans",
]

RESOURCE_ACTIONS = ["create", "read", "update", "delete", "export", "approve"]
RESOURCES = [
    "dashboard",
    "vehicle",
    "driver",
    "employee",
    "party",
    "location",
    "route",
    "trip",
    "lr",
    "fuel",
    "partner",
    "expense",
    "finance",
    "collection",
    "report",
    "settings",
    "template",
    "notification",
    "document",
]


def all_tenant_permissions() -> list[str]:
    perms: list[str] = []
    for resource in RESOURCES:
        for action in RESOURCE_ACTIONS:
            perms.append(f"{resource}:{action}")
    return perms


ROLE_PERMISSIONS: dict[str, list[str]] = {
    "PLATFORM_SUPER_ADMIN": PLATFORM_PERMISSIONS,
    "TENANT_OWNER": all_tenant_permissions(),
    "MANAGER": [
        p
        for p in all_tenant_permissions()
        if not p.startswith("settings:delete") and "approve" not in p
    ],
    "DEEWANJI": [
        "dashboard:read",
        "party:read",
        "trip:read",
        "lr:read",
        "collection:create",
        "collection:read",
        "finance:read",
        "notification:read",
    ],
    "OPERATIONS_USER": [
        "dashboard:read",
        "vehicle:read",
        "vehicle:update",
        "driver:read",
        "party:read",
        "party:create",
        "location:read",
        "route:read",
        "trip:create",
        "trip:read",
        "trip:update",
        "lr:create",
        "lr:read",
        "lr:update",
        "fuel:create",
        "fuel:read",
        "expense:create",
        "expense:read",
        "notification:read",
    ],
    "ACCOUNTANT": [
        "dashboard:read",
        "party:read",
        "lr:read",
        "finance:read",
        "finance:create",
        "finance:export",
        "collection:read",
        "collection:create",
        "expense:read",
        "expense:create",
        "report:read",
        "report:export",
        "employee:read",
        "driver:read",
    ],
    "DRIVER": [
        "dashboard:read",
        "trip:read",
        "lr:read",
        "notification:read",
    ],
    "EMPLOYEE": ["dashboard:read", "notification:read"],
    "CUSTOM_ROLE": ["dashboard:read"],
}


def has_permission(user_permissions: list[str], required: str) -> bool:
    if "*" in user_permissions or required in user_permissions:
        return True
    resource, _, _action = required.partition(":")
    return f"{resource}:*" in user_permissions
