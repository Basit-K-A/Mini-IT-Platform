# Deployment

How Nexventory is built, configured, and deployed — locally with Docker Compose and to a
single AWS EC2 host via GitHub Actions. Deep dives live in
[DOCKER.md](DOCKER.md), [NGINX.md](NGINX.md), [CICD.md](CICD.md), and [EC2_SETUP.md](EC2_SETUP.md);
this is the end-to-end overview.

---

## 1. Topology

```
Internet ─▶ nginx:80 ─┬─▶  /app/   → static React build (mounted from frontend/dist)
                      └─▶  /api/, /docs, /health → api:8000 (uvicorn)
                                                       ├─▶ db:5432   (PostgreSQL)
                                                       └─▶ redis:6379 (cache, optional)
```

Only **nginx** is published to the host. `api`, `db`, and `redis` are reachable only on the
internal Docker network.

---

## 2. Docker (single image)

The API image (`Dockerfile`) is a slim Python 3.12 image running uvicorn as a non-root user,
with a built-in liveness `HEALTHCHECK` against `/health`.

```bash
docker build -t nexventory-api .
docker run --rm -p 8000:8000 --env-file .env nexventory-api
```

> Test dependencies (`requirements-dev.txt`) are intentionally **not** installed into the
> image — it stays production-lean. See [Testing](#7-running-tests).

---

## 3. Docker Compose

The stack is defined in `docker-compose.yml` with environment-specific overlays:

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base stack: nginx + api + db + redis, health checks |
| `docker-compose.dev.yml` | Hot reload, publishes DB `5432` and direct API `8000` |
| `docker-compose.prod.yml` | Detached, only nginx published; DB/api internal |

```bash
# Development (hot reload, direct API + DB exposed)
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production-like (detached, only nginx on the host)
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Common operations:

```bash
docker compose ps                 # health/status of all services
docker compose logs -f api        # follow API logs (JSON in production)
docker compose down               # stop, keep the DB volume
docker compose down -v            # stop and WIPE the DB volume
```

Tables are created on API startup (`Base.metadata.create_all`), and additive column drift on
pre-existing tables is reconciled by `core/schema_guard.ensure_schema` during the lifespan.

---

## 4. Environment variables

Copy the example that matches how you run the stack (`.env.example`, `.env.dev.example`,
`.env.prod.example`). Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL DSN. Inside Compose use host `db` (e.g. `postgresql://postgres:pw@db:5432/mini_it_platform`) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credentials for the `db` service (must match the volume on first init) |
| `SECRET_KEY` | JWT signing secret — generate with `openssl rand -hex 32` |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime (default 15) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh-token lifetime (default 7) |
| `CORS_ORIGINS` | Comma-separated allowed browser origins |
| `ENVIRONMENT` | `development` or `production` — switches plaintext vs JSON logging and error verbosity |
| `LOG_LEVEL` | `INFO` (default), `DEBUG`, ... |
| `REDIS_URL` / `REDIS_ENABLED` | Cache backend; gracefully disabled if unavailable |
| `RATE_LIMIT_*` | Per-route rate limits (login, register, refresh, dashboard, audit) |
| `SLOW_QUERY_MS` / `SLOW_REQUEST_MS` | Thresholds for slow-log warnings |
| `NGINX_PORT` | Host port for the reverse proxy (default 80) |

> **Production note:** set `ENVIRONMENT=production` so logs are emitted as JSON and internal
> error messages are not exposed to clients.

---

## 5. Nginx reverse proxy

Config lives in `deploy/nginx/conf.d/nexventory.conf`. Responsibilities:

- Serve the React SPA under `/app/` from the mounted `frontend/dist` build, with
  `try_files ... /app/index.html` so client-side routes resolve.
- Proxy `/api/`, `/docs`, `/openapi.json`, and `/health*` to `api:8000`, forwarding
  `X-Forwarded-For` / `X-Forwarded-Proto` (uvicorn runs with `--proxy-headers`).
- Redirect `/` → `/app/`.

```bash
# Reload nginx after editing the config (no full restart)
docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload
```

For HTTPS/TLS termination and hardening details, see [NGINX.md](NGINX.md).

---

## 6. AWS deployment workflow (GitHub Actions → EC2)

Pushing to `main` runs `.github/workflows/deploy.yml`:

1. **build** — build and validate the API Docker image.
2. **deploy-backend** — SSH to EC2 and run `scripts/deploy.sh`, which uses
   `scripts/sync-repo.sh` to fast-forward the checkout (`git fetch` + `git reset --hard
   origin/main` + `git clean -fd`) and then `docker compose up -d --build`.
3. **deploy-frontend** — build the React app in CI, `rsync` `frontend/dist` to EC2, then run
   `scripts/deploy-frontend.sh --reload-only` to reload nginx so it serves the new build.

Required **GitHub Secrets**: `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `EC2_DEPLOY_PATH`.

One-time EC2 provisioning (Docker, compose, firewall, first checkout) is in
[EC2_SETUP.md](EC2_SETUP.md). After provisioning:

```bash
cd "$EC2_DEPLOY_PATH"
chmod +x scripts/*.sh
./scripts/deploy.sh
```

Verify after deploy:

```bash
curl http://<EC2_IP>/health/ready     # {"status":"ok","database":"connected", ...}
curl http://<EC2_IP>/api/health        # overall status through nginx
```

---

## 7. Running tests

Tests run against an in-memory SQLite database and do not require the stack to be up.

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest                       # all tests
pytest -m unit               # fast unit tests only
pytest -m integration        # API + DB integration tests
pytest --cov=app --cov-report=term-missing
```

In CI or without a local Python 3.12, run them inside the API image:

```bash
docker run --rm --user root -v "$PWD:/work" -w /work nexventory-api \
  sh -c "pip install -q pytest pytest-cov httpx && pytest --cov=app"
```

See [API.md](API.md) for the endpoint contract and [ARCHITECTURE.md](ARCHITECTURE.md) for how
the pieces fit together.
