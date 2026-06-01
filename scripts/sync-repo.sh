#!/usr/bin/env bash
# Reset the deploy checkout to match origin/main (no merge conflicts on EC2).
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
BRANCH="${DEPLOY_BRANCH:-main}"

cd "$DEPLOY_DIR"

if [[ ! -d .git ]]; then
  echo "ERROR: $DEPLOY_DIR is not a git repository."
  exit 1
fi

echo "==> Syncing repository to origin/${BRANCH}"
git fetch origin "$BRANCH"
git checkout "$BRANCH" 2>/dev/null || git checkout -B "$BRANCH" "origin/${BRANCH}"
git reset --hard "origin/${BRANCH}"
# Remove untracked files that would block a merge (keeps .gitignore'd files like .env.prod, dist/)
git clean -fd

echo "==> HEAD is now at $(git rev-parse --short HEAD)"
