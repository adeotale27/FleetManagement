class EntitlementService:
    def __init__(self, tenant: dict | None):
        self.tenant = tenant or {}
        self.flags = (tenant or {}).get("feature_flags") or {}
        self.limits = (tenant or {}).get("limits") or {}

    def enabled(self, feature: str) -> bool:
        if feature not in self.flags:
            return True
        return bool(self.flags[feature])
