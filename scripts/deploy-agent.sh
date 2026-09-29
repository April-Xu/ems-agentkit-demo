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

# AgentKit may recreate a Runtime after an Error state without writing the new
# runtime_id back into the local YAML. Resolve this demo's fixed name before
# every launch so retries update the current Runtime instead of targeting a
# stale ID or creating a duplicate name.
if [[ "$agent_name" == "schedule-checker" ]]; then
  runtime_name="ems-iw-demo-schedule-checker"
else
  runtime_name="ems-iw-demo-orchestrator"
fi
existing_runtime_id="$(agentkit runtime list --region cn-beijing --json | python3 -c '
import json, sys
name = sys.argv[1]
for runtime in json.load(sys.stdin):
    if runtime.get("name") == name:
        print(runtime.get("runtimeId", ""))
        break
' "$runtime_name")"
if [[ -n "$existing_runtime_id" ]]; then
  python3 - "$deploy_dir/agentkit.yaml" "$existing_runtime_id" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
runtime_id = sys.argv[2]
text = path.read_text(encoding="utf-8")
updated, count = re.subn(
    r"(?m)^(\s+runtime_id:\s*).*$",
    lambda match: match.group(1) + runtime_id,
    text,
    count=1,
)
if count != 1:
    raise SystemExit("Could not locate launch_types.cloud.runtime_id in agentkit.yaml")
path.write_text(updated, encoding="utf-8")
PY
fi

# Resolve ${ENV_VAR} placeholders in the ignored deployment copy. The deployed
# runtime needs literal values; source YAML keeps secrets out of GitHub.
python3 - "$deploy_dir/agentkit.yaml" "$agent_name" <<'PY'
from pathlib import Path
import json
import os
import re
import sys

path = Path(sys.argv[1])
agent_name = sys.argv[2]
keys = (
    "MODEL_AGENT_NAME",
    "MODEL_ENDPOINT",
    "EMS_SCHEDULE_CHECKER_PUBLIC_URL",
) if agent_name == "schedule-checker" else (
    "MODEL_AGENT_NAME",
    "MODEL_ENDPOINT",
    "EMS_DEMO_MCP_URL",
    "EMS_DEMO_MCP_AUTH_KEY",
    "EMS_SCHEDULE_CHECKER_AGENT_CARD_URL",
    "EMS_SCHEDULE_CHECKER_A2A_AUTH_KEY",
)
text = path.read_text(encoding="utf-8")
for key in keys:
    value = os.environ.get(key)
    if not value:
        continue
    pattern = re.compile(rf"(?m)^(\s+{re.escape(key)}:\s*).*$")
    text, count = pattern.subn(lambda match: match.group(1) + json.dumps(value), text, count=1)
    if count != 1:
        raise SystemExit(f"Could not resolve runtime env {key} in agentkit.yaml")
path.write_text(text, encoding="utf-8")
PY

cd "$deploy_dir"
agentkit launch --config-file agentkit.yaml
