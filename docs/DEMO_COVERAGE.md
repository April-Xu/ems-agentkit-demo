# Demo coverage

| Customer capability | Demonstrated by | Guardrail shown |
|---|---|---|
| Employee identity | Interactive orchestrator plus governance API | Subject is derived from verified login/token; prompt text cannot claim identity |
| Temporary Grant | Grant request and separate Feishu Grant approval | Event, actions, batch/row limit, and expiry are explicit; Worker rechecks it |
| Agent governance | Agent MCP allowlist, Change Set service, private Worker | Agent can prepare/freeze/submit only; execute tool and write credential are absent |
| Existing API to MCP | SimplyBook OpenAPI exposed through a read service and a separate Worker-only write service | Service boundary and route allowlist are visible; unverified contract-only paths are withheld |
| Tool integration | Feishu Base read MCP, SimplyBook read/write MCP, governance MCP | Separate scopes and credentials; direct writes are only available to Worker |
| A2A | Orchestrator delegates to the standalone schedule-checker | Checker is a separate Agent with read-only tools and a distinct machine identity |
| Conflict and duplicate checks | Seeded booking overlaps, duplicate email, capacity, and consent cases | Findings carry source IDs; ambiguous rows need a human decision |
| Frozen batch changes | Change Set preview, version, hash, and source versions | Any edit changes the version/hash and invalidates approval |
| Feishu human approval | Separate Grant and Change Set approval instances | Chat confirmation cannot approve; approval must match the frozen Change Set |
| SimplyBook execution | Private Worker calls the SimplyBook write MCP after all checks | Current count-based endpoint cannot map named people to bookings; named-enrollment write stays mock until API confirmed |
| Impact Key sync | Worker reports downstream projection status using a demo adapter placeholder | No customer Impact Key API was provided; do not claim live synchronization |
| Scheduled data-quality review | Data Auditor Agent, manually triggered for a first run and later connected to a scheduler | Dedicated machine identity, Base read-only permission, human-reviewed report |
| Bulk email | Not in the live flow; only a future contract/readiness item | Supplied API has no mail endpoint; do not send mail from sample data |

## Key statements to keep precise

- “The SimplyBook OpenAPI has been wrapped as curated MCP tools” is accurate only after the gateway services are configured. The repository contains the source contract and the exposure plan.
- “The Agent prepared a named-person Change Set” is supported by the demo governance contract and synthetic Base.
- “The production SimplyBook API enrolled these named people” is not supported by the supplied count-only booking endpoint.
- “Impact Key synced” must be labeled as a demo projection result until the live endpoint is supplied and exercised.
- “The checker is a separate A2A Agent” is true of this scaffold. A secured cloud call still needs the selected A2A Registry or gateway machine-auth configuration.

