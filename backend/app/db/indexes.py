INDEXES: dict[str, list[list[tuple]]] = {
    "tenants": [[("status", 1)], [("slug", 1)]],
    "users": [
        [("tenant_id", 1), ("email", 1)],
        [("tenant_id", 1), ("mobile", 1)],
        [("email", 1)],
    ],
    "locations": [[("tenant_id", 1), ("name", 1)], [("tenant_id", 1), ("status", 1)]],
    "routes": [[("tenant_id", 1), ("status", 1)]],
    "vehicles": [
        [("tenant_id", 1), ("vehicle_number", 1)],
        [("tenant_id", 1), ("status", 1)],
    ],
    "vehicle_documents": [[("tenant_id", 1), ("vehicle_id", 1)], [("tenant_id", 1), ("expiry_date", 1)]],
    "vehicle_maintenance": [[("tenant_id", 1), ("vehicle_id", 1), ("date", -1)]],
    "drivers": [[("tenant_id", 1), ("mobile", 1)], [("tenant_id", 1), ("status", 1)]],
    "employees": [[("tenant_id", 1), ("mobile", 1)], [("tenant_id", 1), ("status", 1)]],
    "parties": [[("tenant_id", 1), ("mobile", 1)], [("tenant_id", 1), ("name", 1)]],
    "trips": [
        [("tenant_id", 1), ("trip_number", 1)],
        [("tenant_id", 1), ("status", 1), ("start_at", -1)],
        [("tenant_id", 1), ("vehicle_id", 1)],
        [("tenant_id", 1), ("driver_id", 1)],
    ],
    "lrs": [
        [("tenant_id", 1), ("lr_number", 1)],
        [("tenant_id", 1), ("trip_id", 1)],
        [("tenant_id", 1), ("status", 1), ("date", -1)],
        [("tenant_id", 1), ("sender_id", 1)],
    ],
    "fuel_providers": [[("tenant_id", 1), ("name", 1)]],
    "fuel_entries": [[("tenant_id", 1), ("vehicle_id", 1), ("date", -1)]],
    "partners": [[("tenant_id", 1), ("name", 1)]],
    "partner_trips": [[("tenant_id", 1), ("partner_id", 1)]],
    "expenses": [[("tenant_id", 1), ("date", -1)], [("tenant_id", 1), ("category", 1)]],
    "ledger_entries": [
        [("tenant_id", 1), ("account_type", 1), ("account_id", 1), ("created_at", -1)],
        [("tenant_id", 1), ("ref_type", 1), ("ref_id", 1)],
        [("tenant_id", 1), ("idempotency_key", 1)],
    ],
    "collections": [[("tenant_id", 1), ("collected_by", 1), ("date", -1)]],
    "handovers": [[("tenant_id", 1), ("deewanji_id", 1), ("date", -1)]],
    "notifications": [[("tenant_id", 1), ("user_id", 1), ("created_at", -1)]],
    "audit_logs": [[("tenant_id", 1), ("created_at", -1)], [("entity", 1), ("entity_id", 1)]],
    "sequences": [[("tenant_id", 1), ("key", 1)]],
    "files": [[("tenant_id", 1), ("entity", 1), ("entity_id", 1)]],
    "templates": [[("tenant_id", 1), ("template_type", 1), ("version", -1)]],
}


async def ensure_indexes(db) -> None:
    for collection, specs in INDEXES.items():
        for keys in specs:
            unique = collection == "sequences" and keys == [("tenant_id", 1), ("key", 1)]
            await db[collection].create_index(keys, unique=unique)
