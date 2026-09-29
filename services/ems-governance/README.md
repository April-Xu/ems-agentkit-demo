# EMS demo MCP and governance backend

This container exposes a Streamable HTTP MCP endpoint at `/mcp`, a health probe
at `/health`, and reviewer/worker-only demo HTTP routes. The deployed AgentKit
Gateway publishes only `/mcp`; the other routes are for a local demo process and
are not reachable through the public Gateway. It loads the synthetic Base export
in `data/feishu/` and defaults to mock SimplyBook behavior.

The Agent-facing MCP tool list contains reads, temporary Grant requests, and
Change Set preview/freeze/approval submission. It has no booking, cancellation,
email, or Impact Key write tool. Grant reviewer, Change Set reviewer, and
Worker routes use separate bearer secrets and are not MCP tools. Worker execution always returns
`MOCK_ONLY_NOT_SENT`; it never writes to SimplyBook or Impact Key.

The SQLite state file is local to one process. Use one replica for this demo.
Local and cloud containers have separate databases. Restarting a container resets
active demo state if the file is ephemeral.
Do not use this service as a production governance system.

For local startup, deployment and manual endpoint examples, see
[`docs/DEPLOYMENT.md`](../../docs/DEPLOYMENT.md).
