#!/usr/bin/env bash
# Nexventory — production deploy script (run on EC2 after git pull)
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
ENV_FILE="${ENV_FILE:-.env.prod}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

cd "$DEPLOY_DIR"

echo "==> Deploying Nexventory in $DEPLOY_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Copy .env.prod.example to .env.prod on the server."
  exit 1
fi

echo "==> Pulling latest code"
git pull origin main

if [[ -f frontend/package.json ]]; then
  echo "==> Building React UI (served at /app/)"
  (cd frontend && npm ci && npm run build)
  if [[ ! -f frontend/dist/index.html ]]; then
    echo "ERROR: frontend/dist/index.html missing after build."
    exit 1
  fi
fi

echo "==> Building and starting containers"
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES up -d --build --remove-orphans

echo "==> Service status"
docker compose --env-file "$ENV_FILE" $COMPOSE_FILES ps

echo "==> Health check (via nginx)"
sleep 5
curl -sf "http://localhost/health/ready" && echo ""
curl -sf "http://localhost/health" && echo ""

echo "==> Deploy complete"
