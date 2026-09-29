# EMS AgentKit Demo

Governed Impact Week event operations using a synthetic Feishu Base export, the customer SimplyBook API contract, AgentKit MCP, a read-only A2A schedule checker, temporary Grants, frozen Change Sets, and a private mock Worker.

This repository contains a deployable **synthetic demo path**. The MCP service reads repository snapshots of the synthetic Feishu Base. Its SimplyBook adapter is mock by default. In the hosted cloud walkthrough, the orchestrator stops when the scoped Grant is `PENDING_APPROVAL`; the complete Change Set and mock Worker flow is only available in a separate local simulation. No live Feishu Base, SimplyBook, Feishu approval, or Impact Key credentials are connected.

## Start here

1. Follow [Deployment](docs/DEPLOYMENT.md) to cloud-build the MCP image, create the AgentKit MCP Gateway, configure its Host allowlist, and deploy the AgentKit Runtimes.
2. Review the [architecture](docs/ARCHITECTURE.md), [demo runbook](docs/DEMO_RUNBOOK.md), [coverage matrix](docs/DEMO_COVERAGE.md), and [assumptions](docs/ASSUMPTIONS_AND_QUESTIONS.md).
3. Open the [synthetic Feishu Base](https://bytedance.larkoffice.com/base/EqKybzfN6apgq2sPztVckxZMnth) and review the customer-provided contracts under `contracts/`.

## What the demo proves

- A separate read-only A2A schedule checker can return duplicate, consent, booking-conflict, and capacity findings.
- AgentKit connects to an MCP endpoint whose allowlist exposes read, Grant request, and Change Set preparation tools, without a business execution tool.
- The governance backend checks event, batch, action scope, row limit, expiry, consent, duplicate candidates, current bookings, and schedule conflicts.
- Change Sets are versioned, frozen, and bound to a stable SHA-256 hash before the separate reviewer step.
- The mock Worker checks Grant, approval state, payload hash, expiry, and idempotency, then returns `MOCK_ONLY_NOT_SENT`.

## Demo boundaries

- `demo.operator` is a configured synthetic principal, not a verified employee identity. AgentKit Runtime authentication is not treated as employee SSO.
- The repository includes a snapshot of the synthetic Feishu Base, not a live Feishu Base connector.
- The SimplyBook MCP adapter maps a small read-only subset of the supplied contract. Mock mode is the default; the live read adapter has not been validated against the customer endpoint.
- The supplied SimplyBook batch-booking API accepts a count and does not map named people to bookings. The demo Worker performs no write.
- Reviewer and Worker HTTP routes are local-only; they use local SQLite state and cannot approve a cloud-issued Grant. They do not create or approve a Feishu approval instance. The public cloud MCP Gateway exposes only `/mcp`.
- Impact Key sync, email, recurring data audit, and Feishu approval callback are not connected.

## Repository map

| Path | Purpose |
|---|---|
| `docs/DEPLOYMENT.md` | Step-by-step local and cloud deployment guide |
| `scripts/` | Start the mock MCP server, build/push its image through AgentKit Build, verify MCP tools, and launch AgentKit Runtimes |
| `services/ems-governance/` | Streamable HTTP MCP backend, demo governance state, local reviewer/Worker routes, and Docker image |
| `agents/orchestrator/` | AgentKit/VeADK orchestrator; connects to the demo MCP service and read-only A2A checker |
| `agents/schedule-checker/` | Standalone read-only AgentKit A2A Agent |
| `agents/data-auditor/` | Separate read-only data-audit scaffold; not part of the two-Runtime deploy script |
| `contracts/SIMPLY_BOOK_OPENAPI.yaml` | Customer-provided SimplyBook API contract, retained as source material |
| `contracts/SIMPLY_BOOK_SCHEMA.md` | Customer-provided database schema, retained as source material |
| `contracts/EMS_GOVERNANCE_AGENT_OPENAPI.yaml` | Proposed Agent-facing governance contract, not a customer production API |
| `contracts/EMS_WORKER_INTERNAL_OPENAPI.yaml` | Private execution/projection contract; never publish as Agent MCP tools |
| `data/feishu/` | Synthetic Feishu Base snapshot loaded by the demo MCP backend |
| `agentkit-config/` | MCP exposure and A2A boundary definitions |
| `skills/ems-change-operator/SKILL.md` | EMS operating procedure and Agent safety rules |

## Cloud deployment status

The public repository does not contain cloud credentials or endpoint API keys. Each customer can deploy an isolated copy into their own AgentKit project by following [the deployment guide](docs/DEPLOYMENT.md). The guide's cloud build path uses AgentKit Build, so Docker is optional. The hosted walkthrough demonstrates MCP tool discovery, a scoped Grant stopping at `PENDING_APPROVAL`, and an independently callable A2A checker. A cloud reviewer endpoint/shared state is still needed to continue the orchestrator through Change Set approval. The current example remains synthetic: Feishu snapshots are not live-linked and execution does not call SimplyBook or Impact Key.
