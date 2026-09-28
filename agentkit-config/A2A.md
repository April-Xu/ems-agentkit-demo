# A2A checker setup

The schedule checker is a separate AgentKit A2A app. It has no MCP toolsets
and its system prompt allows analysis only. The orchestrator references the
checker Agent Card through EMS_SCHEDULE_CHECKER_AGENT_CARD_URL.

## Local demo

Run the checker on a loopback-only development port and set the Agent Card URL
in the orchestrator environment. The synthetic dataset contains no real
personal data. Do not expose an unauthenticated checker to a public network.

## Cloud demo

Choose one of these patterns with the customer:

1. Register the checker and orchestrator in an AgentKit A2A Registry space and
   use Registry-managed machine-to-machine authentication.
2. Use a fixed Agent Card URL behind an approved gateway that authenticates
   the calling workload.

The checker must use a dedicated service identity. It receives only the
minimum data needed for schedule validation. Never forward the employee's
bearer token to the checker, and never treat its findings as a Grant or
approval.

The current orchestrator scaffold uses a fixed Agent Card URL for the direct
A2A sub-agent connection. Registry discovery and cloud M2M credentials remain
deployment wiring to be selected and verified. AgentKit Harness documents
Registry-based Agent discovery and OAuth client-credentials for remote agents:
https://volcengine.github.io/agentkit-sdk-python/content/2.agentkit-cli/5.harness.html

