#!/usr/bin/env bash
# Build the React app (if Node is available) or verify frontend/dist exists, then reload nginx.
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
ENV_FILE="${ENV_FILE:-.env.prod}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

cd "$DEPLOY_DIR"

echo "==> Deploying frontend (served at /app/)"

RELOAD_ONLY=false
if [[ "${1:-}" == "--reload-only" ]]; then
  RELOAD_ONLY=true
fi

if [[ "$RELOAD_ONLY" == true ]]; then
  echo "==> Reload only (dist uploaded by CI)"
elif [[ -f frontend/package.json ]] && command -v npm >/dev/null 2>&1; then
  echo "==> Building on server with npm"
  (cd frontend && npm ci && npm run build)
elif [[ -f frontend/dist/index.html ]]; then
  echo "==> Using existing frontend/dist (uploaded by CI or prior build)"
else
  echo "ERROR: frontend/dist/index.html not found and npm is unavailable."
  echo "       Run the deploy-frontend GitHub Actions job or: cd frontend && npm ci && npm run build"
  exit 1
fi

if [[ ! -f frontend/dist/index.html ]]; then
  echo "ERROR: frontend/dist/index.html missing after build."
  exit 1
fi

echo "==> Reloading nginx to pick up static files"
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES up -d --force-recreate nginx

if curl -sf -o /dev/null "http://localhost/app/"; then
  echo "==> Frontend OK at http://localhost/app/"
else
  echo "WARN: Could not fetch http://localhost/app/ — check nginx logs."
fi

echo "==> Frontend deploy complete"
