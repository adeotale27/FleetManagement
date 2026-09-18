# Environment

Copy `.env.example` to `.env`. Never commit secrets.

Required: `MONGODB_URL`, `MONGODB_DATABASE`, `JWT_SECRET`, `CORS_ORIGINS`.

`RUN_SEED=true` only with `APP_ENV=development`. Seed will not run in production.
