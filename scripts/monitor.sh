#!/usr/bin/env bash
# Quick status check on EC2 or local prod stack
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
ENV_FILE="${ENV_FILE:-.env.prod}"
COMPOSE="docker compose --env-file $ENV_FILE -f docker-compose.yml -f docker-compose.prod.yml"

cd "$DEPLOY_DIR"

echo "==> Container status"
$COMPOSE ps

echo ""
echo "==> Health (nginx)"
curl -sf "http://localhost/health" | head -c 500 && echo ""
curl -sf "http://localhost/health/ready" && echo ""

echo ""
echo "==> Recent API logs (last 20 lines)"
$COMPOSE logs --tail=20 api
