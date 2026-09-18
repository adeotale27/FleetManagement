# Deployment

Docker Compose runs MongoDB, API, and nginx-served SPA.

```bash
cp .env.example .env
docker compose up --build
```

Reverse proxy should terminate HTTPS and forward `/api` to the API container and `/` to the frontend.

Backups: schedule `mongodump` against `MONGODB_URL`. Retain per your RPO; test restore with `mongorestore`.
