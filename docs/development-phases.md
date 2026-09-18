# Development phases

Implemented as a modular monolith. Each phase is represented in backend services, APIs, UI, and tests.

| Phase | Scope |
|------|--------|
| 0 | Discovery, audit, docs |
| 1 | UI design system / tokens / shell components |
| 2 | Backend foundation (FastAPI, MongoDB, auth, tenant context) |
| 3 | Platform super admin |
| 4 | Tenant settings |
| 5–6 | Locations, hubs, configurable indoor routes |
| 6 | Vehicles, documents, maintenance, temporary vehicles |
| 7 | Drivers, employees, advances (ledger) |
| 8 | Parties, autocomplete, party ledger |
| 9 | Trips (indoor/outdoor, lifecycle) |
| 10 | LR, templates, print/PDF HTML |
| 11 | Fuel pumps and ledger |
| 12 | 3PL partners, trips, ledger |
| 13 | Expenses |
| 14–16 | Finance, Deewanji collections/handover, owner dashboard |
| 17 | Reports and export (CSV/Excel/PDF/print) |
| 18 | Notifications |
| 19 | Mobile/PWA, bottom nav, quick create |
| 20 | Security (tenant isolation, rate limit, headers, CORS) |
| 21 | Tests |
| 22 | Indexes, pagination, lazy routes |
| 23 | Docker, reverse proxy |
| 24 | Documentation |
