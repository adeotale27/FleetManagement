# Database

Shared MongoDB database. Tenant documents always include `tenant_id`.

## Collections

tenants, users, locations, routes, vehicles, vehicle_documents, vehicle_maintenance, drivers, employees, parties, trips, lrs, fuel_providers, fuel_entries, partners, partner_trips, expenses, ledger_entries, collections, handovers, notifications, audit_logs, sequences, files, templates.

## Ledger model

`ledger_entries`: account_type, account_id, debit, credit, ref_type, ref_id, voided, idempotency_key.

Party outstanding = sum(debit) − sum(credit) for `account_type=party`.

Cash/bank: debit increases balance, credit decreases.

## Indexes

See `backend/app/db/indexes.py`. Indexes exist for tenant-scoped lookups (vehicle_number, trip_number, lr_number, party mobile, ledger account, dates).
