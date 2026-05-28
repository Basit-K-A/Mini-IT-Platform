# Nginx reverse proxy

Nginx is the **public entrypoint** for the Nexventory API. Browsers and clients hit port **80** on the host; Nginx forwards requests to the internal `api` service on port 8000.

## Traffic flow

```
Internet / browser
       │
       ▼
  Host :80  (NGINX_PORT)
       │
  nexventory_nginx  ──proxy_pass──►  nexventory_api:8000
       │                                    │
       │                                    ▼
       │                            nexventory_db:5432
       │
  (postgres never exposed in prod)
```

## File layout

| Path | Role |
|------|------|
| `deploy/nginx/conf.d/nexventory.conf` | Upstream, `proxy_pass`, gzip, security headers |
| `deploy/nginx/html/errors/502.html` | Shown when the API is down |
| `deploy/nginx/html/maintenance.html` | Optional static maintenance page |

## Important directives

| Directive | Purpose |
|-----------|---------|
| `upstream nexventory_api` | Defines backend pool; `server api:8000` uses Compose DNS |
| `keepalive 32` | Reuses connections to uvicorn |
| `proxy_pass http://nexventory_api` | Forwards HTTP to FastAPI |
| `proxy_set_header X-Forwarded-*` | Tells FastAPI the real client IP and scheme (http vs https later) |
| `proxy_http_version 1.1` | Required for keepalive and WebSockets |
| `gzip on` | Compresses JSON/text responses |
| `server_tokens off` | Hides nginx version in headers/errors |
| `error_page 502 503` | Serves custom HTML when API is unreachable |

## Run the stack

```powershell
copy .env.dev.example .env.dev
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up --build
```

| URL | Description |
|-----|-------------|
| http://localhost/docs | Swagger (via nginx) |
| http://localhost/health | Liveness |
| http://localhost/health/ready | Readiness (DB + API) |
| http://localhost:8000/docs | Dev only — direct API (bypass nginx) |

## Verify routing

```powershell
# Through nginx (production path)
curl http://localhost/health
curl http://localhost/health/ready

# Response headers show nginx
curl -I http://localhost/docs

# Compare dev direct API (only if docker-compose.dev.yml exposes 8000)
curl http://localhost:8000/health
```

Register/login via Swagger at **http://localhost/docs** — OAuth2 and JWT behave the same; only the hostname/port seen by the browser changes.

## Nginx logs

```powershell
docker compose logs -f nginx
docker compose exec nginx tail -f /var/log/nginx/nexventory.access.log
docker compose exec nginx tail -f /var/log/nginx/nexventory.error.log
```

## Debug networking

| Symptom | Check |
|---------|--------|
| 502 from nginx | `docker compose ps` — is `api` healthy? `docker compose logs api` |
| Connection refused on :80 | Is `nginx` running? Port 80 in use on Windows? Try `NGINX_PORT=8080` |
| Swagger broken assets | Usually wrong URL; use http://localhost/docs not :8000 unless direct |
| CORS errors from React | Add `http://localhost` to `CORS_ORIGINS`; set `VITE_API_URL=http://localhost` |
| API works on :8000 but not :80 | nginx config or `depends_on` — `docker compose logs nginx` |

Test DNS inside nginx container:

```powershell
docker compose exec nginx wget -qO- http://api:8000/health
```

## FastAPI / proxy headers

- **Uvicorn** runs with `--proxy-headers --forwarded-allow-ips *`
- **ProxyHeadersMiddleware** reads `X-Forwarded-For`, `X-Forwarded-Proto`, etc.

This keeps redirects and future HTTPS links correct when TLS terminates at nginx.

## Future HTTPS (not enabled yet)

1. Obtain certificates (Let’s Encrypt / ACM).
2. Add to nginx:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    # ... same location / blocks as port 80 ...
}

server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

3. Mount certs as a read-only volume in Compose.
4. Set `CORS_ORIGINS=https://your-domain.example`.
5. On AWS/Oracle: terminate TLS at ALB **or** on the VM nginx — not both unless you understand double proxy headers.

## Production deployment

- Publish **only** `nginx` ports (80/443).
- Keep `api` and `db` on the internal bridge network (`expose`, not `ports`).
- Point your domain A record to the VM load balancer.
- Add the React `frontend` container or static files as another `location /` or separate subdomain later.

See also [DOCKER.md](DOCKER.md).
