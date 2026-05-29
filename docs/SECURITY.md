# API security hardening (Week 3)

## New dependency

```text
slowapi==0.1.9
```

Rebuild the API image after pulling: `docker compose ... up -d --build api`

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Short-lived JWT for API calls |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `RATE_LIMIT_DEFAULT` | `60/minute` | Global API limit per IP |
| `RATE_LIMIT_LOGIN` | `5/minute` | `/token` |
| `RATE_LIMIT_REGISTER` | `10/minute` | `/register` |
| `RATE_LIMIT_REFRESH` | `10/minute` | `/token/refresh` |
| `RATE_LIMIT_AUDIT` | `30/minute` | `/audit-logs` |
| `LOGIN_MAX_ATTEMPTS` | `5` | Failures before lockout |
| `LOGIN_LOCKOUT_MINUTES` | `15` | Lockout duration |

## JWT refresh flow

1. `POST /token` → `{ access_token, refresh_token, expires_in }`
2. Call APIs with `Authorization: Bearer <access_token>`
3. When access expires → `POST /token/refresh` with `{ "refresh_token": "..." }`
4. Use new pair; old refresh token should be discarded client-side

Refresh tokens include `typ: refresh` and are rejected on protected routes.

## Swagger /docs blank page

If `/docs` is blank but `/openapi.json` returns 200, the API is fine — the browser blocked
Swagger UI scripts due to `Content-Security-Policy: default-src 'none'`. Documentation paths
now use a relaxed CSP (see `app/middleware/security_headers.py`).

## Testing in Swagger

1. Register with strong password: `Admin123!`
2. Login via `/token` — copy `access_token` and `refresh_token`
3. Authorize with access token
4. Call `/audit-logs`, `/devices`, etc.
5. `/token/refresh` with JSON body `{ "refresh_token": "..." }`
6. Use expired/wrong token → `401` + `INVALID_TOKEN` in audit logs
7. Hit `/token` 6+ times with wrong password → `429` lockout + `LOGIN_LOCKOUT` audit

## Rate limit test (Postman/curl)

```bash
for i in {1..10}; do curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost/token -d "username=x&password=y"; done
```

Expect `429` after the configured login limit.
