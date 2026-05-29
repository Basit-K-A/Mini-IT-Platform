# Security monitoring dashboard (Week 4)

## New table

`alerts` — created on API startup via `Base.metadata.create_all()`.

## Dashboard endpoints (JWT + admin/analyst)

| Endpoint | Purpose |
|----------|---------|
| `GET /dashboard/overview` | KPI cards + runs analysis |
| `GET /dashboard/security-summary` | Severity charts |
| `GET /dashboard/recent-alerts` | Alert table |
| `GET /dashboard/failed-logins` | Brute-force visibility |
| `GET /dashboard/top-active-users` | User activity |
| `GET /dashboard/top-ip-addresses` | Suspicious IPs |
| `GET /dashboard/recent-audit-logs` | Audit feed |
| `GET /dashboard/recent-events` | Infrastructure events |

## Detection rules

| Rule | Alert type | Default threshold |
|------|------------|-------------------|
| Failed logins per IP | `POSSIBLE_BRUTE_FORCE` | 5 / hour |
| Permission denied per IP | `REPEATED_PERMISSION_DENIED` | 5 / hour |
| Rate limits per IP | `EXCESSIVE_API_USAGE` | 10 / hour |
| Account lockouts | `SUSPICIOUS_AUTH_BEHAVIOR` | any in 24h |
| Critical events | `HIGH_SEVERITY_EVENT` | recent critical |

Env overrides: `ALERT_FAILED_LOGIN_IP_THRESHOLD`, `ALERT_DEDUP_MINUTES`, etc.

## Testing

1. Rebuild API: `docker compose ... up -d --build api`
2. Promote user to `admin` or `analyst`
3. Trigger 5+ failed logins: `POST /token` with wrong password
4. `GET /dashboard/overview` with Bearer token
5. `GET /dashboard/recent-alerts` — expect `POSSIBLE_BRUTE_FORCE`

```sql
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```
