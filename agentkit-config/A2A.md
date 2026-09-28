# A2A checker setup

The schedule checker is a separate AgentKit A2A app. It has no MCP toolsets
and its system prompt allows analysis only. The orchestrator references the
checker Agent Card through EMS_SCHEDULE_CHECKER_AGENT_CARD_URL.

## Local demo

Run the checker on a loopback-only development port and set the Agent Card URL
in the orchestrator environment. The synthetic dataset contains no real
personal data. Do not expose an unauthenticated checker to a public network.

## Cloud demo

The current orchestrator uses the fixed Agent Card URL in
`EMS_SCHEDULE_CHECKER_AGENT_CARD_URL` and sends the separate schedule-checker
Runtime API Key from `EMS_SCHEDULE_CHECKER_A2A_AUTH_KEY` as a Bearer credential.
The Runtime must require key authentication, and these values must be filled
after deploying the checker. The public demo uses synthetic data only.

The checker must use a dedicated service identity. It receives only the
minimum data needed for schedule validation. Never forward the employee's
bearer token to the checker, and never treat its findings as a Grant or
approval. A production deployment should replace the fixed demo key with the
customer's approved service identity / registry pattern and rotate the key.
