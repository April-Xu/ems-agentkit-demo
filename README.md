# EMS AgentKit Demo

Governed Impact Week event operations using a synthetic Feishu Base export, the customer SimplyBook API contract, AgentKit MCP, a read-only A2A schedule checker, temporary Grants, frozen Change Sets, and a private mock Worker.

This repository contains a deployable **synthetic demo path**. The MCP service reads repository snapshots of the synthetic Feishu Base. Its SimplyBook adapter is mock by default. The Agent can prepare and submit a Change Set, but cannot execute a booking. Reviewer and Worker routes are demo-only. No live Feishu Base, SimplyBook, Feishu approval, or Impact Key credentials are connected.

## Start here

1. Follow [Deployment](docs/DEPLOYMENT.md) to run the mock MCP backend and deploy the AgentKit Runtimes.
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
- Reviewer routes simulate human approval locally; they do not create or approve a Feishu approval instance.
- Impact Key sync, email, recurring data audit, and Feishu approval callback are not connected.

## Repository map

| Path | Purpose |
|---|---|
| `docs/DEPLOYMENT.md` | Step-by-step local and cloud deployment guide |
| `scripts/` | Start the mock MCP server, build/push its image, and launch AgentKit Runtimes |
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

No cloud Runtime, MCP Gateway, Feishu approval definition, live SimplyBook endpoint, email sender, or Impact Key API has been provisioned. The deployment guide documents the exact steps and resource names. Creating cloud resources requires an authenticated AgentKit CLI account; the local task session is not logged in.
