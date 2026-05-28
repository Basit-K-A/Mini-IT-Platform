# Nexventory — Docker & infrastructure guide

This document explains how the multi-container setup works and how to operate it on Windows (Docker Desktop) or Linux.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Host                                                         │
│  localhost:80  ──► nexventory_nginx ──► nexventory_api:8000  │
│  localhost:5432 ──► nexventory_db  (dev profile only)        │
│  localhost:8000 ──► api direct      (dev profile only)       │
└──────────────────────────────────────────────────────────────┘
                        nexventory_backend (bridge)
              nginx ──► api ──► db:5432
```

Reverse proxy details: **[NGINX.md](NGINX.md)**

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base stack: `nginx` + `api` + `db`, network, volume, health checks |
| `docker-compose.dev.yml` | Dev: publish DB port, bind-mount `app/`, `uvicorn --reload` |
| `docker-compose.prod.yml` | Prod-like: no DB on host, `restart: always`, no reload |
| `Dockerfile` | API image: slim Python, non-root user, image health check |
| `.dockerignore` | Keeps secrets, `frontend/`, `.venv` out of build context |

## Commands

### Development (recommended on Windows)

```powershell
copy .env.dev.example .env.dev
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Production-like (detached)

```powershell
copy .env.prod.example .env.prod
# Edit .env.prod — strong POSTGRES_PASSWORD and SECRET_KEY
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### Quick start (base compose + `.env`)

```powershell
copy .env.example .env
docker compose --env-file .env up --build
```

### Stop / restart / logs

```powershell
# Stop containers, keep database volume
docker compose down

# Stop and DELETE database data
docker compose down -v

# Restart one service
docker compose restart api

# Follow logs
docker compose logs -f api
docker compose logs -f db

# Container health status
docker compose ps
```

## Health checks

| Endpoint | Meaning |
|----------|---------|
| `GET /health` | Liveness — API process is running |
| `GET /health/ready` | Readiness — API can reach PostgreSQL |

Compose waits for `db` to be healthy before starting `api`. The `api` service health check calls `/health/ready` inside the container.

Test from your host (via nginx):

```powershell
curl http://localhost/health
curl http://localhost/health/ready
```

Swagger: http://localhost/docs (dev direct API: http://localhost:8000/docs)

## Environment variables

| Variable | Used by | Notes |
|----------|---------|-------|
| `POSTGRES_*` | `db` container | Creates database on first volume init |
| `DATABASE_URL` | `api` | **In Compose, host must be `db`**, not `localhost` |
| `SECRET_KEY` | `api` | JWT signing — use a long random value in prod |
| `CORS_ORIGINS` | `api` | Comma-separated browser origins |
| `API_PORT` | Compose | Host port mapped to api `:8000` |
| `POSTGRES_PORT` | Dev only | Publishes DB to host for pgAdmin / psql |

### Why `localhost` changes inside Docker

- **On your Windows machine**, `localhost` is your PC. PostgreSQL on port 5432 is reachable if the `db` service publishes that port (dev profile).
- **Inside the `api` container**, `localhost` is the container itself, not the database container. The DB runs in a separate container.
- Compose creates a **bridge network** (`nexventory_backend`). Each service is reachable by its **service name** as DNS: `db`, `api`.
- Therefore `DATABASE_URL` for the API must use `@db:5432`.

### Managing secrets

- Commit only `*.example` files.
- Copy to `.env`, `.env.dev`, or `.env.prod` locally (gitignored).
- On AWS/Oracle Cloud later: use parameter store / secrets manager instead of files on disk.

## Infrastructure concepts

### Container networking

Containers on the same Compose project share a virtual network. They get private IPs and can resolve each other by service name. Traffic between `api` and `db` never needs to leave the Docker network.

### Bridge networks

`driver: bridge` is the default. Your host can reach published ports (`8000:8000`). Unpublished services (prod `db`) are only reachable from other containers on that network.

### Docker volumes

`postgres_data` → `/var/lib/postgresql/data` in the DB container. Data survives `docker compose down`. It is removed only with `docker compose down -v` or `docker volume rm nexventory_postgres_data`.

### Restart policies

- `unless-stopped` (base): restart on failure unless you stopped the container manually.
- `always` (prod override): restart even after Docker daemon reboot.

### Exposed ports vs internal ports

- **Internal**: `db:5432` — always available to `api` on the backend network.
- **Published**: `5432:5432` on host — only in **dev** for tools on your machine. Omit in prod so the database is not exposed to your LAN/internet.

### Container lifecycle

1. `docker compose up` — create network/volume, start `db`, wait for health, start `api`.
2. `docker compose stop` — stop containers, keep volumes.
3. `docker compose down` — remove containers, keep volumes.
4. `docker compose down -v` — also remove volumes (**wipes DB**).

## Verify PostgreSQL persistence

```powershell
# 1. Start stack and register a user via /docs
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d

# 2. Stop without removing volume
docker compose down

# 3. Start again
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d

# 4. Log in again — user should still exist
```

Inspect the volume:

```powershell
docker volume inspect nexventory_postgres_data
```

## Test checklist

1. `docker compose ps` — `db`, `api`, and `nginx` are `healthy`
2. http://localhost/health/ready → `{"status":"ok","database":"connected"}`
3. http://localhost/docs — Swagger loads via nginx
4. `POST /register` + `POST /token` — auth works
5. Dev: edit `app/main.py`, save — API reloads (dev profile only)

## Cloud deployment

1. Run Compose with **prod** files; publish only nginx `80`/`443`.
2. Terminate TLS at nginx — see [NGINX.md](NGINX.md).
3. Serve the React `frontend` static build from nginx or a separate container.
4. Set `CORS_ORIGINS` to your real HTTPS origin.

**Cloud deployment path:** build and push the API image to ECR/OCIR → run Compose or a single VM with managed RDS instead of containerized Postgres → secrets from AWS SSM / OCI Vault.

## Suggested next improvements

1. **Alembic migrations** — replace `create_all()` for schema changes in production.
2. **Frontend** behind nginx (see `frontend/Dockerfile`; add `location /` or subdomain).
3. **CI pipeline** — `docker build` + smoke test against `/health/ready`.
4. **Managed PostgreSQL** (RDS) — point `DATABASE_URL` at external host; remove `db` service.
5. **Structured logging** (JSON) for CloudWatch / centralized logs.
6. **Resource limits** in Compose (`mem_limit`, `cpus`) for production hosts.
