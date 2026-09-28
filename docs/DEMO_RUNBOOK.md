# Demo runbook

## Goal

Show that an Agent can turn a natural-language EMS request into a reviewed, auditable proposal, while identity, temporary authorization, A2A analysis, human approval, and backend writes stay under explicit control.

Suggested length: 12–15 minutes.

## Before the meeting

- Use only the synthetic Feishu Base and demo event DEMO-IW-2026-001.
- Prepare separate operator and reviewer identities.
- Set SimplyBook and Impact Key adapters to sandbox/mock mode unless the customer explicitly provides and approves non-production endpoints.
- Publish only read-only SimplyBook methods and governance prepare/approval methods as Agent MCP tools.
- Publish validated SimplyBook write methods in a separate private MCP service used only by the Worker.
- Keep Worker credentials and execute endpoint private.
- Keep emails in example.com; do not send mail.
- Confirm the approval action refers to a frozen Change Set ID and hash.
- Have an audit view ready to show subject, Agent, Grant, A2A call, approval, Worker job, backend response, and Impact Key sync status.

## Storyboard

### 1. Establish identity and request authority

Log in as a synthetic event operator. Ask:

> 帮我处理 BATCH-DEMO-001：检查报名资格、重复邮箱、时间冲突和课程容量，给出可报名名单；不要直接写入，先申请本活动的临时授权并生成待审批变更集。

Show that the authenticated subject comes from login, not a user-supplied prompt or header. The Agent requests a Grant limited to event DEMO-IW-2026-001, the enrollment-preparation scope, one batch, a maximum of three new enrollments, and a short expiry.

### 2. Approve the temporary Grant

As the event owner, open the Feishu Grant approval. Review subject, event, scope, action limit, duration, and reason. Approve it. Return to the Agent and show the Grant ID, status, expiry, and permitted actions in its audit trail.

The Agent may proceed with reads and preparation. It still cannot execute a booking.

### 3. Show API-to-MCP and A2A analysis

Ask the Agent to inspect the event batch.

- It reads source records from the synthetic Base.
- It reads the target and alternate calendars and current bookings through SimplyBook MCP tools.
- It sends the minimum participant identifiers, email, consent flag, requested session, and current booking windows to the separate schedule-checker over A2A.
- The checker returns findings and source record IDs, without tools that can change data.

Expected findings from the supplied sample:

| Request | Finding | Safe proposal |
|---|---|---|
| P-DEMO-001 | No conflict; consent is present | Include in target session |
| P-DEMO-002 | Already booked in target session | Skip as already enrolled |
| P-DEMO-003 | Email matches P-DEMO-007 | Require canonical-person confirmation; choose P-DEMO-003 for this scripted example |
| P-DEMO-004 | No conflict; consent is present | Include in target session |
| P-DEMO-005 | Overlaps existing booking in CAL-DEMO-102 | Propose CAL-DEMO-103; do not silently move |
| P-DEMO-006 | Consent is not confirmed | Exclude and request manual confirmation |

Target CAL-DEMO-101 has three seats remaining. After the operator confirms P-DEMO-003 is the canonical record, the scripted proposed set is P-DEMO-001, P-DEMO-003, and P-DEMO-004.

### 4. Preview and freeze the Change Set

Show a diff with:

- Included, skipped, and held rows, each with reasons and source row IDs.
- The event, target session, maximum count, before/after capacity, and source-data version.
- The SimplyBook operation the Worker would call.
- Downstream Impact Key projection fields and intended status.
- Change Set ID, version, payload hash, policy version, and expiry.

Freeze the preview. Any later edit creates a new version/hash and requires new approval.

### 5. Approve the exact Change Set in Feishu

As a different reviewer, open the Feishu Change Set approval and check the included participants, exceptions, event/session, count, hash, and expiry. Approve or reject in Feishu. Show that chat confirmation alone cannot move the Change Set to approved.

### 6. Execute and verify the user-facing projection

When approved, the private Worker rechecks the Grant and approval, confirms the exact frozen hash, applies idempotency, and calls the private SimplyBook MCP service. Show:

- SimplyBook job state and returned booking IDs.
- Any skipped or failed rows.
- Impact Key adapter result and user-facing projection status.
- Audit entry with actor, Agent, Grant, Change Set, reviewer, timestamps, and backend job IDs.

For this seeded scenario, the operation should create three demo enrollments only if the selected demo adapter can associate individual participants with bookings. The supplied SimplyBook contract only accepts a booking count, so a live person-to-booking write must remain in mock mode or be replaced by a customer-confirmed enrollment endpoint.

## Optional short second act: block a stale Change Set

After the reviewer approves the Change Set, change one value or revoke/expire the Grant before the Worker starts. Show the Worker refusing the stale request and requiring a new Grant or Change Set. This proves approval and temporary authorization are checked again at execution time.

## Optional second story: scheduled data-quality review

Invoke the EMS Data Auditor once with the dedicated read-only machine identity. Ask it to scan the permitted participant table for duplicate emails, likely duplicate records, missing/invalid fields, inconsistent dates, and Chinese/English translation candidates. Show a report with source row IDs and evidence, then leave all proposed corrections for human review.

For the POC, one manual invocation demonstrates the Agent. The recurring trigger is an existing customer scheduler or approved Feishu Workflow and remains unconfigured until the customer chooses the trigger, identity, cadence, retry policy, and report destination. The auditor must not update source records or send emails.

## What the customer should observe

- Which MCP methods were exposed from the OpenAPI contract, and which write methods were withheld from the Agent.
- Whether Grant issuance and Change Set execution can be separate Feishu approvals.
- Whether reviewers see a stable diff and hash that match what the Worker executes.
- Whether the user's identity and A2A service identity remain distinct in audit records.
- Whether Impact Key status can be queried and reconciled after the write.
- Whether failure, retry, expiry, and duplicate delivery remain safe.
