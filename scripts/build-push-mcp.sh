#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$repo_root/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$repo_root/.env"
  set +a
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to build and push the MCP backend image." >&2
  exit 1
fi
if [[ -z "${EMS_MCP_IMAGE:-}" ]]; then
  echo "Set EMS_MCP_IMAGE in .env to your Volcengine Container Registry image URL." >&2
  exit 1
fi

docker buildx build \
  --platform linux/amd64 \
  --file "$repo_root/services/ems-governance/Dockerfile" \
  --tag "$EMS_MCP_IMAGE" \
  --push \
  "$repo_root"

echo "Pushed MCP backend image: $EMS_MCP_IMAGE"
