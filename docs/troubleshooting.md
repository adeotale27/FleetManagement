# Troubleshooting

- API will not start: check `MONGODB_URL` and that Mongo is reachable (`/api/v1/health/db`).
- Login fails: confirm seed user or that the tenant is `active`.
- Empty lists: confirm JWT tenant_id and permission.
- Frontend API 404: in dev, Vite proxies `/api` to `:8000`.
- bcrypt errors: reinstall `backend/requirements.txt` in a fresh venv.
