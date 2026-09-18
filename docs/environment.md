# Environment

`LOGIN=hidden` (default for now) skips the login form and shows Platform / Business owner / Deewanji. Set `LOGIN=required` and `VITE_LOGIN=required` to restore sign-in.

Copy `.env.example` to `.env`. Never commit secrets.

Required: `MONGODB_URL`, `MONGODB_DATABASE`, `JWT_SECRET`, `CORS_ORIGINS`.

`RUN_SEED=true` only with `APP_ENV=development`. If Mongo is down and login is hidden, the API uses an in-memory store so the owner UI still runs.
