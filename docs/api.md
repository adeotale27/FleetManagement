# API

Base: `/api/v1`

Auth: `Authorization: Bearer <jwt>`

Standard success: `{ "success": true, "data": ... }`  
Standard error: `{ "success": false, "error": { "code", "message" } }`

Listings: `{ items, total, page, limit, has_next }`

## Core

- POST `/auth/login`
- GET `/auth/me`
- GET `/health` GET `/health/db`
- GET `/dashboard/owner`
- GET `/search?q=`
- CRUD `/{resource}` for locations, routes, vehicles, drivers, employees, parties, trips, lrs, fuel-providers, partners, expenses, collections, templates, notifications
- POST `/trips` POST `/trips/{id}/status`
- POST `/lrs` GET `/lrs/{id}/print`
- POST `/finance/collections` `/finance/handovers` `/finance/expenses` `/finance/advances`
- GET `/finance/ledger/{type}/{id}` GET `/finance/receivables`
- GET `/reports/{name}` `?format=csv`
- Platform: `/platform/tenants`, `/platform/overview`, `/platform/audit`, support-access
