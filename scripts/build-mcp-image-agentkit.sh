#!/usr/bin/env bash
set -euo pipefail
umask 077

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="$repo_root/.deploy/mcp-image"
mkdir -p "$build_dir"
chmod 700 "$repo_root/.deploy" "$build_dir"
cp "$repo_root/services/ems-governance/server.py" \
  "$repo_root/services/ems-governance/requirements.txt" \
  "$build_dir/"
cp -R "$repo_root/data/feishu" "$build_dir/data"
cp "$repo_root/services/ems-governance/Dockerfile.agentkit" "$build_dir/Dockerfile"
cp "$repo_root/services/ems-governance/agentkit-build.yaml" "$build_dir/agentkit.yaml"
chmod 600 "$build_dir/server.py" "$build_dir/requirements.txt" \
  "$build_dir/Dockerfile" "$build_dir/agentkit.yaml"

if ! command -v agentkit >/dev/null 2>&1; then
  echo "Install AgentKit CLI first: https://docs.volcengine.com/docs/AgentKit/Creating_runtime_via_CLI_tool?lang=en" >&2
  exit 1
fi
if ! agentkit whoami --no-auto-login --provider volcengine >/dev/null 2>&1; then
  echo "Sign in first with: agentkit login --console --provider volcengine" >&2
  exit 1
fi

(
  cd "$build_dir"
  agentkit build --config-file agentkit.yaml
)

image_url="$(python3 - "$build_dir/agentkit.yaml" <<'PY'
from pathlib import Path
import re
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(r"(?m)^\s+cr_image_full_url:\s*(\S+)\s*$", text)
if not match:
    raise SystemExit("AgentKit build completed without writing cr_image_full_url")
print(match.group(1))
PY
)"
if [[ -f "$repo_root/.env" ]]; then
  python3 - "$repo_root/.env" "$image_url" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
value = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()
replacement = f"EMS_MCP_IMAGE={value}"
indices = [i for i, line in enumerate(lines) if line.startswith("EMS_MCP_IMAGE=")]
if indices:
    lines[indices[0]] = replacement
    for i in reversed(indices[1:]):
        del lines[i]
else:
    lines.append(replacement)
path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
path.chmod(0o600)
PY
fi
find "$build_dir" -type d -exec chmod 700 {} +
find "$build_dir" -type f -exec chmod 600 {} +
echo "MCP image built and pushed through AgentKit cloud build."
