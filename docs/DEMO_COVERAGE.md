# Demo coverage and current limits

| Customer capability | What this repository can show after deployment | What remains unconnected |
|---|---|---|
| Identity | Configured synthetic subject `demo.operator`, separate Runtime and MCP/A2A credentials | Employee SSO, verified user identity propagation, OBO |
| Temporary Grant | Event/batch/action scope, row limit, expiry, separate mock Reviewer decision | Production identity policy and Feishu Grant approval |
| Agent governance | Agent has read/prepare/freeze/submit tools only; Worker route is not in the MCP tool list | Live governance API and private cloud Worker service |
| Existing API to MCP | MCP read tools map a subset of the SimplyBook API contract and run against fixtures in mock mode | Full OpenAPI-derived MCP coverage and verified live API route/auth semantics |
| Tool integration | AgentKit MCP Gateway client, local synthetic Base snapshot, SimplyBook read adapter | Live Feishu Base connector and customer SimplyBook account |
| A2A | Separate read-only schedule-checker Runtime, called with its own API Key | Cloud deployment has not been run in this task account |
| Duplicate/conflict/capacity | Checker findings plus backend policy guards for consent, duplicate candidates, existing booking, overlap, and capacity | Customer production policy values and data freshness guarantees |
| Frozen batch changes | Versioned Change Set, stable SHA-256 payload hash, freeze and approval state | Durable production storage, source version lock, audit retention |
| Human approval | Separate local Reviewer route; chat text cannot approve | Native Feishu approval definitions, callbacks, reviewer authentication, cloud ingress |
| SimplyBook execution | Mock Worker checks Grant, approval, hash, expiry, and idempotency | Person-specific enrollment/write API and production credentials |
| Impact Key sync | Response shape shows a mock projection result | Impact Key endpoint, retries, reconciliation |
| Scheduled data quality | Separate read-only auditor scaffold | Live Base MCP connection, scheduler/workflow, report destination |
| Bulk email | Explicitly withheld from Agent tools | Customer email API and sending approval policy |

## Claims to keep precise

- “The demo MCP server is deployable” is accurate; “the MCP Gateway service is already deployed” is not.
- “The AgentKit orchestrator has an A2A checker configured” is accurate; “cloud A2A was exercised” is not until both Runtime endpoints are Ready and a fresh call succeeds.
- “SimplyBook reads are represented as MCP tools” is accurate; “all SimplyBook APIs were automatically converted” is not.
- “The demo reviewed a mock Change Set” is accurate; “Feishu approved the Change Set” is not.
- “Worker simulation passed governance checks” is accurate; “SimplyBook enrolled these people” or “Impact Key synced” is not.
