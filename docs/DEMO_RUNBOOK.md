# Demo runbook

## Goal

Show the deployed MCP tool boundary, a scoped Grant request that stops at `PENDING_APPROVAL`, and a separately deployed A2A schedule checker. The public cloud demo does not yet expose a Reviewer API or Feishu callback, so the local Reviewer/Worker story is a separate local-only act.

Suggested length: 12–15 minutes. Follow [Deployment](DEPLOYMENT.md) before the meeting.

## Before the meeting

- Use the synthetic Feishu Base snapshot under `data/feishu/`; the cloud demo does not yet read the live Base.
- Keep SimplyBook in mock mode unless a non-production read endpoint has been explicitly configured and checked.
- Use the configured synthetic principal `demo.operator`; it is not employee SSO.
- Use separate local Reviewer and Worker secrets. Never configure the Worker key in the Agent Runtime.
- Do not describe the mock Reviewer route as a Feishu approval instance.
- Keep emails under example.com; no email is sent.
- Have the tool list and audit responses ready to show that agent-facing MCP contains no write or approval tools.
- Confirm both Runtime Agents are `Ready` and that the configured ModelArk model is enabled for this account.

## Storyboard

### 1. Establish the configured demo identity

Open the AgentKit MCP service tool list and the two Runtime details. Show the available read, Grant request, and Change Set preparation tools; there are no direct booking, approval, email, or Impact Key write tools.

Ask the orchestrator:

> 仅为 DEMO-IW-2026-001 / BATCH-DEMO-001 申请临时授权。返回授权状态后停止；如果不是 Active，不要读取数据、准备变更或执行写入。

Show the MCP response for the Grant request. It records `demo.operator`, the event, batch, allowed actions, row limit, expiry, and `PENDING_APPROVAL`. Explain that this is a server-configured synthetic subject. The production employee-login / identity-broker flow is still to be connected. Stop here for the cloud Grant: the public Gateway only routes `/mcp`, and its separate reviewer HTTP routes are not reachable through it. The local Reviewer below cannot approve this cloud Grant.

### 2. Demonstrate the A2A checker

To demonstrate the A2A endpoint independently, copy the schedule-checker Runtime ID from `agentkit status --config-file .deploy/schedule-checker/agentkit.yaml --verbose`, then call it directly:

```bash
agentkit invoke run --runtime-id <SCHEDULE_CHECKER_RUNTIME_ID> \
  --region cn-beijing --a2a \
  "Analyze synthetic records only: event DEMO-IW-2026-001, session S-101, capacity 2. P-DEMO-003 and P-DEMO-007 have the same email; report the duplicate and capacity findings. Make no changes."
```

This verifies the separately deployed A2A Runtime and its read-only analysis. The orchestrator's A2A delegation is configured in code, but the public cloud run cannot reach that stage while the Grant remains pending.

### 3. Show the local-only reviewer and mock worker

If you want to show the complete approval gate, start the local MCP service and use only local state as described in `docs/DEPLOYMENT.md`:

- Create a local synthetic Grant, approve it with the separate Reviewer key, then prepare and freeze a Change Set.
- Approve the Change Set using the second Reviewer key and invoke the private mock Worker using its separate key.
- This is a local HTTP demo, not a cloud approval flow or Feishu workflow. Local SQLite state and cloud state are not shared.

The local MCP server reads the checked-in Base snapshot and sample SimplyBook calendar/booking data. Its SimplyBook tools are a read-only subset of the customer contract and mock mode is the default.

### 4. Walk through the policy findings

Use the results from the A2A sample or local preview to show duplicate email candidates, existing enrollment, consent, time overlap, and remaining capacity. In the A2A sample, P-DEMO-003 and P-DEMO-007 share an email, so both require human confirmation. For a clean local preview, select P-DEMO-001 and P-DEMO-004 only. The governance backend rejects missing consent, duplicate-email candidates, existing enrollments, schedule conflicts, cross-event sessions, and over-capacity batches.

Expected data-quality findings:

| Person | Finding | Safe handling |
|---|---|---|
| P-DEMO-001 | No booking conflict; consent present | Eligible for the target session |
| P-DEMO-002 | Already booked in the target session | Skip as already enrolled |
| P-DEMO-003 (`email1`) | Email matches P-DEMO-007 (`email2`) | Hold for canonical-person confirmation |
| P-DEMO-004 | No conflict; consent present | Eligible for the target session |
| P-DEMO-005 | Existing booking overlaps the target session | Hold; do not silently move |
| P-DEMO-006 (`not-confirmed`) | Consent is not confirmed | Exclude pending manual confirmation |

For a local clean preview, select P-DEMO-001 and P-DEMO-004 only. The governance backend independently rejects missing consent, duplicate-email candidates, existing enrollments, schedule conflicts, cross-event sessions, and over-capacity batches.

### 5. Preview, freeze, and execute the local mock Change Set

Show the included participant IDs and linked names, event/session, remaining capacity, source version, Grant, policy version, Change Set ID, version, and hash. Freeze the exact preview and submit it for a separate reviewer decision. Editing the preview or using another hash must fail the governance check.

### 6. Review the local Change Set separately

Use the local reviewer route with the Reviewer key to review and approve the exact Change Set. Demonstrate that the chat message “同意” does not change approval state. The local route is a mock reviewer API; native Feishu approval definitions, reviewer identities, and callbacks are not connected.

### 7. Show the Worker boundary

The private demo Worker endpoint accepts only a separate Worker key. It rechecks Grant expiry/scope, final review status, frozen payload hash, and idempotency. The result is `SIMULATED`, `MOCK_ONLY_NOT_SENT` for SimplyBook, and `MOCK_ONLY_NOT_SYNCED` for Impact Key. No booking or user-facing app record changes.

The supplied SimplyBook API accepts a booking count and cannot bind individual people to created booking IDs. A production named-enrollment write needs a confirmed customer endpoint.

## Optional short second act: reject stale authorization

Wait until the Grant expires or change a Change Set payload/hash. Show the Worker rejecting the stale request. A new Grant or frozen Change Set must be prepared and reviewed.

## Optional second story: data-quality review

The `agents/data-auditor/` folder is a separate scaffold. Its read-only MCP URL is not included in the two-Runtime deployment script. Connect an approved Base read service and scheduler before showing it as an autonomous recurring audit.

## What the customer should observe

- The published Agent MCP tool list has no direct business-write, reviewer-approval, email, or Impact Key tool.
- MCP and A2A use different service credentials and identities.
- Grant scope and expiry are checked by the governance backend, and the Worker checks them again.
- A Change Set approval is associated with a frozen ID/version/hash.
- The current repository proves the governed flow with synthetic records and mock adapters. Employee SSO, native Feishu approval, live Base reads, SimplyBook writes, and Impact Key sync remain integration work.
- The public cloud walkthrough currently reaches `PENDING_APPROVAL`; direct A2A checking is a separate Runtime call. Cloud Reviewer state sharing and Feishu callbacks remain integration work.
