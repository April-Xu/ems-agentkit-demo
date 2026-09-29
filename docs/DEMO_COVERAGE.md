# Demo coverage and current limits

| Customer capability | What this repository can show after deployment | What remains unconnected |
|---|---|---|
| Identity | Configured synthetic subject `demo.operator`, separate Runtime and MCP/A2A credentials | Employee SSO, verified user identity propagation, OBO |
| Temporary Grant | Cloud request records event/batch/action scope, row limit, expiry, and `PENDING_APPROVAL`; a separate mock Reviewer decision is only demonstrated against local state | Production identity policy, cloud Reviewer ingress/shared state, and Feishu Grant approval |
| Agent governance | Agent has read/prepare/freeze/submit tools only; Worker route is not in the MCP tool list | Live governance API and private cloud Worker service |
| Existing API to MCP | MCP read tools map a subset of the SimplyBook API contract and run against fixtures in mock mode | Full OpenAPI-derived MCP coverage and verified live API route/auth semantics |
| Tool integration | AgentKit MCP Gateway client, local synthetic Base snapshot, SimplyBook read adapter | Live Feishu Base connector and customer SimplyBook account |
| A2A | Separate read-only schedule-checker Runtime; direct A2A invocation with synthetic records succeeded on 2026-09-29 | Orchestrator-to-checker delegation cannot be exercised in the hosted flow while the Grant is pending |
| Duplicate/conflict/capacity | Checker findings plus backend policy guards for consent, duplicate candidates, existing booking, overlap, and capacity | Customer production policy values and data freshness guarantees |
| Frozen batch changes | Versioned Change Set, stable SHA-256 payload hash, freeze and approval state | Durable production storage, source version lock, audit retention |
| Human approval | Separate local Reviewer route; chat text cannot approve; local state cannot approve a cloud Grant | Native Feishu approval definitions, callbacks, reviewer authentication, cloud ingress and shared durable state |
| SimplyBook execution | Mock Worker checks Grant, approval, hash, expiry, and idempotency | Person-specific enrollment/write API and production credentials |
| Impact Key sync | Response shape shows a mock projection result | Impact Key endpoint, retries, reconciliation |
| Scheduled data quality | Separate read-only auditor scaffold | Live Base MCP connection, scheduler/workflow, report destination |
| Bulk email | Explicitly withheld from Agent tools | Customer email API and sending approval policy |

## Claims to keep precise

- “The MCP Gateway service is deployed for the maintainer's demo account” applies only to that account; a customer clone must deploy its own resources.
- “The orchestrator has an A2A checker configured” and “the checker accepts a direct A2A request” are separate claims. The direct checker request is verified; the orchestrator has not delegated a live request to it because the cloud Grant stops at `PENDING_APPROVAL`.
- “SimplyBook reads are represented as MCP tools” is accurate; “all SimplyBook APIs were automatically converted” is not.
- “The demo reviewed a mock Change Set” is accurate; “Feishu approved the Change Set” is not.
- “Worker simulation passed governance checks” is accurate; “SimplyBook enrolled these people” or “Impact Key synced” is not.
