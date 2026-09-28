# Demo runbook

## Goal

Show a natural-language EMS request moving through MCP reads, a separate A2A checker, a temporary scoped Grant, and a frozen Change Set that requires a separate reviewer decision before the mock Worker can proceed.

Suggested length: 12–15 minutes. Follow [Deployment](DEPLOYMENT.md) before the meeting.

## Before the meeting

- Use the synthetic Feishu Base snapshot under `data/feishu/`; the cloud demo does not yet read the live Base.
- Keep SimplyBook in mock mode unless a non-production read endpoint has been explicitly configured and checked.
- Use the configured synthetic principal `demo.operator`; it is not employee SSO.
- Use separate local Reviewer and Worker secrets. Never configure the Worker key in the Agent Runtime.
- Do not describe the mock Reviewer route as a Feishu approval instance.
- Keep emails under example.com; no email is sent.
- Have the tool list and audit responses ready to show that agent-facing MCP contains no write or approval tools.

## Storyboard

### 1. Establish the configured demo identity

Ask the Agent:

> 帮我处理 BATCH-DEMO-001：检查报名资格、重复邮箱、时间冲突和课程容量，申请本活动的临时授权，生成待审批变更集；不要直接写入。

Show the MCP response for the Grant request. It records `demo.operator`, the event, batch, allowed actions, row limit, expiry, and `PENDING_APPROVAL`. Explain that this is a server-configured synthetic subject. The production employee-login / identity-broker flow is still to be connected.

### 2. Approve the demo Grant separately

Use the local reviewer route from `docs/DEPLOYMENT.md` with the Reviewer key to inspect the queue and approve the Grant. Return to the Agent and show that preparation is blocked before the Grant becomes active. This is an HTTP demo reviewer action, not a Feishu workflow.

### 3. Show tool integration and A2A analysis

Ask the Agent to inspect `DEMO-IW-2026-001` and `BATCH-DEMO-001`.

- The demo MCP server reads the checked-in Base snapshot and the sample SimplyBook calendar/booking data.
- Agent-facing SimplyBook tools correspond to a read-only subset of the supplied API contract. Mock mode is the default.
- The orchestrator delegates analysis to a distinct read-only schedule-checker Runtime over A2A. The checker gets a separate Runtime API Key, not the MCP or reviewer credential.
- The checker reports duplicate-email candidates, existing enrollment, consent, time overlap, and remaining capacity.

Expected data-quality findings:

| Person | Finding | Safe handling |
|---|---|---|
| P-DEMO-001 | No booking conflict; consent present | Eligible for the target session |
| P-DEMO-002 | Already booked in the target session | Skip as already enrolled |
| P-DEMO-003 (`email1`) | Email matches P-DEMO-007 (`email2`) | Hold for canonical-person confirmation |
| P-DEMO-004 | No conflict; consent present | Eligible for the target session |
| P-DEMO-005 | Existing booking overlaps the target session | Hold; do not silently move |
| P-DEMO-006 (`not-confirmed`) | Consent is not confirmed | Exclude pending manual confirmation |

For a scripted clean preview, select P-DEMO-001 and P-DEMO-004 only. The governance backend independently rejects missing consent, duplicate-email candidates, existing enrollments, schedule conflicts, cross-event sessions, and over-capacity batches.

### 4. Preview and freeze the Change Set

Show the included participant IDs and linked names, event/session, remaining capacity, source version, Grant, policy version, Change Set ID, version, and hash. Freeze the exact preview and submit it for a separate reviewer decision. Editing the preview or using another hash must fail the governance check.

### 5. Review the Change Set separately

Use the local reviewer route with the Reviewer key to review and approve the exact Change Set. Demonstrate that the chat message “同意” does not change approval state. The local route is a mock reviewer API; native Feishu approval definitions, reviewer identities, and callbacks are not connected.

### 6. Show the Worker boundary

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
