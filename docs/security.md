# Security

- Passwords hashed with bcrypt
- JWT secret from env
- Tenant scope enforced in repositories
- Permission strings (not role string checks in features)
- Support impersonation audited
- CORS allowlist from env
- Security headers middleware
- Soft-delete for masters; ledger void instead of delete
- Do not commit `.env`
- Production hides internal exception text
