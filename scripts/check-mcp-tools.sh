#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$repo_root/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$repo_root/.env"
  set +a
fi

if [[ -z "${EMS_DEMO_MCP_URL:-}" || -z "${EMS_DEMO_MCP_AUTH_KEY:-}" ]]; then
  echo "Set EMS_DEMO_MCP_URL and EMS_DEMO_MCP_AUTH_KEY in .env first." >&2
  exit 1
fi
python_bin="$repo_root/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
  fi
  uv venv --python 3.12 "$repo_root/.venv"
fi
uv pip install --python "$python_bin" -r "$repo_root/services/ems-governance/requirements.txt" >/dev/null

"$python_bin" - <<'PY'
import asyncio
import os
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    headers = {"Authorization": f"Bearer {os.environ['EMS_DEMO_MCP_AUTH_KEY']}"}
    async with streamablehttp_client(os.environ["EMS_DEMO_MCP_URL"], headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            names = sorted(tool.name for tool in result.tools)
            if not names:
                raise SystemExit("MCP endpoint connected but returned no tools")
            print("MCP tools ({}): {}".format(len(names), ", ".join(names)))

asyncio.run(main())
PY
