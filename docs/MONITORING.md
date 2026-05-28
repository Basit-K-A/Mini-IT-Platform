# Monitoring and logging

Beginner-friendly visibility for Nexventory: application logs, Docker logs, health endpoints, and basic resource checks.

## Health endpoints

| Endpoint | Checks | Use for |
|----------|--------|---------|
| `GET /health` | API process running | Liveness (nginx, Docker, uptime tools) |
| `GET /health/ready` | API + PostgreSQL | Readiness before sending traffic |

**Via nginx (production path):**

```bash
curl http://localhost/health
curl http://localhost/health/ready
```

Example liveness response:

```json
{
  "status": "ok",
  "service": "nexventory-api",
  "environment": "production"
}
```

Docker Compose already uses these for container health checks.

## Application logging

Configured in `app/logging_config.py` and `app/middleware/request_logging.py`.

| Setting | Default | Effect |
|---------|---------|--------|
| `ENVIRONMENT` | `development` | `production` → JSON logs |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `WARNING`, etc. |

**Development** (human-readable):

```text
2026-05-28 12:00:00 | INFO     | nexventory.access | request_completed method=GET path=/devices status=200 duration_ms=12.34
```

**Production** (JSON, one line per event):

```json
{"timestamp": "2026-05-28T12:00:00+00:00", "level": "INFO", "logger": "nexventory.access", "message": "request_completed method=GET path=/devices status=200 duration_ms=12.34"}
```

Health probe paths (`/health`, `/health/ready`) are not logged on every request to reduce noise.

### View API logs

```bash
# Follow API logs
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api

# All services
docker compose logs -f
```

On EC2 with prod files:

```bash
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml logs -f api
```

### Nginx logs

```bash
docker compose exec nginx tail -f /var/log/nginx/nexventory.access.log
docker compose exec nginx tail -f /var/log/nginx/nexventory.error.log
```

## Docker monitoring commands

```bash
# Container status and health
docker compose ps

# Live CPU / memory / network
docker stats

# Inspect one container
docker inspect nexventory_api --format '{{.State.Health.Status}}'
```

### Log rotation (production compose)

`docker-compose.prod.yml` sets json-file logging with `max-size: 10m` and `max-file: 3` per service so disks do not fill up.

## Simple monitoring workflow

1. **After deploy** — `curl http://YOUR_HOST/health/ready` (expect HTTP 200).
2. **Daily / on alert** — `docker compose ps` (all `healthy`).
3. **On errors** — `docker compose logs --tail=200 api nginx`.
4. **Under load** — `docker stats` (watch API/DB memory).

## Optional helper script

On the server:

```bash
./scripts/monitor.sh
```

Runs `docker compose ps`, hits `/health/ready`, and shows recent API log lines.

## Future upgrades (not in scope now)

- **UptimeRobot** or **Better Stack** — HTTP check on `/health` every 5 minutes
- **AWS CloudWatch** agent — ship `docker logs` to CloudWatch Logs
- **Prometheus + Grafana** — metrics scraping
- **Sentry** — error tracking for Python exceptions

For a student/portfolio project, health checks + `docker logs` + `docker stats` are enough to demonstrate operational awareness.
