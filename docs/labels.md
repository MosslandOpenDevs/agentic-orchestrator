# GitHub Labels Guide

This document describes the labels used in the Mossland Agentic Orchestrator workflow.

> **The per-item issue mirror is retired.** No scheduled process creates, labels, comments on or
> closes issues any more ([Issue Lifecycle](#issue-lifecycle-retired)). SQLite
> (`data/orchestrator.db`) is the record and https://ao.moss.land renders it. This page documents
> the labels on existing issues and the manual `ao backlog` CLI, which still reads and writes
> them. Closing an issue does not delete data.

> **`promote:to-plan` is not a "future" label.** Its consumer is implemented
> (`GitHubClient.find_ideas_to_promote` → `BacklogOrchestrator.run_cycle`) and last ran
> successfully on 2026-01-04. What is missing is a *scheduler entry*: `run_cycle` is reachable
> only from `ao backlog run` / `ao backlog process`, and no PM2 process invokes it. The PM2
> `moss-ao-backlog` job runs a different function (`run_backlog_triage` + retention), not
> `run_cycle`. Until the mirror was retired, the orchestrator also added this label **itself** to
> ideas it promoted — see
> [Known Ambiguity](#known-ambiguity-promoteto-plan-had-two-meanings).

## Quick Reference

Source of truth for this table is `Labels.ALL_LABELS` in
[`github_client.py`](../src/agentic_orchestrator/github_client.py). Since the mirror was retired,
"Orchestrator" below means the manual `ao backlog` CLI: no scheduled process adds or removes any
of these labels.

| Label | Purpose | Who Adds It | Status |
|-------|---------|-------------|--------|
| `type:idea` | Marks an idea issue | Orchestrator | Active |
| `type:plan` | Marks a planning issue | Orchestrator | Active |
| `status:backlog` | In backlog, awaiting action | Orchestrator | Active |
| `status:planned` | A plan exists for this idea | Orchestrator | Active |
| `status:archived` | Low-scoring idea (<4.0) | Orchestrator | Defined; unused on this repo |
| `status:in-dev` | Plan is being implemented | Orchestrator | Defined; unused on this repo |
| `status:done` | Completed | Orchestrator | Defined; unused on this repo |
| `generated:by-orchestrator` | Auto-generated content | Orchestrator | Active |
| `source:trend` | Generated from trend analysis | Orchestrator | Active |
| `promote:to-plan` | Queue idea for planning | Human (the scheduled pipeline also added it until the mirror was retired) | Active |
| `processed:to-plan` | Promotion consumed; plan created | Orchestrator | Active |
| `reject:plan` | Reject a plan and regenerate | Human | Defined; unused on this repo |
| `rejected` | Terminal marker written by `reject_plan()` | Orchestrator | Active (closed issues) |
| `curated:keep` | Survived the 2026-06 issue-cleanup triage | Human | Active (12 issues) |
| `promote:to-dev` | Start development from plan | Human | *Not implemented* |

`curated:keep` is a human-only triage marker: no code adds it (as with `reject:plan` and
`promote:to-dev`). It was applied during the 2026-06 cleanup. Nothing on a schedule closes issues
any more, so the label now records that decision rather than sparing an issue from a sweep.

`rejected` and `reject:plan` are **not** duplicates: `reject:plan` is the input a human adds, and
`rejected` is the terminal marker `reject_plan()` writes afterwards. Do not retire either one.

## Current Workflow (DB-Centric)

SQLite is the only record the scheduled pipeline writes, and https://ao.moss.land renders it. No GitHub issue is created.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SIGNAL COLLECTION                            │
│                           ↓                                      │
│                     TREND ANALYSIS                               │
│                           ↓                                      │
│                   MULTI-STAGE DEBATE                             │
│                           ↓                                      │
│                     AUTO-SCORING                                 │
│          ┌────────────┼────────────┐                            │
│          ↓            ↓            ↓                            │
│     promoted      scored       archived                         │
│      (>=7.0)      (4-7)        (<4.0)                           │
│          │            │            │                            │
│          ↓            ↓            ↓                            │
│   ┌─────────────────────────────────────────┐                   │
│   │           SQLite DB (Primary)            │                   │
│   │              ideas table                 │                   │
│   │              plans table                 │                   │
│   └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Debate completes** → Ideas generated with scores
2. **Auto-Scorer evaluates** → Assigns status based on score
3. **DB storage** → the record: the `ideas` table, and `plans` for the one promotion that carries the debate's plan document
4. **Published** → on https://ao.moss.land; no GitHub issue

### Status Mapping (issues created before the retirement)

Was written by `_auto_score_and_save_ideas` in
[`scheduler/tasks.py`](../src/agentic_orchestrator/scheduler/tasks.py), which no longer touches GitHub.

| DB Status | GitHub Labels | Description |
|-----------|---------------|-------------|
| `promoted` | `type:idea`, `promote:to-plan` | High-quality idea, queued for planning |
| `scored` | `type:idea`, `status:backlog` | Medium-quality, needs review |
| `archived` | *(no issue created)* | Low-quality, DB-only since v0.6.15 |
| `planned` | `type:plan`, `status:backlog` | Plan document exists |

Note that the `promoted` row carries **no** `status:` label. That is deliberate:
`find_ideas_to_promote()` queries `[type:idea, promote:to-plan]`, and adding `status:backlog`
would double-count the issue across two queues that are meant to be exclusive.

Archived ideas (score < 4.0) stopped getting GitHub issues in v0.6.15 — an issue
that is dead on arrival is tracker noise; the DB row remains the record. Issues
created before v0.6.15 with `status:archived` still exist in the closed set.

### Issue Lifecycle (retired)

Scheduled closing stopped with the mirror: nothing closes an issue when its idea is promoted or
archived, there is no aging sweep, and no scheduled process closes an issue for any other reason.
An issue now closes by hand — directly, or through the manual `ao backlog` CLI a person runs.
Closing is visibility-only: DB rows are untouched, and any closed issue can be reopened.

## Label Categories

### Type Labels

These indicate what kind of issue it is:

- **`type:idea`** - An idea for a new micro Web3 service
  - Created by: the manual `ao backlog` CLI; debate ideas got one until the mirror was retired
  - Contains: Idea summary, auto-score results, debate context

- **`type:plan`** - A detailed planning document
  - Created by: the manual `ao backlog` CLI; promoted debate ideas got one until the mirror was retired
  - Contains: Full implementation plan with architecture, timeline, KPIs

### Status Labels

These track the current state of an issue:

- **`status:backlog`** - In the backlog, waiting for review
- **`status:planned`** - A plan has been generated from this idea
- **`status:archived`** - Low-scoring idea (<4.0), not actively pursued
- **`status:in-dev`**, **`status:done`** - Defined for the development stage; not in use yet

There is no `status:promoted`. A promoted idea is identified by `promote:to-plan`.

### Source Labels

These indicate where the content came from:

- **`source:trend`** - Generated from trend analysis
- **`generated:by-orchestrator`** - Auto-generated (all orchestrator content)

There is no `source:debate` label. Debate-originated ideas carry only
`generated:by-orchestrator`; to tell the two apart, read `ideas.source_type` in the DB
(`debate` vs `trend_based`).

---

## Label-Based Promotion

### Known Ambiguity: `promote:to-plan` had two meanings

The docs and the issue template describe this label as a **human approval gate**
(`.github/ISSUE_TEMPLATE/idea.yml`: "If selected, add the `promote:to-plan` label to start
planning"). Until the mirror was retired, the orchestrator also applied it **automatically** to
every idea it promoted (`scheduler/tasks.py`). When this was last checked, every open issue
carrying it had been labelled by the bot in the same second the issue was created; the only
human-applied instances are #7 and #11 from 2026-01-04.

The retirement settles it for new labels: no scheduled code adds `promote:to-plan` any more, so
from now on the label means a person asked. Issues the bot labelled still carry it, though, so
before anyone puts `run_cycle` on a schedule, check which of those are still open — the consumer
would queue them for a plan the pipeline may already have written.

### Promotion Labels

- **`promote:to-plan`** — implemented. Consumer: `find_ideas_to_promote()` →
  `BacklogOrchestrator.run_cycle`. Behaviour when it runs:
    1. Generate a detailed planning document
    2. Create a new `type:plan` issue
    3. Swap the idea's labels to `processed:to-plan` + `status:planned`
  - Reachable today only via `ao backlog run` / `ao backlog process`; no PM2 job calls it.

- **`promote:to-dev`** - *Not implemented.* Tell the orchestrator to start development
  - Add to any `type:plan` issue you want to implement
  - Planned behavior:
    1. Create project scaffold in `projects/` directory
    2. Set up directory structure based on plan
    3. Generate initial boilerplate code
    4. Update the plan with `status:in-dev`

### Planned Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        IDEA BACKLOG                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  type:idea + status:backlog                              │  │
│  │  (created by the manual `ao backlog` CLI; debate ideas   │  │
│  │   too until the mirror was retired)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                    Human adds: promote:to-plan                  │
│                             ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                        PLAN BACKLOG                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  type:plan + status:backlog                              │  │
│  │  (Generated from promoted idea)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                    Human adds: promote:to-dev                   │
│                             ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                      IN DEVELOPMENT                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  type:plan + status:in-dev                               │  │
│  │  Project scaffold created in: projects/<project-name>/   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                    Development complete                         │
│                             ↓                                   │
├─────────────────────────────────────────────────────────────────┤
│                          DONE                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  status:done                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setting Up Labels

Do not hand-write `gh label create` calls — an earlier version of this page created three labels
that no code uses and omitted most of the ones that matter. Create them from the registry
instead, which is idempotent and always matches `Labels.ALL_LABELS`:

```bash
ao backlog setup
```

`curated:keep` is in the registry too, so `ao backlog setup` creates it; only people apply it.

## Common Scenarios

### "I want to see what ideas were generated"

```bash
# Via CLI
sqlite3 data/orchestrator.db "SELECT id, title, status, score FROM ideas ORDER BY created_at DESC LIMIT 10"

# Via API
curl https://ao.moss.land/api/ideas
```

### "I want to see high-quality ideas"

```bash
# Via CLI
sqlite3 data/orchestrator.db "SELECT id, title, score FROM ideas WHERE status='promoted' ORDER BY score DESC"

# Via API
curl "https://ao.moss.land/api/ideas?status=promoted"
```

### "I want to check plan details"

```bash
# Via API
curl https://ao.moss.land/api/plans/{plan_id}
```
