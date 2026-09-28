# Synthetic Feishu Base

Base: [EMS AgentKit Demo（合成样例数据）](https://bytedance.larkoffice.com/base/EqKybzfN6apgq2sPztVckxZMnth)

All names are synthetic, email addresses use example.com, and all identifiers
are labeled DEMO. No customer participant data was copied into this Base.

## Tables seeded

| Table | Sample rows | Purpose |
|---|---:|---|
| 活动 | 1 | Impact Week demo event and date range |
| 课程排期 | 3 | Target session, conflicting session, and alternative session |
| 人员名单 | 7 | Candidate participant list, consent flags, duplicate-email candidate |
| 当前报名 | 2 | Existing enrollment in the target and overlapping session |
| 批量报名请求 | 6 | Batch DEMO-001 requests for the target session |

The JSON files in this directory use Lark Base batch-create payloads. They
are retained as reproducible seed data; the Base was populated separately.
The Base token and user access credentials are intentionally not stored here.

## Scripted findings

- CAL-DEMO-101 has three remaining seats.
- P-DEMO-002 is already enrolled in CAL-DEMO-101 and should be skipped.
- P-DEMO-003 and P-DEMO-007 share participant03@example.com; the canonical
  person must be confirmed before preparing an enrollment for P-DEMO-003.
- P-DEMO-005 has an overlapping booking in CAL-DEMO-102; CAL-DEMO-103 is an
  alternate session but any move requires explicit review.
- P-DEMO-006 lacks confirmed consent and should be held.
- The scripted Change Set includes P-DEMO-001, P-DEMO-003, and P-DEMO-004
  only after the operator confirms P-DEMO-003 is the canonical record.

