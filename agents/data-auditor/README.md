# EMS Data Auditor

Read-only companion Agent for the scheduled data-quality scenario. It checks a
permitted Feishu Base table for exact duplicate emails, likely duplicate
records, missing or invalid fields, date inconsistencies, and Chinese/English
translation candidates. Its only toolset is a dedicated Base read-only MCP
service.

The Agent itself does not contain a scheduler. Trigger it from the customer's
existing scheduler or an approved Feishu Workflow; keep the trigger identity
separate from an employee's interactive identity. The first demo can invoke
one audit run manually to review its report. Do not describe recurring
execution as configured until the scheduler, run identity, retry behavior,
and report destination are connected.

The output is a report for human review. This Agent cannot edit/delete source
rows, change consent, enroll/remove participants, create approvals, or send
email.

