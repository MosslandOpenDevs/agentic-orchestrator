# GitHub Labels

GitHub issues are not a record anywhere in this repository: no code in it creates, reads, labels,
comments on or closes an issue. The record is SQLite (`data/orchestrator.db`), and
https://ao.moss.land renders it.

The labels below were applied by the orchestrator, which used to mirror ideas and plans into
issues, and by people, who used them to give it instructions.

| Label | Meant |
|-------|-------|
| `type:idea` | An idea |
| `type:plan` | A plan written for an idea |
| `generated:by-orchestrator` | Opened by the orchestrator, not by a person |
| `source:trend` | An idea generated from RSS trend analysis (#2–#64, January 2026) |
| `status:backlog` | Waiting for a decision |
| `status:planned` | A plan was written for this idea |
| `status:archived` | The idea was archived in the database |
| `status:done` | A project was generated from this plan |
| `promote:to-plan` | Write a plan for this idea — added by a person, or by the orchestrator when it promoted the idea |
| `processed:to-plan` | That request was handled: a plan exists |
| `processed:to-dev` | A project was generated from this plan |
| `reject:plan` | A person rejected this plan and asked for a new one |
| `rejected` | The plan was closed after that rejection |
| `curated:keep` | Keep this issue open |

## Open issues

The 12 open issues — #1, #5, #59, #62, #529, #570, #730, #731, #750, #762, #1011 and #2820 — are the
`curated:keep` shortlist the owner chose on 2026-06-26 (checked 2026-09-11). Nothing reads or writes
them. Closing an issue deletes nothing, and a closed issue can be reopened.
