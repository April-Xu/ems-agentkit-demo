#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
agent_name="${1:-}"
if [[ "$agent_name" != "schedule-checker" && "$agent_name" != "orchestrator" ]]; then
  echo "Usage: $0 schedule-checker|orchestrator" >&2
  exit 2
fi

if [[ -f "$repo_root/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$repo_root/.env"
  set +a
fi

if ! command -v agentkit >/dev/null 2>&1; then
  echo "Install AgentKit CLI first: https://docs.volcengine.com/docs/AgentKit/Creating_runtime_via_CLI_tool?lang=en" >&2
  exit 1
fi
if ! agentkit whoami --no-auto-login >/dev/null 2>&1; then
  echo "Sign in first with: agentkit login --console --provider volcengine" >&2
  exit 1
fi

if [[ "$agent_name" == "orchestrator" ]]; then
  for key in EMS_DEMO_MCP_URL EMS_DEMO_MCP_AUTH_KEY \
    EMS_SCHEDULE_CHECKER_AGENT_CARD_URL EMS_SCHEDULE_CHECKER_A2A_AUTH_KEY; do
    if [[ -z "${!key:-}" ]]; then
      echo "Set $key in .env before deploying the orchestrator." >&2
      exit 1
    fi
  done
fi

source_dir="$repo_root/agents/$agent_name"
deploy_dir="$repo_root/.deploy/$agent_name"
mkdir -p "$deploy_dir"
cp "$source_dir"/*.py "$source_dir"/requirements.txt "$source_dir"/.dockerignore "$deploy_dir"/
if [[ ! -f "$deploy_dir/agentkit.yaml" ]]; then
  cp "$source_dir/agentkit.yaml" "$deploy_dir/agentkit.yaml"
fi

cd "$deploy_dir"
agentkit launch --config-file agentkit.yaml
