# Assumptions and customer validation

The repo uses working assumptions so the POC can move forward. Validate these with the customer before replacing mock adapters with live writes.

## Assumptions in the demo

1. Feishu Base is the input/source dataset for activities, sessions, participants, current bookings, and requested changes in this POC. The production data owner and write-back rules remain for customer validation.
2. SimplyBook is the EMS backend on Alibaba Cloud and the authoritative backend for its existing classes, calendars, bookings, and credits.
3. Impact Key App is the current end-user surface. Approved backend changes should become visible there after a downstream sync.
4. The Agent uses authenticated employee identity; an EMS governance service resolves user/role and issues an event/action-scoped temporary Grant.
5. A Grant approval and a Change Set approval are separate Feishu approval steps with different reviewers.
6. Batch operations require a preview, a frozen Change Set, policy validation, hash-bound approval, execution-time Grant check, idempotency, and an audit record.
7. The Worker owns backend write credentials. Agent-facing MCP tools may read data and prepare proposals but cannot execute writes.
8. The schedule checker is a separate A2A Agent, receives only minimized data needed for duplicate/conflict/capacity checks, and has no write tools.
9. The sample duration is 15 minutes and the demo batch limit is three new enrollments; both are provisional policy values.
10. The live demo will use a mock adapter for named participant mapping and Impact Key unless the customer supplies the missing contracts.

## Contract gaps from the supplied SimplyBook files

- Batch bookings are exposed as POST /calendars/{calendarId}/bookings, but the body only contains count, bookingId, courseId, and eventId. It does not contain a person/ATO ID, and the response returns ID pairs. Named enrollment cannot be proven with this operation alone.
- The supplied endpoints do not describe updating a participant's selected class, sending batch email, or syncing records into Impact Key.
- Some operations have x-internal-route: null. Treat these as proposed/contract-only until an endpoint owner confirms route availability and semantics.
- The schema describes internal tables and fields. It does not prove that those tables can be read or written directly by this POC; prefer the API layer.
- The Token, Appid, Lang, and Platform headers need a service-auth design and scope review before MCP exposure.

## Questions to confirm with the customer

### Identity and governance

- Which identity provider should authenticate operators: Feishu SSO, another corporate IdP, or both?
- What does a Grant authorize: one event, selected sessions, operation types, named participants, maximum count, or all of these?
- Who can issue/approve a Grant, and who can approve a Change Set? Must the approvers be different people?
- What are the required Grant lifetime, revocation behavior, and reauthentication rules?
- Should a Grant require event ownership, role membership, manager approval, or an allowlist?
- Which fields must be recorded for audit, and what are the retention requirements?

### SimplyBook and Impact Key

- Is there a person-specific enrollment endpoint that binds ATO ID/person ID to the booking record?
- Which API updates a booking, removes one participant, moves a participant to a different class, or cancels a booking?
- What is the canonical identifier shared between Feishu, SimplyBook, and Impact Key?
- Does SimplyBook push changes to Impact Key, or does the Worker call a separate Impact Key API?
- Is there an idempotency key or reconciliation endpoint for both systems?
- Which environments and API accounts are safe for POC writes?

### Feishu

- Which Base/table is the source of truth for each data domain? What are the stable IDs and required fields?
- Should the demo use a native Feishu Approval definition, and what are its approval codes, form fields, approvers, and callback mechanism?
- Can the approval card display the full participant/session diff and immutable hash, or should a review page be linked?
- Which identity performs Base reads and approval callbacks: current user, bot, or a dedicated application?

### AgentKit and A2A

- Which AgentKit region, Runtime auth type, approved model, and MCP Gateway should be used?
- Should SimplyBook MCP be read-only for the Agent with a separate private Worker write path?
- Should A2A discovery use AgentKit Agent Registry, a fixed A2A endpoint, or another registry? How will the checker authenticate as a machine client?
- What data may cross the A2A boundary, and should email be hashed or masked for duplicate checks?
- Which trace, audit, and data-residency requirements apply to prompts, MCP tool output, A2A messages, and execution logs?

## Approval to move from scaffold to live POC

The next implementation pass can replace the demo contracts and mock adapters once the customer confirms the enrollment API, Impact Key sync contract, Feishu approval form/callback, identity provider, environment, and Grant policy.
