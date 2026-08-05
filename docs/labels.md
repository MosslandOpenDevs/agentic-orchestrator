# GitHub Labels Guide

This document describes the labels used in the Mossland Agentic Orchestrator workflow.

> **Note**: The system is **DB-centric**. GitHub Issues and labels exist for visibility;
> SQLite (`data/orchestrator.db`) is the source of truth. Closing an issue does not delete data.

> **`promote:to-plan` is not a "future" label.** Its consumer is implemented
> (`GitHubClient.find_ideas_to_promote` → `BacklogOrchestrator.run_cycle`) and last ran
> successfully on 2026-01-04. What is missing is a *scheduler entry*: `run_cycle` is reachable
> only from `ao backlog run` / `ao backlog process`, and no PM2 process invokes it. The PM2
> `moss-ao-backlog` job is a different task (DB aggregation/retention). Note also that the
> orchestrator adds this label **itself** to any idea scoring >= 7.0, so it is not purely a human
> approval signal today — see [Known Ambiguity](#known-ambiguity-promoteto-plan-has-two-meanings).

## Quick Reference

Source of truth for this table is `Labels.ALL_LABELS` in
[`github_client.py`](../src/agentic_orchestrator/github_client.py).

| Label | Purpose | Who Adds It | Status |
|-------|---------|-------------|--------|
| `type:idea` | Marks an idea issue | Orchestrator | Active |
| `type:plan` | Marks a planning issue | Orchestrator | Active |
| `status:backlog` | In backlog, awaiting action | Orchestrator | Active |
| `status:planned` | A plan exists for this idea | Orchestrator | Active |
| `status:archived` | Low-scoring idea (<4.0) | Orchestrator | Defined; unused on this repo |
| `status:in-dev` | Plan is being implemented | Orchestrator | Defined; unused on this repo |
| `status:done` | Completed | Orchestrator | Defined; unused on this repo |
| `generated:by-orchestrator` | Auto-generated content | Orchestrator | Active (all 65 open issues) |
| `source:trend` | Generated from trend analysis | Orchestrator | Active |
| `promote:to-plan` | Queue idea for planning | Orchestrator (score >= 7.0) **and** Human | Active |
| `processed:to-plan` | Promotion consumed; plan created | Orchestrator | Active |
| `reject:plan` | Reject a plan and regenerate | Human | Defined; unused on this repo |
| `rejected` | Terminal marker written by `reject_plan()` | Orchestrator | Active (closed issues) |
| `curated:keep` | Survived the 2026-06 issue-cleanup triage | Human | Active (12 issues) |
| `promote:to-dev` | Start development from plan | Human | *Not implemented* |

`curated:keep` is the only label in the set that the orchestrator neither adds nor reads. It is a
human triage marker applied during the 2026-06 cleanup (2,803 issues closed) and is what any
future bulk-close pass must exclude.

`rejected` and `reject:plan` are **not** duplicates: `reject:plan` is the input a human adds, and
`rejected` is the terminal marker `reject_plan()` writes afterwards. Do not retire either one.

## Current Workflow (DB-Centric)

The current system uses SQLite as the primary data store. GitHub Issues are created for visibility but are not the source of truth.

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
│                           │                                      │
│                           ↓ (optional)                           │
│   ┌─────────────────────────────────────────┐                   │
│   │      GitHub Issues (For Visibility)      │                   │
│   │   Labels: type:idea, status:backlog      │                   │
│   └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Debate completes** → Ideas generated with scores
2. **Auto-Scorer evaluates** → Assigns status based on score
3. **DB storage** → Primary record in `ideas` table
4. **GitHub Issue created** (optional) → For visibility and tracking

### Status Mapping

Written by `_auto_score_and_save_ideas` in
[`scheduler/tasks.py`](../src/agentic_orchestrator/scheduler/tasks.py).

| DB Status | GitHub Labels | Description |
|-----------|---------------|-------------|
| `promoted` | `type:idea`, `promote:to-plan` | High-quality idea, queued for planning |
| `scored` | `type:idea`, `status:backlog` | Medium-quality, needs review |
| `archived` | *(no issue created)* | Low-quality, DB-only since v0.6.15 |
| `planned` | `type:plan`, `status:backlog` | Plan document exists |

Note that the `promoted` row carries **no** `status:` label. That is deliberate:
`find_ideas_to_promote()` queries `[type:idea, promote:to-plan]`, and adding `status:backlog`
would double-count the issue across two queues that are meant to be exclusive. The six open
issues in that state are correct, not untagged.

Archived ideas (score < 4.0) stopped getting GitHub issues in v0.6.15 — an issue
that is dead on arrival is tracker noise; the DB row remains the record. Issues
created before v0.6.15 with `status:archived` still exist in the closed set.

### Issue Lifecycle (v0.6.15)

The tracker is a mirror of the DB pipeline, and since v0.6.15 it **follows** the
pipeline instead of only accumulating. Two mechanisms, both implemented in
[`scheduler/issue_lifecycle.py`](../src/agentic_orchestrator/scheduler/issue_lifecycle.py)
and run from the backlog cycle (every 4h in production), plus an inline close in
the debate task:

1. **Pipeline-linked closes** (`state_reason=completed`)
   - When an idea is promoted and its plan is created, the `[Idea]` issue gets a
     comment linking the `[Plan]` issue, its labels move to
     `status:planned` + `processed:to-plan`, and it closes. This happens inline
     at promotion time; a reconciliation sweep retries any close GitHub dropped.
   - When a project is generated from a plan (auto at score ≥ 8.0 or via
     `POST /plans/{id}/approve`), the `[Plan]` issue gets a comment naming the
     project, labels move to `status:done` + `processed:to-dev`, and it closes.
2. **Aging sweep** (`state_reason=not_planned`)
   - A `generated:by-orchestrator` issue that is older than
     `backlog.issue_lifecycle.max_age_days` (default 30) with **zero comments**
     is closed. The orchestrator never comments on open issues, so any comment
     means a human showed interest and the issue is exempt.
   - **`curated:keep` and `source:trend` issues are never aged out.** Add
     `curated:keep` to any issue you want to pin open indefinitely.

Closes are capped at `backlog.issue_lifecycle.max_closes_per_run` (default 50)
per cycle, use the list API rather than the search API (the search index
silently omits some issues), and are visibility-only: DB rows are untouched and
any closed issue can be reopened. Disable the whole mechanism with
`backlog.issue_lifecycle.enabled: false` in `config.yaml`.

## Label Categories

### Type Labels

These indicate what kind of issue it is:

- **`type:idea`** - An idea for a new micro Web3 service
  - Created by: Orchestrator (auto-generated from debates)
  - Contains: Idea summary, auto-score results, debate context

- **`type:plan`** - A detailed planning document
  - Created by: Orchestrator (when promoted idea gets a plan)
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

### Known Ambiguity: `promote:to-plan` has two meanings

The docs and the issue template describe this label as a **human approval gate**
(`.github/ISSUE_TEMPLATE/idea.yml`: "If selected, add the `promote:to-plan` label to start
planning"). The code also has the orchestrator apply it **automatically** to every idea scoring
>= 7.0 (`scheduler/tasks.py`, the `status == "promoted"` branch). All six issues currently
carrying it were labelled by the bot in the same second the issue was created; the only
human-applied instances are #7 and #11 from 2026-01-04.

That matters before anyone puts `run_cycle` on a schedule: with both behaviours live, a
high-scoring idea gets a plan generated automatically **and** gets queued for the label consumer,
so plans are generated twice and the human approval gate disappears. Pick one before scheduling:

- keep auto-promotion but give it its own label, leaving `promote:to-plan` purely human; or
- accept that promotion is automatic and correct the docs and issue template instead.

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
│  │  (Auto-generated by orchestrator from debates)           │  │
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

`curated:keep` is deliberately **not** in the registry: it is a human triage marker, so
`setup_labels()` will not recreate it if you delete it.

## Common Scenarios

### "I want to see what ideas were generated"

```bash
# Via CLI
sqlite3 data/orchestrator.db "SELECT id, title, status, score FROM ideas ORDER BY created_at DESC LIMIT 10"

# Via API
curl https://ao.moss.land/api/ideas

# Via GitHub
# Filter issues by label:type:idea
```

### "I want to see high-quality ideas"

```bash
# Via CLI
sqlite3 data/orchestrator.db "SELECT id, title, score FROM ideas WHERE status='promoted' ORDER BY score DESC"

# Via API
curl "https://ao.moss.land/api/ideas?status=promoted"

# Via GitHub
# Filter issues by label:promote:to-plan
```

### "I want to check plan details"

```bash
# Via API
curl https://ao.moss.land/api/plans/{plan_id}

# Via GitHub
# Look for issues with label:type:plan
```
