# EMS governance and execution boundary

This directory is reserved for the policy service and Worker adapters. The
contracts are in contracts/EMS_GOVERNANCE_AGENT_OPENAPI.yaml and
contracts/EMS_WORKER_INTERNAL_OPENAPI.yaml.

## Agent-facing service

The governance API derives the employee subject from a verified identity token
or trusted identity broker. It must not accept a subject ID supplied in the
request body. It supports:

- Temporary Grant requests, with an independent Feishu approval.
- Grant lookup scoped to the authenticated employee.
- Change Set preparation with source versions, finding references, and impact.
- Freeze of the exact preview version and content hash.
- Submission of the frozen Change Set to a separate Feishu approval.

The Agent-facing service has no execute endpoint.

## Private Worker

The Worker consumes approved Change Sets from a queue. Before calling any
backend, it checks:

1. The approval callback is final and belongs to the same Change Set ID,
   version, and hash.
2. The Grant is active, belongs to the same employee and event, covers each
   proposed operation, has not expired or been revoked, and remains within
   its row/batch limit.
3. Source versions, capacity, and policy version still match the frozen
   preview.
4. The idempotency key has not already been applied.

The Worker stores an append-only audit record and reports SimplyBook execution
and Impact Key projection separately. If one stage fails, expose partial
status and safe retry behavior rather than claiming success.

## Integrations to fill in after customer confirmation

- Feishu approval definition, approval instance creation, callback signature
  verification, and reviewer mapping.
- SimplyBook enrollment API that binds a named participant to a booking.
- Impact Key production API, stable identifiers, and reconciliation behavior.
- Email provider/API only if bulk email is in scope for a later demo.
- Durable Change Set store, queue, audit store, and retry/dead-letter policy.
- Customer-approved identity provider, Grant roles, policy rules, and data
  retention.

The demo-only Impact Key route must never be presented as the actual customer
endpoint. No implementation in this directory currently sends live writes.

