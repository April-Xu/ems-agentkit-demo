# EMS AgentKit Demo

Governed Impact Week event operations using a synthetic Feishu Base, SimplyBook API contracts, AgentKit MCP, a read-only A2A schedule checker, temporary Grants, frozen Change Sets, Feishu approval, and a private Worker.

This repository is a demo scaffold. The supplied SimplyBook OpenAPI and schema are retained as source contracts; the Feishu Base contains synthetic records only. Live SimplyBook, Feishu approval, and Impact Key credentials have not been connected.

## Demo story

An authenticated activity operator asks the Agent to prepare a batch enrollment for Impact Week. The Agent requests an event-scoped temporary Grant, reads the Feishu Base and SimplyBook through MCP, and asks a separate read-only schedule checker over A2A to check duplicates, conflicts, and capacity. It prepares a preview and freezes it as a Change Set. A separate Feishu approval must approve that exact frozen version. Only a private Worker can execute after it rechecks the Grant, approval result, Change Set hash, expiry, and idempotency key. The Worker then records the SimplyBook and Impact Key results.

The demo makes the following boundaries visible:

- Identity: retain the authenticated human subject, Agent workload identity, event, and action scope in each Grant and audit entry.
- Temporary authorization: Grant applies to one event, selected actions, one batch, and a short lifetime. It is checked again when the Worker starts.
- Agent governance: the Agent can read, request a Grant, prepare/freeze a Change Set, and submit it for approval. It has no execute tool or write credential.
- Tool integration: the supplied SimplyBook OpenAPI is the source for an AgentKit MCP Gateway service; read and write exposure are separated.
- A2A: the orchestrator delegates only the minimum necessary synthetic data to a distinct schedule checker. The checker is read-only and has no business write tools.
- Human approval: Grant approval and Change Set approval are separate decisions. Approval is bound to the immutable Change Set ID and hash.
- Downstream sync: the Worker reports the write and Impact Key projection status. The Impact Key adapter is a demo placeholder until its API contract is supplied.

## Start here

1. Read the [architecture](docs/ARCHITECTURE.md), [demo runbook](docs/DEMO_RUNBOOK.md), and [assumptions and questions](docs/ASSUMPTIONS_AND_QUESTIONS.md).
2. Review the [demo coverage matrix](docs/DEMO_COVERAGE.md) to see which customer capability each piece proves.
3. Open the [synthetic Feishu Base](https://bytedance.larkoffice.com/base/EqKybzfN6apgq2sPztVckxZMnth). Its records use fake names and example.com email addresses.
4. Review contracts/SIMPLY_BOOK_OPENAPI.yaml and contracts/SIMPLY_BOOK_SCHEMA.md.
5. Review the agent-facing and worker-only contract split under contracts/.
6. Configure local secrets from .env.example only after the customer approves the demo connections and identities.

## Repository map

| Path | Purpose |
|---|---|
| agents/orchestrator/ | AgentKit/VeADK Agent Server scaffold; connects to curated MCP toolsets and delegates to the A2A checker |
| agents/schedule-checker/ | Standalone read-only AgentKit A2A Agent scaffold |
| agents/data-auditor/ | Read-only data-quality Agent for a manually triggered first run and a customer-configured scheduler |
| contracts/SIMPLY_BOOK_OPENAPI.yaml | Customer-provided SimplyBook API contract, unchanged |
| contracts/SIMPLY_BOOK_SCHEMA.md | Customer-provided database schema, unchanged |
| contracts/EMS_GOVERNANCE_AGENT_OPENAPI.yaml | Proposed Agent-facing Grant and Change Set API; demo contract, not customer production API |
| contracts/EMS_WORKER_INTERNAL_OPENAPI.yaml | Private execution and projection operations; never publish as Agent MCP tools |
| data/feishu/ | Payloads used to create the synthetic Base records |
| agentkit-config/MCP_EXPOSURE.yaml | Intended MCP service boundaries and tool allowlist |
| skills/ems-change-operator/SKILL.md | EMS operating procedure and safety rules for the Agent |
| docs/ | Architecture, demo script, assumptions, and customer validation questions |

## Important API fit

The SimplyBook contract includes batch booking as POST /calendars/{calendarId}/bookings, but its body accepts count, bookingId, courseId, and eventId; it does not accept named participants, ATO IDs, or participant-to-booking mappings. The response returns booking ID pairs. Therefore, the supplied contract can demonstrate booking-count operations through MCP, but it cannot prove person-specific enrollment end to end. The demo must label any participant mapping as a mock adapter assumption until the customer supplies or confirms the real enrollment API.

The supplied contract also has operations marked x-internal-route: null; those are contract-only or model-layer operations and must not be advertised as callable production endpoints before route validation. No email-send operation or Impact Key synchronization endpoint appears in the supplied contract.

## Current completion state

- Synthetic Feishu Base and five tables are created and seeded.
- AgentKit orchestrator, read-only A2A checker, and scheduled-audit Agent scaffolds are present.
- Customer SimplyBook API and schema contracts are copied into the repo.
- Demo contracts and runbook describe the intended governed path.
- No cloud Runtime, AgentKit MCP service, Feishu approval definition, live SimplyBook endpoint, email sender, or Impact Key API has been provisioned.

## Runtime setup

The generated AgentKit templates target Python 3.12. Install the dependencies listed in each agent directory, copy .env.example to a local .env, and supply only the demo endpoints and credentials approved for the session. The orchestrator expects curated Streamable HTTP MCP services and a schedule-checker Agent Card URL.

Each scaffold starts its local app when its Python entry file is run from that agent directory. The schedule checker defaults to port 8001 and the data auditor to port 8002. The orchestrator defaults to port 8000. All required MCP endpoints, API keys, and the checker Agent Card URL must be configured first.

For AgentKit MCP clients, this scaffold follows the documented VeADK MCPToolset and StreamableHTTPConnectionParams pattern. The AgentKit SDK A2A Agent template exposes the checker. A2A service authentication must be configured with the chosen deployment; never pass the employee's bearer token to the checker.

The MCP API key in the local example authenticates the Agent to an MCP service; by itself, it does not identify the employee. Before any live Grant request, the deployment must pass a verified employee identity to the governance API using an approved user-token or trusted identity-broker flow. A subject field typed by the Agent is not sufficient.

The complementary scheduled audit is read-only. Its first run can be invoked manually; a customer scheduler or Feishu Workflow must be configured before describing it as recurring automation.

The two Agent templates were generated with AgentKit SDK 0.8.5. Review the current AgentKit and Feishu tenant configuration before deploying. This repository has not been deployed or exercised against customer or cloud endpoints.
