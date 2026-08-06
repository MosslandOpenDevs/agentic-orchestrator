# Changelog

[한국어](CHANGELOG.ko.md) | **English**

All notable changes to the Mossland Agentic Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **The public dashboard's plan proxies spent the operator's API key for anonymous callers.** v0.6.7 put `MOSS_API_KEY` behind Next.js server routes so the browser would never see it — but keeping a key secret is not keeping its authority: `/proxy/plans/{id}/approve` and `/proxy/plans/{id}/generate-project` accepted unauthenticated POSTs and made the request with the key attached, and ao.moss.land has no user accounts. Anyone could approve plans and start LLM project generations at will (GPU time the debate pipeline needs, plus DB and disk writes). The approve proxy had no caller anywhere in the UI and is deleted; generate-project is off unless `MOSS_ENABLE_BROWSER_PROJECT_GENERATION=1`, and when enabled requires a same-origin browser request and rate-limits to the one concurrent generation the backend allows. Be precise about what that buys: the same-origin check is CSRF protection for browsers, not authentication — a non-browser client sets its own headers — so with the flag on, an anonymous caller can still drive generation at the rate limit. The default-deny flag is the control that matters.
- **Stored XSS through debate messages.** Ideas, plans and debate content are LLM output written from RSS items and GitHub issues, and they were rendered by piping `marked.parse()` straight into `dangerouslySetInnerHTML`. `marked` does not sanitize (its `sanitize` option was removed in v5) and no sanitizer was installed, so raw HTML in a model response executed on our origin. Two token-level guards now cover every render path: raw HTML is escaped to visible text, and link/image URLs are limited to safe schemes — marked's `cleanUrl` only runs `encodeURI`, which leaves `javascript:` intact. 12 regression tests cover the payloads.
- **Generated project's docker-compose published PostgreSQL with hardcoded superuser credentials** (`postgres/postgres` on `5432:5432`). Port no longer published; credentials must come from the environment.
- **Next.js 16.2.9 → 16.3.0 and sharp 0.34.5 → 0.35.3**, both reported high by `npm audit --omit=dev` (middleware/proxy bypass, Server Action DoS and SSRF, cache confusion; sharp's inherited libvips CVEs). Declared floors raised so a resolve without the lockfile cannot land back on a vulnerable version.

### Added
- **Second-pass promotion review — the strong model's work is no longer graded only by the weak one.** The pipeline had an inversion: debates run on gpt-5.4-mini, but the gate deciding whether their output became a plan (and then a scaffolded project) was a local gemma3:4b re-score. On 2026-08-05 that scorer returned 8.0 for twenty-two consecutive ideas, several of them near-duplicates, and three each scaffolded a project. Promotion now takes two signatures: the local scorer still grades everything (free, and a fine filter for obvious rejects), and only ideas it wants to **promote** go to the paid reviewer (`scoring/second_pass.py`, new `review` paid tier), which sees the idea plus the local verdict and returns CONFIRM / DEMOTE / REJECT with a reason. The prompt states the local scorer's inflation explicitly so the reviewer does not anchor on it.
  - **When the reviewer cannot run, the idea is HELD, never promoted.** No key, exhausted budget, provider outage, unparseable reply, per-cycle budget spent — every one of those lands on `scored`, where triage can re-offer it later. Auto-approval and project generation are downstream of promotion, so a silent reviewer can never let an unvetted idea reach either. A response that **degraded to a local model is also refused**: the paid tier degrades to local by design, and a local answer here is the first opinion twice, not a second one.
  - Cost is small because the funnel is narrow: ~11 cluster representatives per debate, of which only promotion candidates are reviewed (`min_local_score`, `max_reviews_per_cycle`) — roughly $0.03 a debate.
  - 25 new tests (`tests/test_second_pass_review.py` + 5 in `tests/test_debate_pipeline_gate.py`). The integration tests caught a real hole while being written: with the per-cycle review budget spent, candidates were being promoted **unreviewed** — the exact failure the gate exists to prevent. Fixed, and mutation-verified along with the two other safety properties (treating UNAVAILABLE as promotable, and accepting a locally-degraded review).

### Tests
- **The diversity gate's wiring is now covered, not just its algorithm.** `tests/test_idea_clustering.py` proved the clustering module sound in isolation, but every bug the gate exists to fix was a *wiring* bug — `result.all_ideas` ignoring the already-computed `selected_ideas`, and one `final_plan` document copied byte-identically into every promoted plan. New `tests/test_debate_pipeline_gate.py` (9 tests) drives the real `_auto_score_and_save_ideas` over the real 24 golden ideas against an in-memory DB with a scripted scorer and no GitHub client — so it also runs while the shared GPU is unavailable. It pins: only representatives are scored, losers are persisted as `duplicate` rows pointing at a live representative and are never mirrored to GitHub, the whole batch is accounted for, at most one plan carries the debate document, a plan without the document is never auto-approved, disabling the gate is a true no-op, and a clustering failure falls open to the pre-gate behavior instead of taking the debate down. Mutation-verified: reverting the gate to `all_ideas`, restoring the `final_plan` copy, and skipping duplicate persistence each fail their corresponding test.

### Fixed
- **Removed `SCORING_NUM_CTX = 4096`, which had become the problem it was added to solve.** v0.6.18 pinned idea scoring to a 4k context believing that 16k loads on the shared Ollama hung indefinitely while a resident 4k answered instantly. Re-measured on 2026-08-06 jointly with the other team on that host: a **non-resident context loads in 4.46 s and completes normally** — the hang did not reproduce, and 16384 actually uses *less* VRAM than 8192 (2.89 GB vs 3.03 GB). The host serves exactly **one model instance at a time**, so each distinct `num_ctx` is a distinct instance and any per-task pin evicts whatever is resident: with both services converged on 16384, our scoring calls were the one thing still flipping the instance back to 4k and forcing a reload each way. One context size for the whole pipeline is now the rule, and a test pins that invariant (`test_no_task_pins_its_own_num_ctx`) rather than pinning the old constant. Also measured while verifying: the host **does serialize** (a 5-token request fired 3 s into a 2000-token generation took 8.09 s against a 0.50 s baseline), but at 198 tok/s and our cadence the combined duty cycle is ~2–3%, so serialization costs seconds occasionally rather than the 1800 s stalls — removing it entirely needs `OLLAMA_NUM_PARALLEL` on a host neither team can reach.
- **One failed frontend build wedged the deployer permanently.** Builds stage into `website/.next.new` so a failure can never leave the live `.next` half-written — but the staging dir was only created when it was *absent*, so a failed build's remains, build cache included, were inherited by every build after it. Proven on the server: the identical 379-package install failed with the leftover in place and succeeded the moment the directory was removed. The staging dir is now cleared before every build, and the warm-cache seed always runs instead of being skipped whenever a leftover existed.
- **Every deploy failed, and then its rollback failed, because `npm ci` dropped the devDependencies `next build` needs.** The poller inherits `NODE_ENV=production` from PM2 and npm reads that as `--omit=dev`, so the install landed 45 of 382 packages and the build died on `Can't resolve '@vercel/turbopack/postcss'`. The rollback rebuilt the previous commit exactly the same way, so it failed too and every tick logged `CRITICAL rollback did not come back healthy`. Nothing reached users — builds go to a staging dir and are swapped in whole, so a failed build never touches the live `.next`, and the running processes kept serving the last good bundle — but auto-deploy was wedged. Fixed in two places on purpose: `scripts/deploy.sh` passes `--include=dev`, and `website/.npmrc` pins `include=dev`. The second is the one that unsticks a server already in the loop: bash parses the whole script at startup, so even the deploy carrying the fix runs the *old* deploy.sh — while the checkout, `.npmrc` included, is already the new commit by the time `npm ci` runs.
- **A deploy that cannot check CI no longer fails silently forever.** `ci_conclusion` collapsed every non-answer into `unknown`, and the gate logged one line — "CI: status unavailable (network/API)" — and deferred. That is correct for a network blip and catastrophic for the other cause: without a token the query goes out anonymous, GitHub rate-limits the server's shared IP with a 403, and *every* subsequent tick defers too. Deploys stop permanently and the only symptom is a log line that reads like transient noise. Three changes: `ci_conclusion` now distinguishes **401/403 (`unauthorized`)** from a transient failure by reading the HTTP status, and an `unauthorized` result logs an explicit "DEPLOYS ARE BLOCKED" with the cause and the fix and fires the alert webhook; a genuinely undeterminable status is counted per target SHA, and once `DEPLOY_CI_UNKNOWN_ALERT` ticks (default 3, i.e. ~15 minutes) have failed in a row it escalates to `ERROR` plus an alert instead of staying quiet; and `GITHUB_TOKEN` is read out of `.env` when absent from the environment, so a manual `bash scripts/deploy.sh` over SSH authenticates like the PM2 poller does (the poller inherits it via `ecosystem.config.js`; an SSH session does not, which is how this was found). The dotenv read is a targeted key lookup, not a `source` — deploy.sh must not inherit whatever else lives in that file. 5 new tests; all three guards mutation-verified by reverting each one and confirming its test fails.

- **A failed debate turn no longer silently becomes a gemma turn.** When a paid-tier call failed, the router fell through to its generic handler and reran the request on local Ollama — so one debate round could mix gpt-5.4-mini and gemma3:4b output with nothing in the logs saying so, and the retry landed on the very congested GPU path the tier exists to escape (three debates died there on 2026-08-05). A pinned tier now retries **itself** (`MOSS_PAID_TIER_RETRIES`, default 2, short backoff) and then raises; the scheduler's next cron tick is the real retry. Untagged calls keep their local fallback unchanged.
- **`throttling.ollama.max_concurrent_requests` was dead config.** No semaphore existed anywhere: the throttle held its lock only to update state and released it before the HTTP call, so it spaced request *starts* by `min_request_interval` and then let every caller sit on the GPU at once. A divergence round fans out 8 agents through `asyncio.gather` — all 8 reached the single shared GPU together, which is the load pattern behind the KV-cache stalls. Requests now hold an in-flight slot for the duration of the HTTP call, on both the generate and chat paths; an explicit `0` still means "no cap" rather than deadlock. Measured with a fake transport: 8 concurrent agents at limit 1 peak at 1 in flight (previously 8).

### Added
- **Debate diversity gate — one debate no longer ships one idea 24 times.** On 2026-08-05 a single debate emitted 24 ideas of which 8 were the same payment gateway in 8 wordings; all 24 title strings were distinct, so the 6-token prefix fingerprint caught none of them, three same-theme ideas were each promoted, and each scaffolded a project whose plan document was **byte-identical** (three plans of exactly 16,453 chars). Four root causes, all fixed:
  - **The creativity technique was assigned per ROUND, not per agent** (`protocol.py`): the key was `round_num` alone, so all 8 agents of a round received the same SCAMPER/lateral prompt — and since the round runs concurrently off one `self.ideas` snapshot, nothing else told them apart either. A capable model given identical instructions returns identical thinking; gemma3:4b's incoherence had been supplying diversity by accident. Now each agent draws its own technique and the assignment rotates by round, so 8 agents span all six techniques instead of one.
  - **A clustering gate before scoring, DB and GitHub** (new `scheduler/idea_clustering.py`): hand-rolled TF-IDF cosine with greedy max-degree star clustering — stdlib only, deterministic, O(n²). Chosen over three alternatives by measuring all four against the incident's own 24 ideas: at `threshold: 0.18` it yields pairwise precision **1.00** (11 clusters, zero cross-theme merges) and collapses the 8-member gateway theme to exactly one representative. **Tune on precision, never on cluster count** — the 6-7 themes an eyeball count expects *are* reachable at 0.11-0.14, but only by merging distinct ideas (precision 0.60-0.79), and a merged idea is deleted for good because only the representative proceeds. A `min_shared_terms: 2` rail makes a mis-set threshold survivable: 24 unrelated ideas stay 24 clusters even at threshold 0.04, where the unguarded version collapses them to 15.
  - **Non-representatives are kept, not dropped**: they are stored as `duplicate` rows carrying `duplicate_of`, outside backlog triage's queue, with no GitHub issue and no LLM score. A wrong merge is therefore auditable and reversible rather than a silent deletion.
  - **One plan (and one project) per debate**: the planning phase produces exactly one `final_plan` document, and it was being copied into every promoted idea's plan. It now goes to the first promotion only; auto-approval additionally requires the plan document to be present, so a later promotion can no longer scaffold a project from an empty plan.
- 14 new tests in `tests/test_idea_clustering.py` replay the incident from `tests/data/golden_debate_x402.json` (the real 24 ideas) with no external effects, and pin the precision guards, the low-threshold rail, degenerate batches (n=0,1,2) and determinism.
- **Debates now run on gpt-5.4-mini via a paid-tier allowlist — the rest of the pipeline stays local and free.** The debate was the one task where local gemma3:4b visibly capped quality (score inflation — 88% of triaged ideas promoted; generic "Mossland X + Y Implementation" titles) and the one most exposed to the shared GPU's congestion (it needs 16k context locally; both debates failed on 2026-08-05 for exactly that reason). New config `llm.paid_tiers`: a call site may name a tier (`route(..., paid_tier="debate")`, tagged at all four debate call sites — divergence, convergence, planning, quality gate); the router honors it only when the tier is enabled in config, the provider is initialized, and the budget has headroom. **Two independent switches must both be on before a cent is spent**: server `.env` `MOSS_LOCAL_LLM_ONLY=false` (enables paid providers at all) and the tier's `enabled: true` in config (names who may use them) — flipping the env flag alone provably spends nothing (pinned by test: no `force_api` callers exist, and `_select_model` prefers local everywhere). Every missing precondition — tier disabled, no provider/key, exhausted budget, `force_local`, explicit `model` — silently degrades the debate to local gemma rather than killing it. Budget raised $1→$2/day, $30→$45/month — and made those numbers real: the `budget:` block in config.yaml had never been read (limits came only from `DAILY_BUDGET_USD`/`MONTHLY_BUDGET_USD`, whose defaults happened to match the file), so raising it would have changed nothing and the tier would have silently degraded to local part-way through each day. config.yaml is now the source of truth, env vars still override. Ceiling is 38 paid calls per debate (divergence 8×3, convergence 4×2, planning 3+3, plus syntheses/quality) ≈ $0.30-0.50, tracked in the existing `api_usage` table and `/usage` endpoint; `gpt-5.4-mini` registered in the hierarchy and the pricing table at $0.75/$4.50 per M.
- **OpenAI provider: `max_tokens` → `max_completion_tokens`.** GPT-5-family models reject the legacy parameter with a 400 — verified live against gpt-5.4-mini before shipping (a $0.0001 probe; temperature is accepted). Without this the paid tier would have been a silent no-op: the router catches the 400 and falls back to local gemma on every call. Pre-merge adversarial review (14 agents) caught four more before merge, all fixed here: the sync OpenAI SDK client was being called straight from a coroutine (blocking the event loop and serializing each debate round's concurrent agents — now offloaded with `asyncio.to_thread`); the SDK's default `max_retries=2` silently re-sends on timeouts and 429/5xx while OpenAI bills every attempt and only the returned one reaches `record_usage` (now `max_retries=0` — the router already retries once and then falls back to local); an empty-but-billed completion (GPT-5 reasoning tokens can consume `max_completion_tokens` and return `finish_reason="length"` with no text) was passed through as an empty debate turn (now raises so the router falls back); and a malformed tier value in YAML (`debate: true`) would raise `AttributeError` outside the try block on every debate call, killing the debate instead of degrading it (now dropped at load). 21 tests in `tests/test_paid_tier_routing.py` pin the safety contract (flag-alone spends nothing, every degradation path, registry/pricing entries, the provider parameter, and a source invariant that all four debate call sites carry the tier tag).

### Removed
- **Removed the generated project committed to `src/projects/` in January.** It arrived via the scaffold's `_git_commit_and_push`, which ran unconditionally after every generation until v0.6.15 disabled it — the same path that produced the server's local commits on main. Nothing in the repo referenced it, it sat outside the `output_dir` the generator actually writes to, and generated projects are gitignored by design ("regenerated from plans on demand; keeping them out of git avoids repo bloat"). It also could not be built: no lockfiles, so `npm ci` failed before anything else, and 211 TypeScript errors across its backend and frontend. Recoverable from history at `958f8ea` if a sample of generator output is ever wanted.

### Fixed
- **The auto-deploy could not build the dashboard, and the reason was in the poller's own environment.** `moss-ao-deploy` runs with `NODE_ENV=production`, which npm reads as `--omit=dev`, so `npm ci` skipped postcss, @tailwindcss/postcss and typescript -- exited 0 with 45 packages instead of 382 -- and `next build` then died on "Can't resolve '@vercel/turbopack/postcss'". It stayed hidden because `npm ci` only runs when `website/package*.json` changes, and the server's node_modules had been installed by hand long before; the first dependency bump in months is what fired it. The install now passes `--include=dev` explicitly. The staged-build and rollback guards did their job throughout -- the failed build never reached the live `.next` and ao.moss.land kept serving.
- **A deploy that cannot check CI no longer fails silently forever.** `ci_conclusion` collapsed every non-answer into `unknown`, and the gate logged one line — "CI: status unavailable (network/API)" — and deferred. That is correct for a network blip and catastrophic for the other cause: without a token the query goes out anonymous, GitHub rate-limits the server's shared IP with a 403, and *every* subsequent tick defers too. Deploys stop permanently and the only symptom is a log line that reads like transient noise. Three changes: `ci_conclusion` now distinguishes **401/403 (`unauthorized`)** from a transient failure by reading the HTTP status, and an `unauthorized` result logs an explicit "DEPLOYS ARE BLOCKED" with the cause and the fix and fires the alert webhook; a genuinely undeterminable status is counted per target SHA, and once `DEPLOY_CI_UNKNOWN_ALERT` ticks (default 3, i.e. ~15 minutes) have failed in a row it escalates to `ERROR` plus an alert instead of staying quiet; and `GITHUB_TOKEN` is read out of `.env` when absent from the environment, so a manual `bash scripts/deploy.sh` over SSH authenticates like the PM2 poller does (the poller inherits it via `ecosystem.config.js`; an SSH session does not, which is how this was found). The dotenv read is a targeted key lookup, not a `source` — deploy.sh must not inherit whatever else lives in that file. 5 new tests; all three guards mutation-verified by reverting each one and confirming its test fails.
- **A failed debate turn no longer silently becomes a gemma turn.** When a paid-tier call failed, the router fell through to its generic handler and reran the request on local Ollama — so one debate round could mix gpt-5.4-mini and gemma3:4b output with nothing in the logs saying so, and the retry landed on the very congested GPU path the tier exists to escape (three debates died there on 2026-08-05). A pinned tier now retries **itself** (`MOSS_PAID_TIER_RETRIES`, default 2, short backoff) and then raises; the scheduler's next cron tick is the real retry. Untagged calls keep their local fallback unchanged.
- **`throttling.ollama.max_concurrent_requests` was dead config.** No semaphore existed anywhere: the throttle held its lock only to update state and released it before the HTTP call, so it spaced request *starts* by `min_request_interval` and then let every caller sit on the GPU at once. A divergence round fans out 8 agents through `asyncio.gather` — all 8 reached the single shared GPU together, which is the load pattern behind the KV-cache stalls. Requests now hold an in-flight slot for the duration of the HTTP call, on both the generate and chat paths; an explicit `0` still means "no cap" rather than deadlock. Measured with a fake transport: 8 concurrent agents at limit 1 peak at 1 in flight (previously 8).

### Tests
- **The diversity gate's wiring is now covered, not just its algorithm.** `tests/test_idea_clustering.py` proved the clustering module sound in isolation, but every bug the gate exists to fix was a *wiring* bug — `result.all_ideas` ignoring the already-computed `selected_ideas`, and one `final_plan` document copied byte-identically into every promoted plan. New `tests/test_debate_pipeline_gate.py` (9 tests) drives the real `_auto_score_and_save_ideas` over the real 24 golden ideas against an in-memory DB with a scripted scorer and no GitHub client — so it also runs while the shared GPU is unavailable. It pins: only representatives are scored, losers are persisted as `duplicate` rows pointing at a live representative and are never mirrored to GitHub, the whole batch is accounted for, at most one plan carries the debate document, a plan without the document is never auto-approved, disabling the gate is a true no-op, and a clustering failure falls open to the pre-gate behavior instead of taking the debate down. Mutation-verified: reverting the gate to `all_ideas`, restoring the `final_plan` copy, and skipping duplicate persistence each fail their corresponding test.

## [0.6.18] - 2026-08-05
- **Restoring the database is a command now, not a runbook.** `restore-db` validates the snapshot, refuses while another process is writing, copies the current database aside so the restore itself is reversible, removes the WAL sidecars, swaps the file in atomically and verifies the result: `python -m agentic_orchestrator.scheduler restore-db [--list] [--from SNAPSHOT]`. The step it exists to enforce is deleting `orchestrator.db-wal` first. With a writer that did not close cleanly -- a crash or an OOM kill, i.e. the situation you are in when you reach for a backup -- copying a snapshot over the database file makes SQLite replay the old WAL on top of it: the restore silently does not happen and `PRAGMA integrity_check` still reports "ok". `tests/test_restore.py::TestTheHazard` reproduces exactly that (a 1-row snapshot restoring as 401 rows, integrity ok) so the reason for each guard stays visible.

### Changed
- `project.auto_generate.enabled: false` — paused until the diversity gate has been verified against a live debate. Re-enable after that.
- **Monthly API budget $45 → $100.** The v0.6.19 pair was inconsistent: at $2/day the monthly cap must clear $62 (daily × 31) or the month dies before the day does. Measured cost of one debate on gpt-5.4-mini is **$0.446** (38 calls, 273k input / 54k output — debate context accumulates across rounds, so input dominates), i.e. ~$1.78/day and ~$54/month at 4 debates/day; the old $45 cap would have bitten around day 25 and silently degraded every later debate to local gemma. $100 covers the measured usage plus manual runs.
- **The dashboard no longer invents data.** `ScoreBreakdown` drew each idea's per-dimension scores as `overall + Math.random() * 1.5`, re-rolled on every render and printed to one decimal beside the real weights; `TrendSparkline` invented a seven-day signal history the same way and derived "momentum" and "velocity" from it; `IdeaDetail` passed a consensus percentage of `70 + 5 per debate, capped at 95`. None of it exists in the database, and it was rendered on pages titled "transparency". The generators are gone; the components render what they are given, with an explicit "not recorded" note otherwise. The fetchers also fell back to demo fixtures not only on API failure but on a legitimately empty list, with nothing marking the result synthetic — empty is now empty. The footer's "System Online" badge and the dashboard's "SYSTEM ONLINE" banner were literal text shown regardless of state; both report what `/status` actually said, including "unknown".
- **Frontend/backend contract drift.** `fetchIdeas`/`fetchPlans` replaced the backend UUID with `index + 1`, so the Backlog page's detail button always 404'd. `IdeaCard`'s status map used the demo vocabulary, so seven of eight real `IdeaStatus` values — including `rejected` and `archived` — rendered as a grey "Backlog" chip. Debate views tested for `in-progress`, a status the backend has never emitted (it is `active`), which left live mode permanently off and made the transparency page's "in progress" filter return zero rows. `PlanDetail`'s `regenerate --force` button sent `force_regenerate: false`; a failed job poll left the spinner running forever; a `ready_with_warnings` project rendered a blank panel.
- **CI now covers the dashboard and installs from a lockfile.** `uv.lock` is committed and CI installs with `uv sync --frozen`, the same lock production installs from — previously each resolved its own graph from mostly lower-bound pins, so CI, a fresh deploy and a rollback of one commit could run different packages. A new `website` job runs lint, typecheck, tests, build and a production-only audit; the three generated packages currently in the tree fail `npm ci` outright and CI stayed green. Actions are pinned to commit SHAs and the workflow declares `contents: read`. The stale `pnpm-lock.yaml` (referencing a removed dependency, so the documented `pnpm install` failed immediately) is deleted and the READMEs follow the deploy path's `npm ci`.
- **An `ecosystem.config.js` change could sit unapplied indefinitely.** PM2 process definitions are deliberately not re-registered by the deployer (doing that from inside a PM2-managed process is the 2026-08-05 cron-contamination incident), but the reminder was a single log line on the deploy that carried the change — HEAD then moved past it and every later tick was a silent no-op. The pending change is recorded in `logs/.ecosystem-pending` now and re-logged on every run until an operator applies it and removes the file.
- OpenGraph metadata pointed at `/og-image.png`, which existed neither in `public/` nor as a route, so every social share fetched a 404. Generated by `app/opengraph-image.tsx` now.

### Fixed


- **A deploy killed mid-flight can no longer masquerade as a success.** `git reset --hard` advances HEAD *before* the build and health check run, so a poller killed in between (PM2 `max_memory_restart` sends SIGKILL, OOM, reboot) left HEAD at the new commit with the old build still live — and every later tick compared HEAD to `origin/main`, read "up to date", and hid the failure forever. `scripts/deploy.sh` now keeps its own state: the SHA of the last **successful** deploy in `.git/moss-ao-deployed-sha` (inside the git dir, where `reset --hard` cannot reach), written only after the health check passes. That state — not HEAD — is the tick baseline; when it disagrees with HEAD the deploy is treated as unfinished and retried, and the change-classification diff is the union of `state..target` and `HEAD..target` so a half-finished deploy still rebuilds everything it owes. Rollback now also returns to the last *known-good* SHA rather than the pre-tick HEAD, which after a crash may itself be the broken commit.
- **Server-local commits are no longer silently destroyed.** The dirty-tree guard only caught uncommitted edits; a commit made by hand on the server was thrown away by `reset --hard` without a word. A `git merge-base --is-ancestor HEAD origin/main` guard now aborts the deploy (with the offending commits listed and a webhook alert) whenever HEAD is ahead of or diverged from the remote; `--force` remains the deliberate override.
- **Failed deploys back off instead of re-running the full cycle every 5 minutes.** Each attempt at a target SHA is journaled in `.git/moss-ao-deploy-attempt` *before* any work starts — so even a SIGKILLed attempt counts — and further attempts at the same SHA wait `DEPLOY_RETRY_BASE_MIN × 2^(n-1)` minutes (default 5, capped at `DEPLOY_RETRY_MAX_MIN`, default 60) instead of repeating the forced DB snapshot, build, double restart, rollback and webhook alert on every tick. A new commit on the remote resets the journal immediately; `--force` ignores the wait; success clears it.
- **The frontend build is atomic.** `npm run build` used to write straight into `website/.next` while moss-ao-web was serving from it, so a failed or killed build left the live dir half-written. The deploy now builds into a staging dir (`website/.next.new` — `next.config.ts` honours `NEXT_DIST_DIR`, unset everywhere else) and swaps it in with two renames immediately before the web restart, only after the whole build succeeded. Stale `.next/types` from the old commit are dropped pre-build (they are typecheck-only and would fail the staged build when a page is deleted), and the previous build cache is seeded into the staging dir so builds stay incremental. Verified against a real Next 16 build: the staged build serves correctly after the rename and the build does not dirty any tracked file.
- **A SIGKILLed poller no longer wedges the deploy lock for 90 minutes.** SIGKILL skips bash's EXIT trap, so the lock directory survived and every tick until the `DEPLOY_LOCK_STALE_MIN` age-out was skipped. The lock now records its owner's PID; a lock whose owner is no longer alive is reclaimed on the very next tick, with the age check kept as a backstop for unreadable PID files. On the prevention side, the poller's `max_memory_restart` goes from 1G to 3G in `ecosystem.config.js` — the Next.js build runs inside the poller's memory budget and 1G was close enough to invite exactly that SIGKILL.
- **deploy.sh is safe to self-deploy.** The whole script body now lives in `main()`, invoked on the last line. bash reads scripts incrementally, so without the wrapper an in-place update of the running file could have bash continue at a byte offset of the new content. (Same construction, for the same reason, as mossland-website-2026's autodeploy.sh.)
- **Detail-route share metadata now follows the unified family convention** (PR #2922 review, P2-1). The four `/{ideas,plans,projects,signals}/[id]` routes still returned their pre-#2922 metadata — `Plan - MOSS.AO`, `siteName: 'MOSS.AO'`, `twitter:card summary` — and, because Next.js merges metadata shallowly (a child `openGraph` replaces the root object wholesale), every deep link also dropped the shared og:image. The convention now lives in one place (`website/src/lib/metadata.ts`), the root title is a `default`/`template` pair so child routes stay unbranded (`Plan` renders as `Plan — MOSS.AO · Mossland`), and all four routes build their metadata via `detailMetadata()`. Verified against the built app: detail pages now serve the templated title, `og:site_name Mossland`, `summary_large_image`, and an absolute og:image URL. The `/og-image.png` asset itself landed separately in 0.6.17 (PR #2953), so every detail route now serves the same existing image.
- **Ecosystem bar accessibility** (PR #2922 review, P3-1/P3-2). The site name and its role concatenated in the accessible name — the visual gap was CSS margin only, so screen readers, voice control, and text search saw "BRIDGEGovernance OS"; an explicit space text node makes it "BRIDGE Governance OS". The two external links (BRIDGE, Algora) now disclose their new-tab behavior with a visible `↗` marker plus localized screen-reader text (`ecosystem.newTab`: EN "opens in new tab" / KO "새 탭에서 열림", W3C technique H83).
- **Idea scoring pinned to the 4k Ollama context — backlog triage no longer starves when the shared GPU can't load 16k.** The v0.6.15 fix made every request send `num_ctx` (default 16384) because trend prompts overflow 4k. But each distinct `num_ctx` is its own model instance server-side, and on 2026-08-05 afternoon the congested shared GPU hung **every** 16k/8k KV-cache load for ~30 min (per-call 1800s timeouts) while the already-resident 4k instance kept answering in <1s — the 12:25 debate failed after 90 min, the 16:15 trend run saved 0 trends, and the first aggressive-consumption triage tick (16:45, 25 ideas selected) got 1 idea skipped per 30 min. The triage fallback detector did exactly its job (timeouts → `scorer_unavailable`, zero strikes handed out — live-verified at 17:15/17:45), but consumption was effectively zero. Scoring's prompt (~2.5k tokens) + 1,024-token output fit 4,096 with headroom, so `IdeaScorer` now passes `SCORING_NUM_CTX = 4096`: triage keeps consuming even when big-context loads hang. Plumbing follows the v0.6.15 schema lesson — `num_ctx` is forwarded per-call through `route()` → all three `_call_ollama` sites (both fallbacks included) → the provider payload, where a per-call value beats the throttle default; 4 new tests pin the payload override, the None-keeps-default path, the router plumb, and the scorer's constant. Big-context tasks (trends/debates) still need the 16k instance and still require the GPU box itself to recover — that part is infra, not code.
- **Follow-up from an adversarial review of the fixes above.** Sixteen defects the first pass introduced or failed to close, each verified by an independent refutation attempt before being accepted. The load-bearing ones: the markdown sanitizer left image `alt` unescaped (marked escapes `title` but not `alt`), a zero-click XSS since the attacker also controls `src`; and it validated URL schemes against the raw string, so `javascript&#58;alert(1)` — no literal colon — read as scheme-less and came back to life when the HTML parser decoded the attribute. `PRAGMA journal_mode=WAL` ran before `busy_timeout` and SQLite does not run the busy handler for a journal-mode change, so the one-time migration of the still-`delete`-mode production database would have raised out of the connection hook on the first contended connect, taking `ensure_schema()` and every request with it. Committing `uv.lock` while the deploy script still ran a non-frozen `uv sync` meant one re-resolution would dirty a tracked file and the dirty-tree guard would then abort every 5-minute tick until a human intervened; the same commit left `uv.lock` out of the change classifier, so a lock-only dependency bump was classified "docs only" and never installed at all. Recording a pending `ecosystem.config.js` change used an unguarded append that could abort a deploy after the checkout moved but before the build. The QA gate was made unpassable in its default configuration while the max-revisions branch still routed failures to DONE, so the net effect was five wasted regeneration cycles before the same wrong outcome. `backup-db` reported a corrupt database as "nothing to snapshot", which let the deploy proceed without a restore point in exactly the state that needs one. The dashboard still printed a fabricated `Confidence: MED (±0.8)`, a hard-coded `uptime: 99.9%`, a `RUNNING` badge that stayed green through a total outage, and a `last_run` read off the viewer's own clock. Three tests were vacuous (they passed against the pre-fix code) and were rewritten until removing the fix fails them.
- **Three more from the same review, found by working through the findings it flagged but did not have budget to verify.** A database outage would have put the deployer in a loop: `/ready` fails, the deploy rolls back, and five minutes later it tries the same commit again — restarting the API every tick for the length of an unrelated outage. The deployer now distinguishes the three states (ready / up-but-not-ready / down) and defers on the middle one, where a deploy can neither be verified nor help. `_get_existing_project` selected with no ordering, and retrying a failed generation now leaves two rows for one plan, so the stale `error` record could shadow the successful one and re-trigger generation indefinitely. And enforcing the Ollama concurrency cap is a real behaviour change: debate rounds fire their agents with `asyncio.gather`, and `max_concurrent_requests: 1` had never been read before, so this genuinely serializes them where it previously did not. Output is unaffected; wall-clock is not. config.yaml now says so and names the knob to relax if debates approach the 90-minute cycle budget.
- **The rest of the review's backlog, worked through by hand.** `/status` reported `cache` and `llm_router` as healthy while probing neither; they now say `unknown`, which is what the endpoint actually knows (the 5-minute scheduler check is what measures the router). The dashboard printed `total_adapters: 9` against a backend that registers 11, and gave pulsing green "online" dots to every configured LLM — including `qwen3-embedding:0.6b`, which is not installed on the production host and which no code path calls. The backlog's "In Development" tab had a count but no render branch, so selecting it showed an empty page whatever the count claimed; it is gone, and the "In Development" stat tile now counts generated projects instead of the hard-coded 0 it always reported. `PlanDetail`'s plan badge keyed on `in-review`, a status the backend has never emitted. A project row stuck at `generating` — which nothing clears when the run that claimed it is killed — blocked that plan from ever generating again; it now expires after two hours, and the panel watches it with a bounded poll instead of spinning forever. Demo signals written by the migration script claimed `source="rss"`, hiding them in exactly the source-mix statistics its own docstring worried about, and their id overflowed the declared column width.
- **Every database Session in a process shared one connection, and therefore one transaction.** File SQLite used `StaticPool`, so a rollback in any request discarded every other request's uncommitted writes, and a long project generation held the whole API inside its transaction. `StaticPool` is now limited to `:memory:` (where the connection *is* the database); file databases pool normally and get `journal_mode=WAL` plus a 30s `busy_timeout`. **Restore procedure changed**: delete `data/orchestrator.db-wal`/`-shm` before copying a snapshot over, or SQLite replays the old WAL onto the restored file.
- **Time decay was corrupting the stored signal score to weight nothing.** `_apply_time_decay_to_signals` multiplied `Signal.score` in place and let the trend task commit it, so a signal older than 48h decayed again every two hours (1.0 → 0.2 → 0.04 → …), permanently rewriting the value the API sorts and filters on — while the decayed number never reached the analyzer, because `FeedItem` has no score field. The weight is transient now and is applied *before* batch selection, where it actually decides which signals the LLM sees. The freshness histogram read `s.metadata`, which on a declarative model is SQLAlchemy's `MetaData`, so it always reported 100% fresh. Scores already decayed in production cannot be recovered from the code change; they are replaced as signals turn over.
- **Auto-deploy had three fail-open paths.** A commit with zero check runs was logged as "no checks reported -- proceeding" and deployed unverified, though that state is usually just CI not having registered yet; `skipped`/`stale` conclusions counted as green because they were merely absent from the failure list; and a failed pre-deploy DB snapshot only warned, so a change could be applied with no restore point. All three now defer or refuse. `backup-db` exits 2 for "nothing to snapshot" so an empty database stays benign, and `DEPLOY_REQUIRE_CI_JOBS` can pin the exact jobs that must have passed.
- **The post-deploy health check verified liveness, not readiness.** `/health` answers 200 whenever the process is up — it did so throughout the 2026-07 incident while every DB-backed endpoint returned 500 — so a deploy that broke the database would have been recorded as `DEPLOYED`. New `/ready` endpoint reads a real table and answers 503 when it cannot; the deployer gates on that.
- **Retention pruned nothing, silently.** Old trends and debate sessions are referenced by surviving Ideas and Plans with no `ON DELETE` policy, so the sweep raised `FOREIGN KEY constraint failed` — and because both sweeps shared one transaction, one failure rolled back both, every four hours, behind a single warning line. Referenced parents are provenance (`/ideas/{id}/lineage` walks them) and are kept and counted; unreferenced rows are pruned; each sweep gets its own transaction.
- **QA passed projects that had nothing to check.** A missing implementation directory, no test files, pytest not installed and no reachable reviewer all reported pass/7.0 — the default required score — so an empty project scored 7.0/10 and was routed to DONE. The gate now passes only on positive evidence. Separately, it ran model-written tests with `python -m pytest` in the orchestrator's own environment (pytest executes arbitrary code at collection time, before any assertion); execution is now opt-in via `MOSS_RUN_GENERATED_TESTS` and off by default. Reachable only from the manual `ao` CLI, which is why this never caused an incident.
- **Retrying a failed project generation did nothing and reported success.** The API allows an `error` project to be retried, but the scaffold returned early for *any* existing row — `success=True`, `project_path=None`, no work done — and the background job recorded that as "completed".
- **Manual plan approval lost its audit trail.** `extra_metadata` is a plain JSON column, not `MutableDict`, so SQLAlchemy never saw the in-place mutation and `manually_approved`/`approved_at` were dropped for every pipeline-created plan. The background generation task also closed its session only on the success path, leaking a connection and an open transaction per failure.
- **`?limit=-1` bypassed the documented pagination caps.** Limits declared only an upper bound and SQLite reads `LIMIT -1` as no limit, so a single request could serialize every matching row. All limits now require `ge=1`.
- **`/adapters` was an unauthenticated third-party fan-out.** Every request built all eleven adapters and awaited their external health probes sequentially, each with a ~10s timeout. Probes now run concurrently under a 5s per-probe budget behind a 60s shared cache.
- **Ollama reported healthy when it was unreachable.** `health_check` called a helper that swallows every network, HTTP and JSON error into an empty list, then returned `"healthy"` unconditionally. It now reports `error` when the fetch fails and `degraded` when the server lacks the model everything runs on; the scheduler's health task also read a `models` key that `health_check` has never returned, so it always logged 0 models. The interval throttle computed its wait under the lock but claimed the slot only after sleeping, so concurrent callers woke together and it throttled nothing; slots are reserved in the same critical section now. `max_concurrent_requests`, documented in config.yaml as "1 = sequential only", was read by nothing and is now a real semaphore.
- **A malformed response from a sister service blanked every page.** `NpcCityStrip` cast `npc.moss.land`'s payload straight to `Headline[]`, so a *successful* reply in an unexpected shape (`{"headlines": {}}`) threw on `.length`/`.slice` outside the fetch's try/catch. It is a server component in the root layout with no boundary above it. Every field is validated now, unusable records are dropped, and a `global-error.tsx` backstops the root layout.
- **`SignalStorage` reads were unusable.** They returned live ORM rows from sessions that commit and close on exit, so the first attribute access raised `DetachedInstanceError`; `backup_signals(include_raw=True)` was separately a no-op. Both fixed.
- **Re-running the data migration duplicated demo signals.** They had no dedupe key and claimed `source="rss"`, making them indistinguishable from collected signals in source-mix statistics. Now opt-in (`--with-sample-signals`), marked with a `demo:` id prefix, and idempotent.

### Tests
- 57 new tests in `tests/test_paid_provider_gating.py`: the kill switch at construction (all three factories, `dry_run` exemption, unset/typo'd values failing closed, recognized off-values), the router and the factories provably reading one flag one way, the legacy path metered exactly once (`complete()` and `chat()`, dry-run and zero-token CLI responses skipped, the router path asserted *not* double-counted), the budget ceiling (refusal before the request rather than after, the numbers named in the message, `QuotaExhaustedError` subclassing, no retry on a spent budget), both fail-open paths (unreachable ledger, unreadable status), Gemini's overridden `complete()` metering the model that actually answered in its multi-level fallback chain, and source invariants (every paid factory calls the gate; paid providers are constructed nowhere outside the factories except the router, which guards itself; the three reported sites still route through factories). Pre-merge adversarial review (25 agents, 19 findings, 8 surviving refutation) added the last three groups and fixed what they exposed: **every behavioural test stubbed `_budget_controller`**, so the one seam where the guards meet the real `BudgetController` was never executed — the feature could have been inert end to end with all tests green; the Gemini test covered only the fallback branch and never asserted the budget gate; and `test_router_path_is_not_double_counted` never constructed a router and covered only OpenAI. There are now real-SQLite-ledger tests (a billed completion lands in `api_usage` with the right cost, a really-spent budget refuses, the lazy import seam resolves, the controller is built once per provider) and a real-`HybridLLMRouter` test parameterized over both paid providers. Mutation-verified twice: removing the gate and the metering fails 10 tests; reverting the CLI exemption and making the ledger inert fails 5.
- 15 new tests in `tests/test_deploy.py`, same run-the-real-script harness: deploy state (recorded only on success, docs-only syncs included; the crashed-deploy retry), the local-commit guard (block + `--force` override + the commit survives), failure backoff (skip inside the window, retry after it, journal growth on a second failure, immediate reset on a new commit, `--force` bypass), the staged web build (promoted on success, live `.next` untouched on failure), lock ownership (dead owner reclaimed immediately, live owner respected), a source invariant that the script body is wrapped in `main()`, and an ecosystem invariant pinning the poller's 3G memory headroom. All mutation-verified: 14 of the 15 fail against the pre-hardening script/config (the 15th, live-lock-respected, is an invariant that must hold on both).
- `tests/test_website_share_metadata.py` (17 tests): source-level pins for the share-metadata convention and the ecosystem-bar accessibility fixes, in the same spirit as test_deploy.py pinning "`git clean` appears nowhere in deploy.sh" — the website has no JS test runner, so the guards fail on the commit that reintroduces inline share metadata or drops the separator/new-tab hint, not on the next visual QA pass. The og:image pin was hardened during the pre-merge adversarial review: it now asserts the `images: [OG_IMAGE]` usage inside `detailMetadata()` — the bare URL-constant check stayed green under a mutation that removed the usage.
## [0.6.19] - 2026-08-06


## [0.6.17] - 2026-08-05

### Changed
- **Triage tuned for a lower open-issue steady state — the first live day proved the defaults too timid.** v0.6.16 shipped with `min_age_hours: 24`, which quarantined every idea for a full day: the 12:00 UTC backlog tick ran against a backlog whose newest-to-oldest ideas were all under 24h old and consumed **exactly zero** — the whole day's production sat untouchable until D+1. Tuning (config + code defaults + docs, all in sync): `per_run` 15 → **25** (capacity 150 touches/day ≥ 75 decisions/day vs ~40/day produced; a debate's ~20-idea burst drains within two cycles), `min_age_hours` 24 → **6** (trends refresh every 2h, so a 6h-old idea already faces a materially different context; ideas are now decided the same day), and the aging-sweep backstop `max_age_days` 30 → **14** (with decision-based closes as the normal path, the timer only catches orphan issues with no DB row behind them). Expected steady state: ~15–25 in-flight [Idea] issues on top of the 62-issue human-curated keep-set (12 `curated:keep`, 43 `source:trend`, 7 with human comments), so ~80–90 open total, down from the ~100–150 the v0.6.16 defaults implied. `max_strikes` stays 2 — gemma3:4b score noise is real and the 6–7 band deserves its second look.

### Fixed
- **Auto-deploy no longer stamps its own cron onto api/web.** PM2 injects a managed process's config keys (`cron_restart`, `autorestart`, …) into its environment as plain variables, and `pm2 restart --update-env` merges the caller's environment into the target app's stored definition — so every deploy run by the `moss-ao-deploy` poller (cron `4-59/5 * * * *`) stamped that cron onto `moss-ao-api`/`moss-ao-web`, force-restarting both every 5 minutes (2026-08-05: 59 restarts over ~5 h; re-registering cleanly did not stick because the next deploy re-applied it — PM2 never re-reads `ecosystem.config.js` on restart, upstream #3742/#4504). The mechanism was reproduced with a scratch PM2 app before fixing. `deploy.sh` now scrubs the known injected config-key variables (`cron_restart` and 8 siblings) at startup and restarts without `--update-env` (which was also leaking deploy-only env such as `GITHUB_TOKEN` into the apps); app env comes solely from `ecosystem.config.js` at registration time. Note `pm2 restart X --cron-restart 0` does **not** clear a stored cron in PM2 7.0.3 — delete + re-register is the only reliable cleanup; detection one-liner and full incident writeup in `docs/deployment.md`. `TestPm2EnvHygiene` (real deploy runs with all nine scrub-list keys injected; also pins that a deploy only ever uses `pm2 jlist`/plain `restart` — never `start`/`save`, and `--update-env` on *any* verb) and a source invariant fail against the pre-fix script; an ecosystem-registration invariant separately guards `ecosystem.config.js` itself (api/web: no `cron_restart`, `autorestart: true`) against a future config regression — it passes pre-fix, since the file was never wrong. The guards were hardened after an adversarial review demonstrated by mutation that the originals missed `--update-env` on non-restart verbs and detected only 2 of the 9 scrubbed keys.

- **Social share cards get their image — `/og-image.png` was a 404.** `layout.tsx` has declared `/og-image.png` (1200×630) as the OG/Twitter image ever since the share metadata was added, but the file never existed in `website/public/` — https://ao.moss.land/og-image.png returned 404, so every share card rendered imageless (0.6.15's `metadataBase` fix made the URL *resolve* correctly, to an asset that wasn't there; PR #2950 extends the same reference to every detail route). Added the asset: a 1200×630 terminal-window card on `#0d1117` — MOSS :: AO wordmark in the site's `#39ff14`/`#00ffff`, JetBrains Mono, "Agentic Orchestrator · Mossland" tagline, `signals → trends → debate → ideas → plans` status line — 57 KB. `scripts/generate_og_image.py` regenerates it byte-for-byte (Pillow; fetches the same JetBrains Mono the site uses via next/font), so future design edits don't start from a screenshot.

## [0.6.16] - 2026-08-05

### Added
- **Backlog triage — idea production finally has a matching consumer.** Debates produce ~40 ideas/day, but only auto-promoted ones (score ≥ 7 at debate time) ever left the backlog; the other ~85% sat in `scored` forever — nothing in the codebase read that status again — and their GitHub issues waited for the 30-day aging timer. Production had no consumer, so the open-issue count could only climb (the mechanism behind the 2,866-issue flood repeating in slow motion). New `scheduler/backlog_triage.py`, run from the backlog cycle (4h) right before the issue lifecycle:
  - Re-scores the **oldest** `scored`/`pending` ideas (quota `per_run`, default 15; ideas younger than `min_age_hours` are left alone) against **today's** trends, not the trends of the debate that produced them.
  - Re-score ≥ promote threshold → `promoted` + a **draft** plan for human approval via `POST /plans/{id}/approve` — never auto-approved, and no new [Plan] issue; the existing lifecycle closes the [Idea] issue as `completed`. Re-score < archive threshold → `archived` with the verdict recorded in `extra_metadata.triage`. Middle band → one strike; at `max_strikes` (default 2) the idea archives anyway ("re-evaluated N times, never promotable").
  - Every idea therefore reaches `promoted|archived` within at most `max_strikes` touches, bounding the open backlog at production_rate × days-to-decision (~100–150 open issues at current rates) instead of unbounded growth. Sizing rule documented in config: `per_run × 6 runs/day` must exceed daily idea production (15×6 = 90 touches/day ≥ 45 decisions/day vs ~40 produced).
  - Triage writes **only to the DB** (SQLite stays the source of truth); closing mirror issues is the issue lifecycle's job. The scorer's transport-error fallback (flat 5.0, empty reasoning) is detected and skipped without a strike — an Ollama outage must not archive ideas by attrition. To make that discrimination real, `IdeaScore` now carries the model's `reasoning` through (`_parse_score_response` used to discard it, which would have made the reasoning check vacuous and misclassified every genuine 5/5/5/5 verdict as an outage — caught in pre-merge adversarial review, pinned by a test against the real class, not the test double). Config: `backlog.triage` (enabled/per_run/min_age_hours/max_strikes). 12 new tests in `tests/test_backlog_triage.py`.
- **Issue lifecycle: archived reconciliation.** A DB-`archived` idea whose mirror issue is still open now closes as `not_planned` with the triage verdict in a comment ("Backlog triage re-scored this idea at 3.1/10 — archived (…)"). Human engagement overrides the bot exactly like the aging sweep: `curated:keep`/`source:trend` labels and any comment keep the issue open. This is also what makes triage crash-safe: decisions land in the DB even when GitHub is down, and the next backlog cycle reconciles the mirror. `_close_issue` now closes **before** commenting: comment-first had a poison window (comment lands, close fails on a 5xx/rate-limit — GitHub calls have no retry) where the bot's own verdict comment would read as human engagement and permanently block every future auto-close of that issue — caught in pre-merge adversarial review; the partial-failure path is now tested including recovery on the next cycle. 6 new tests. The 30-day aging sweep remains as the backstop for issues with no DB row (e.g. the pre-restore era); the normal path is now a decision with a stated reason, not a silence timer.

### Fixed
- **`backlog.max_open_ideas` was a delayed kill switch for the GitHub mirror.** The cap compared against `count_all()` — every idea ever created — but ideas are never deleted (the retention sweep prunes trends and debate sessions only), so at ~40 ideas/day the count would have crossed 800 within ~3 weeks of the 2026-08-05 DB restore and silently stopped all [Idea]/[Plan] issue creation, permanently. It now counts OPEN (scored/pending, i.e. awaiting a triage decision) ideas, matching its name and its documented intent; with triage draining the backlog it becomes the emergency valve it was meant to be.
- Docs-only deploys no longer take a pre-deploy DB snapshot. Nothing restarts on a docs sync and `reset --hard` cannot touch the untracked DB, so the snapshot protected nothing — while each one rotated the 7-slot backup window, meaning a burst of docs merges could churn days of restore points into minutes. Code deploys still snapshot first. Gate mutation-verified.
## [0.6.15] - 2026-08-05

### Fixed
- **Scaffold no longer pushes to origin/main from the production server.** `_git_commit_and_push` ran unconditionally after every generated project — `git add` + `commit` + `git push origin main` on whatever checkout the scheduler runs in. It has only been failing (with warning spam) since /projects/ became gitignored; before that this path is exactly where the server's local "feat: generate production-quality code…" commits on main came from. config.yaml has carried `git.auto_push: false` all along — nothing read it. The scaffold now honors it (default false, fail-closed when config is unreadable, explicit constructor argument wins), and the gate placement itself is pinned by a test.
- **Idea scoring joins structured outputs.** The score parser had the same fenced-JSON fragility as trends, with a worse blast radius: its except-path *invents* a neutral 5.0 score, so a parse failure silently files every idea in the backlog band regardless of quality. The route now attaches `SCORE_RESPONSE_SCHEMA` (grammar-enforced; all four dimensions required) and a 1,024-token output budget; the neutral fallback remains as a transport-error path only.
- **Social-share previews pointed at localhost.** `metadataBase` was never set, so Next.js resolved the relative `og-image.png` against `http://localhost:3000` in production builds — every OG/Twitter card for ao.moss.land carried a localhost image URL (visible in the served HTML). Set to `https://ao.moss.land`.
- Documentation told two lies about the embedding model, now corrected in CLAUDE.md and code comments: no code path calls an embedding API (signal "semantic dedup" is title-token Jaccard, `signals/aggregator.py::_is_semantic_duplicate`), and the production Ollama host does not have `qwen3-embedding:0.6b` pulled. The hierarchy entry stays as an explicitly-labeled reserved slot.

### Added
- **GitHub issue lifecycle — the tracker now circulates instead of only accumulating.** The orchestrator created an issue per idea and per promoted plan but nothing ever closed one: 0.07% closure rate, 2,866 open issues by 2026-06, two manual mass-cleanups since. `GitHubClient` always had `update_issue`/`add_comment`; no scheduled task called them. New `scheduler/issue_lifecycle.py`, run from the backlog cycle (4h), adds the missing half:
  - **Pipeline-linked closes** (`state_reason=completed`): when an idea is promoted and its plan is created, the `[Idea]` issue gets a comment linking the `[Plan]` issue, labels move to `status:planned`+`processed:to-plan`, and it closes — inline at promotion time, with a reconciliation sweep retrying anything GitHub dropped. When a project is generated from a plan (auto ≥ 8.0 or via `POST /plans/{id}/approve`), the `[Plan]` issue closes naming the project. Reconciliation reads DB truth (`ideas.github_issue_id`/`plans.github_issue_id`), so manual API-path promotions are covered too.
  - **Aging sweep** (`state_reason=not_planned`): bot-generated issues older than `backlog.issue_lifecycle.max_age_days` (default 30) with zero comments close automatically. The orchestrator never comments on open issues, so one comment means human interest and exempts the issue; `curated:keep` (new label, added to `Labels`/`ensure_labels_exist`) and `source:trend` are never aged out — the 2026-06 curated keep-set stays pinned.
  - **Archived ideas (score < 4.0) no longer get an issue at all** — dead-on-arrival issues were pure tracker noise; the DB row is the record.
  - Guardrails: closes capped per run (`max_closes_per_run`, default 50), the sweep uses the **list API** because this repo's search index silently omits issues (#36/#43/#60/#668 historically), every close is best-effort (a GitHub failure logs and moves on, never breaking the backlog cycle), and everything is visibility-only — DB rows untouched, closed issues reopenable. Disable via `backlog.issue_lifecycle.enabled: false`. 20 new tests in `tests/test_issue_lifecycle.py` cover the age-out decision matrix, both reconciliation directions against a real in-memory DB, budget enforcement, error counting, PR filtering in `list_issues`, and `state_reason` plumbing.
- **Structured outputs for trend analysis.** Ollama has enforced JSON schemas at the decoding level since v0.5.0 (Dec 2024) — the `format` field constrains sampling so invalid tokens *cannot be emitted* — and the production server (0.32.5) has had the capability all along; the code simply never used it. The provider now accepts `format_schema`, the router plumbs `response_schema` through every Ollama call site (including both fallback paths, where a dropped schema would fail silently), and the trend-analysis call attaches `TrendAnalyzer.TRENDS_RESPONSE_SCHEMA`. E2E on the production box: the first response token is `{`, smart quotes now appear only *inside* string values where they are legal, strict `json.loads` passes with no lenient repair, and content quality holds (700-950-char summaries at the same temperature). The lenient parser stays as defense in depth — schema-valid is not semantically-valid, and a `max_tokens` cut can still truncate the document. A schema-vs-parser consistency test guards that every field the parser reads exists in the schema, so the grammar can never forbid a field the pipeline stores. 7 new tests; the three-hop plumbing (provider payload, router forward, analyzer attach) is mutation-verified hop by hop.

### Fixed
- **Debate idea titles could again be raw JSON fragments** (`[Idea] "Decentralized Oracle Integration (Chainlink)",` — issues #2903/#2906/#2910/#2912 from the 2026-08-05 cycle). When the idea JSON fails to parse (typically a truncated generation), the text fallback scans raw lines for a title. The #2870 noise filter rejected `"key": value` property lines but not **bare string values** — array elements such as tech-stack or roadmap entries — so the first sufficiently long element became the issue title, quotes and trailing comma included. `_is_json_noise_line` now also rejects any line that begins with a straight double quote (curly-quoted “real” titles are unaffected — LLMs use those decoratively, never as JSON delimiters), and the chosen fallback title is defensively stripped of wrapping quotes and trailing commas. 12 new tests in `tests/test_title_extraction.py` pin the exact production shapes, including a truncated-JSON body whose only long lines are array elements.
- **Prompt-echo duplicates.** The divergence prompt's "Good examples" line embedded two complete, Mossland-plausible titles — and gemma3:4b copies them: "GPT-5 Based DeFi Position Auto-Rebalancing Agent Development" was recreated 129× historically and again on 2026-08-05 (#2894/#2895) the first cycle after the DB (and with it the dedup fingerprint history) was rebuilt empty; "Real-time Metaverse Asset Value Tracker" reappeared as #2902. The prompt now teaches the title *pattern* ([specific tech/protocol] + [what it does] + [for whom]) instead of giving copyable titles, and explicitly forbids reusing any title seen in the discussion, background, or instructions.
- **Trend analysis produced 0 trends — every cycle, silently.** Two stacked defects, both confirmed against the live server on 2026-08-05. First: no Ollama request ever sent `num_ctx`, so the shared server loaded gemma3:4b at its own 4096 default; the trends prompt alone is ~3,300 tokens, and generation stopped at exactly `prompt_eval + eval == 4096` with `done_reason="length"` — which the provider then discarded, so nothing was ever logged. Second: the JSON extractor demanded a *closed* ` ```json ` fence (truncation eats the closing fence) and `json.loads` has no tolerance for gemma3's habit of using curly “smart quotes” as string delimiters — observed even in complete, non-truncated responses. Either defect alone discarded the whole response; the numbered-list text fallback then matched nothing, yielding `Saved 0 trends`.
- Fixes, each mutation-verified: every generate/chat/stream call now sends `num_ctx` (default 16384, configurable via `throttling.ollama.num_ctx`); the trend call sets an explicit `max_tokens=4096` output budget; `OllamaResponse` now carries `done_reason` and a `truncated` property, and a truncated generation logs a WARNING with token counts instead of passing silently; parsing is layered — strict fence → balanced-brace slice (string-aware) → lenient re-parse with smart-quote normalization and trailing-comma stripping (repairs run only after strict parsing fails, so well-formed content is never altered) → object-by-object salvage of the `"trends"` array, which recovers the complete leading objects from a truncated tail. An "after-```json-to-end" layer was tried and removed: salvage provably covers it.
- End-to-end verified on the production box before merge: the same live prompt that previously died at 4096 (`eval=798`, reason=`length`, 0 trends) now completes naturally (`eval=1397`, reason=`stop`) and parses into scored trends.
- `tests/test_trend_json_parsing.py` (24 tests) pins both halves: payload options (`num_ctx` always present, configurable; `max_tokens` → `num_predict`), truncation detection and its warning, and a parser gauntlet including the exact production failure shape (prose preamble + fence + smart quotes + truncation). Six mutations — dropping `num_ctx`, dropping `done_reason`, disabling quote normalization, disabling salvage, silencing the warning, removing the analyzer's `max_tokens` — each fail their corresponding tests.
- `scripts/deploy.sh` now picks its dependency installer from what the checkout actually is: `uv sync` when `uv.lock` is present or `.venv/pyvenv.cfg` records a uv-built environment, `pip install -e .` otherwise. Found by inspecting the production box rather than by testing: its `.venv` is uv-managed and contains no `pip` at all, so the original `pip install -e .` would have failed on the one machine this script exists for — and only on commits that touch `pyproject.toml`, which is exactly when a rollback is least welcome. The lockfile is untracked there, so the choice is a property of the machine and not of the commit. Both branches and the uv-sync failure path are covered, and the detection was mutation-verified in both directions (forcing uv on, forcing it off).

### Added
- **Pull-based auto-deploy** (`scripts/deploy.sh` + the opt-in `moss-ao-deploy` PM2 job): the production server now follows `main` on its own, every 5 minutes, instead of a human running `git pull` + `npm run build` + `pm2 restart` by hand. Push-from-CI was not an option and the reason is worth recording: the app server has no public inbound route (it is reachable only inside the Tailscale tailnet, with the public `ao.moss.land` Nginx proxying in from a separate Lightsail box), this repository is public — where a self-hosted runner would let a fork PR execute code on an internal machine — and the account operating it holds `MAINTAIN`, not admin, so registering runners or Actions secrets returns 403. Pulling needs none of that: a public repo fetches anonymously, so the server opens no port, holds no deploy key, and requires no GitHub-side configuration at all. Tailscale stays what it already was — the human admin path — and is not part of the deploy path.
- The deployer only does the work the diff calls for: `pip install -e .` when `pyproject.toml` moved, `npm ci` when the lockfile moved, `npm run build` for any `website/` change (`NEXT_PUBLIC_*` is baked in at build time, so restarting alone would keep serving the old bundle), and a restart of `moss-ao-api` / `moss-ao-web` only. The scheduler jobs are deliberately *not* restarted: signals/trends/debate/backlog/health each spawn a fresh `.venv/bin/python` on every cron tick, so they pick up new code by themselves, and restarting them would only kill work in flight. A docs-only commit therefore restarts nothing.
- Guards, each of which exists because the unguarded version has a specific failure: deploy only commits GitHub Actions reports green (pending defers to the next tick; an unreachable API also defers rather than deploying blind); abort when tracked files were hand-edited on the server, which `git reset --hard` would otherwise discard silently; defer back-end deploys while a debate is running (~30 min) since reinstalling packages under a live import can break it, while front-end-only changes proceed; a stale-tolerant lock so overlapping ticks cannot interleave; a forced DB snapshot before every deploy; and automatic rollback — *including a rebuild*, so the restored commit is served consistently — when the build or the post-deploy health check fails.
- `docs/deployment.md`: install, configuration (`MOSS_AO_AUTO_DEPLOY`, `DEPLOY_*`), day-to-day operation, manual rollback, troubleshooting, and what it would take to move to instant GitHub Actions + Tailscale deploys (tailnet admin for `tag:ci` and an OAuth client, repo admin for secrets) — with the note that even then the workflow should call this same script, so guards and rollback do not fork into two implementations.

### Changed
- `ecosystem.config.js`: removed the `pm2 deploy` block. It had never been runnable — it named a host that does not exist (`server1.moss.land`), the wrong repository (`mossland/` rather than `MosslandOpenDevs/`) and a `requirements.txt` this project does not have — and it could not work in principle, since nothing outside the tailnet can SSH into the app server. Leaving it in place implied a deployment path that did not exist.

### Tests
- Added `tests/test_deploy.py` (29 tests). The deploy script is what stands between `git push` and production, so it is tested by running it: each test builds a throwaway origin/checkout pair and puts stub `pm2`, `npm` and `curl` executables first on `PATH`, so the real script takes its real code paths against fake infrastructure. Covered: the no-op fast path (it runs every 5 minutes — it must stay silent and free), per-path build/restart selection, every guard above, rollback after a failed health check and after a failed build, and the `CRITICAL` case where the rollback itself does not come back healthy.
- The load-bearing test is that untracked server state survives a deploy: `data/orchestrator.db`, `data/backup/`, `.env` and `website/.env.local` all live untracked on the server, and the 2026-07 outage was that DB going missing. `git reset --hard` leaves them alone and `git clean` destroys them, so the invariant is pinned twice — behaviourally (the files are still there afterwards) and statically (`git clean` appears nowhere in the script's code).
- All six ways this can regress were mutation-verified against a copy of the script — adding `git clean`, dropping the dirty-tree guard, dropping the rollback, ignoring a red CI verdict, dropping the busy-scheduler guard, and losing the no-op fast path — and in each case the corresponding test was confirmed to fail.
- Added `tests/test_version_resolution.py` (10 tests) covering the version-resolution *logic* in `__init__.py`, which 0.6.12's `TestVersionReporting` could not distinguish — those tests assert the surfaces (`/health`, `/`, `/openapi.json`) agree with `__version__`, but every one of them still passes if the resolver is changed to consult installed metadata **before** the source tree. That was verified by mutation, and it matters because metadata-first silently reintroduces the drift 0.6.12 fixed: `importlib.metadata` returns the snapshot taken at `pip install` time, so an editable install whose checkout has since been bumped keeps reporting the old version — and `git pull` + `pm2 restart` with no reinstall is the documented deploy flow. Now covered: source-tree-beats-metadata precedence, the metadata fallback for wheel installs, the `0.0.0+unknown` sentinel *and* its warning log, the `[project].name` guard that stops a foreign `pyproject.toml` from being adopted when the package sits in site-packages, and graceful degradation on a malformed / version-less / missing `pyproject.toml` (resolution must degrade, never raise on import). A positive control asserts a synthetic tree with a matching name *is* adopted, so the negative cases cannot pass for the wrong reason.
- Extended the no-hardcoded-literal guard to `__init__.py` as well as `api/main.py`, so re-hardcoding is caught at the commit that introduces it rather than at the next version bump.
- All 10 tests were mutation-verified: each of the 9 ways this logic can regress — including re-hardcoding `__version__` itself, the obvious way to undo the fix — was applied to a copy of the source, and the corresponding test was confirmed to fail.
- The suite is install-shape agnostic, verified against all three: a bare `PYTHONPATH=./src` run, CI's `pip install -e ".[dev]"`, and a non-editable `pip install .`. Under the last one the imported package is the site-packages copy, not the checkout, so `parents[2]` is the venv directory and declining the source tree is *correct*; the one assertion that only makes sense against this checkout skips there with that reason rather than reporting a phantom drift bug.

## [0.6.14] - 2026-08-04

### Documentation
- **README restructured — 375 lines to 266, 38 headings to 16.** The v0.6.13 accuracy pass fixed the facts but kept the shape it found, and adding the six previously-undocumented adapters in the existing one-h3-per-adapter style left `## Signal Sources` as eleven consecutive two-bullet subsections. The file had one heading every 9.9 lines. Nothing verified was removed; the same facts are now carried by two tables.
  - `## Signal Sources`: eleven h3 stubs become one table with a new **Auth** column, so the credential each adapter needs (`TWITTER_BEARER_TOKEN`, `DISCORD_BOT_TOKEN`, `NEYNAR_API_KEY`, or none) is visible at a glance instead of buried in prose. All tracked-entity counts kept.
  - `## Multi-Stage Debate System`: four h3 subsections become one table, and it now states **pool size vs agents per round** in adjacent columns (16/8/10 pools, 8/4/3 per round from `debate.normal.*_agents_per_round`) rather than leaving a reader to reconcile two numbers from different sections.
  - `## Dashboard`, `### PM2 Commands` and `## Development` lose their h3 children, which were mostly one-command fences.
- **The README named twelve agent personas that do not exist.** `Innovator`, `Skeptic`, `Pragmatist`, `Synthesizer`, `Evaluator`, `Prioritizer`, `Risk Assessor` and `Resource Planner` return zero matches in `personas/catalog.py`; the real roster is Frontend/Backend/Blockchain engineers, VCs and accelerator mentors, CPO/Leads/QA/DevRel. The v0.6.13 pass corrected the phase *counts* and never checked the *names*. Both the debate table and the architecture diagram now list the real role families.
- **The architecture diagram was stale and structurally broken.** It drew 5 adapters while the text said 11, and 20 of its 35 English lines (22 of 35 in Korean) were the wrong display width, so the box borders did not line up. Redrawn at exactly 75 display columns on all 27 lines in **both** files, verified programmatically with East-Asian width accounted for, and now naming all 11 adapters.
- Deduplicated the adapter list, which had appeared in four places (Key Features bullet, architecture diagram, Signal Sources, Project Structure tree). The Key Features bullet now links to `#signal-sources` instead of re-listing eleven proper nouns; the Project Structure tree collapses the eleven adapter files to one annotated line.
- Trimmed the `## Related Mossland Projects` bullets, which carried the file's longest line by a wide margin (372 chars against a 257-char runner-up). The `` (`alpha.moss.land`) `` / `` (`signalmap.moss.land`) `` parentheticals restated the href verbatim and appeared nowhere else in either README, and the alpha-mcp reference moves to its own sub-bullet. All four links preserved.
- EN/KO line parity holds: both files are 267 lines with identical heading line numbers.

## [0.6.13] - 2026-08-04

### Fixed
- **Issue bodies no longer break mid-JSON.** `_auto_score_and_save_ideas` built the GitHub issue body from `idea_content[:500]`. Debate output is a fenced ```` ```json ```` object, so that slice cut the block open and every following section — Auto-Score Results, Decision, Context — rendered inside the unclosed code span. **12 still-open issues** are in that state, 7 of them `curated:keep` (#529, #570, #583, #668, #698, #730, #731, #750, #762, #1011, #1252, #2437), verified by scanning every open issue for an odd fence count. The DB `summary`/`summary_ko` columns were truncated the same way; `description` was always intact, so nothing was lost. `_format_idea_summary()` now parses the JSON and lays it out as markdown, falling back to `_truncate_markdown()`, which cuts on a paragraph/line/sentence boundary and closes any fence it would otherwise leave open. Both paths honour the length bound. Existing issue bodies are untouched; backfilling them needs the production DB.
- **Markdown no longer leaks into issue titles.** Titles were cleaned with `title.replace("#", "")`, which left emphasis markers intact — GitHub renders no markdown in titles, so 27 open issues read `[IDEA] **Foo**` with literal asterisks. `_clean_issue_title()` now strips `*`, `` ` `` and `_` and collapses the whitespace left behind, at all four issue-title construction sites. (The 27 existing titles were corrected directly on the tracker.)
- **`status == "archived"` created an off-taxonomy label.** The branch appended the raw string `"archived"` while its two sibling branches used `Labels` constants, so a resumed pipeline would create a stray `archived` label outside the registry. Added `Labels.STATUS_ARCHIVED = "status:archived"` — documented since the beginning, never actually defined — to `ALL_LABELS` and used it.
- **`website/src/lib/version.ts` was still on 0.6.10**, three releases behind, despite its own comment instructing that it be kept in sync. 0.6.11 and 0.6.12 both bumped `pyproject.toml` without it.
- **Restored EN/KO README line parity**, which 0.6.11 broke by one line: an explanatory paragraph landed as 4 lines in English and 3 in Korean. The Korean paragraph is rewrapped to 4 lines with identical content; both files are 375 lines with identical heading positions again.

### Documentation
- **`docs/labels.md` rewritten against the real registry.** It documented three labels that exist nowhere in the code (`status:promoted`, `status:archived`, `source:debate`) and omitted four that are in active use (`processed:to-plan`, `curated:keep`, `rejected`, `reject:plan`). Its "Setting Up Labels" block created the three phantom labels and missed most real ones; it now points at `ao backlog setup`, which is generated from `Labels.ALL_LABELS`.
  - `promote:to-plan` was filed under "Future / Not yet implemented". Its consumer (`find_ideas_to_promote` -> `BacklogOrchestrator.run_cycle`) is fully implemented and last ran on 2026-01-04; what is missing is a scheduler entry, since `run_cycle` is reachable only from `ao backlog run` / `ao backlog process` and no PM2 job calls it. (`moss-ao-backlog` is a different task.)
  - Documented the **two conflicting meanings** of `promote:to-plan`: the docs and issue template call it a human approval gate, while `scheduler/tasks.py` applies it automatically at score >= 7.0. Scheduling the consumer before resolving that would generate every plan twice and remove the human gate. Recorded as a decision for a maintainer, deliberately not resolved here.
  - Recorded why the six `promote:to-plan` issues carry no `status:` label — `find_ideas_to_promote()` queries `[type:idea, promote:to-plan]`, so adding `status:backlog` would double-count them across two queues meant to be exclusive. They are correct as they are.

### Housekeeping (GitHub tracker, no code change)
- Deleted the 9 unused GitHub default labels (`bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`) — all verified at 0 usage across 2,868 issues and every PR. The label set is now exactly the 11 the taxonomy defines.
- Closed #65 and #66 as duplicates: both are backfill artifacts labelled `type:idea` whose bodies are the planning documents for #12 and #10, with titles duplicating ideas #11 and #7. Originals and plans all remain open.
- Collapsed three promotional comments as spam (#583, #1252, #2437). Minimising retains the comment, so the "has a non-bot comment" protection on the 2026-06 keep-set is unaffected — re-verified afterwards.

## [0.6.12] - 2026-08-04

### Fixed
- **Two API routes were permanently unreachable due to registration order.** Starlette/FastAPI matches routes in the order they are registered, so a literal path declared *after* a same-prefix parameterized route can never be reached:
  - `GET /signals/timeline` was registered after `GET /signals/{signal_id}`, so every request bound `signal_id="timeline"` and returned `404 Signal not found`. The System page's signal timeline widget (`website/src/app/system/page.tsx` → `components/visualization/SignalTimeline.tsx`, via `getSignalTimeline()`) had therefore never rendered data.
  - `GET /plans/pending-approval` was registered after `GET /plans/{plan_id}`, breaking the manual plan-approval workflow documented in CLAUDE.md — it returned `404 Plan not found: pending-approval`.

  Both literal routes now precede their parameterized siblings. The handlers themselves are unchanged, and the frontend `SignalTimelineResponse` type already matched the payload the timeline handler emits.
- **`/adapters` omitted `CoingeckoAdapter`**, listing 10 of the 11 adapters that `signals/aggregator.py` actually registers. The adapter is now enumerated, and its `TRACKED_COINS` attribute feeds the shared `sources`/`source_count` contract that the other adapters use.
- **API version strings had drifted three ways**: `FastAPI(version=...)` and `/health` reported `0.5.0`, `/` reported `0.6.0`, and `__init__.py` (which backs `cli --version`) reported `0.3.0` — while `pyproject.toml` declared `0.6.10`. `__version__` now resolves from **the source tree's `pyproject.toml` first**, falling back to installed distribution metadata and then to a logged-warning `0.0.0+unknown`; all three API call sites read from it.
  - Reading installed metadata alone would not have been enough. `importlib.metadata` returns a snapshot taken at `pip install` time, so it goes stale on the very commit that bumps the version. More importantly, every PM2 app in `ecosystem.config.js` launches `.venv/bin/python` with `PYTHONPATH: './src'` — the code being served is the **working tree**, not an installed copy — so a venv without dist-info would have silently published `0.0.0+unknown` on `/health`, `/` and `/openapi.json`. Reading the checkout first keeps the documented deploy flow (`git pull` + `pm2 restart`, CLAUDE.md) accurate with no reinstall step.

### Tests
- Added `tests/test_api.py::TestLiteralRouteOrdering` — asserts `/signals/timeline` and `/plans/pending-approval` return their intended payload *shape and counts* (not the single-resource handler's), that the parameterized siblings still route and still 404 on unknown ids, and a table-wide `test_no_literal_route_is_shadowed` guard that walks every registered route and fails if any literal path is shadowed by an earlier parameterized one — blocking this whole bug class from recurring. The guard compares **HTTP methods as well as paths**: Starlette keeps scanning past a path match whose method does not match, so routes sharing no verb cannot shadow each other and must not be flagged.
- Added `TestVersionReporting` (`/health`, `/`, `/openapi.json` and the package version all agree with `pyproject.toml`) and `TestAdaptersEndpoint` (the `/adapters` listing must equal the aggregator's registered set). `/adapters` calls `health_check()` on all 11 adapters and many of those issue real outbound HTTP, so both tests stub `health_check` to keep the suite hermetic.

## [0.6.11] - 2026-08-04

### Changed
- **One canonical RSS feed list.** Signal collection and trend analysis were reading two different, silently diverging lists: `config.yaml` `trends.feeds` (16 feeds) fed only the trend path (`trends/feeds.py`), while signal collection used 32 feeds hardcoded in `adapters/rss.py` `DEFAULT_FEEDS`, because `signals/aggregator.py` constructs `RSSAdapter()` with no `feeds=` argument. The merged union (35 entries) now lives in a new **top-level `feeds:` section of `config.yaml`**, which both consumers read. Feeds can be added, fixed, or disabled without a code change or redeploy.
  - `RSSAdapter.DEFAULT_FEEDS` is replaced by `RSSAdapter.load_configured_feeds()` plus a 5-feed `FALLBACK_FEEDS` used only when no config can be read (logged as a warning). The legacy `trends.feeds` location is still read as a fallback, with a deprecation warning, so a deployment carrying a locally modified `config.yaml` keeps working.
  - Feed entries accept `enabled: false`, honoured by both consumers at load time so disabled feeds never reach the fetch loop.
  - Merging added 2 live sources that existed only in `config.yaml` (arXiv AI, The Hacker News) and de-duplicated 8 hosts the two lists carried under different URLs — including Hacker News, which both lists had via different hosts (`hnrss.org` mirror vs the official `news.ycombinator.com`; the official one was kept). Where the two disagreed on scope, the topic-specific feed was kept (e.g. TechCrunch AI over TechCrunch all).
- **4 dead feeds disabled rather than deleted**, with the observed failure recorded inline: Chainlink (200 but redirects to an HTML page), Polygon (404), Paradigm (525), a16z Crypto (404). All four were in the hardcoded list and had been fetched — and failing — on every 30-minute signal run. No publisher-provided replacement feed exists; verified 2026-08-04.

### Fixed
- **A malformed `feeds:` section degrades instead of taking down signal collection.** Because `RSSAdapter` is constructed inside `SignalAggregator._default_adapters()`, an `AttributeError` from the feed loader propagated out of `SignalAggregator()` itself — so a `feeds:` written as a flat list or a scalar (a plausible hand-edit of the very file operators are now told to edit) would have stopped **all 11 adapters** from collecting, not just RSS, on every 30-minute cycle. Both consumers now reject a non-mapping `feeds:` with a warning and fall back, matching the loader's documented contract, which already degraded gracefully for an unreadable or syntactically broken config.
- **`custom_feeds` no longer mutates a shared list.** `RSSAdapter.__init__` assigned `self.feeds = feeds or self.DEFAULT_FEEDS` and then appended `custom_feeds` to it, mutating the class-level default (or the caller's list) for the lifetime of the process. The feed list is now copied before appending.

### Documentation
- **CLAUDE.md accuracy pass**, matching the README pass in #1935:
  - Its project-structure tree placed the signal adapters at `signals/adapters/`; the real location is `src/agentic_orchestrator/adapters/`. The tree now shows the actual layout, including the previously undocumented `trends/` package.
  - `rss.py` was described as "RSS 피드 (28개 소스)" — a number that matched neither list.
  - **Persona pool size vs agents-per-round is now stated explicitly** in both CLAUDE.md and the READMEs. `personas/catalog.py` defines pools of 16/8/10 (34 total) while `config.yaml` `debate.normal` runs 8/4/3 per round, `multi_stage.py` `_select_agents_for_round()` drawing a diversity-balanced subset each round. Both numbers are correct; documenting only one made the two documents look contradictory.
- New `## RSS 피드 소스` section in CLAUDE.md documenting the canonical `feeds:` contract, the per-feed keys, and why the split existed.

## [0.6.10] - 2026-07-02

### Fixed
- **`/status` no longer hard-500s when the database is broken** (2026-07 incident: every DB-backed endpoint on ao.moss.land returned 500 while `/health` stayed 200 — the production SQLite file had been lost/emptied, and `system_status()` ran its stat queries *before* any health check, so the prepared `degraded` branch was unreachable). The stat queries now double as the health probe: on failure the endpoint returns 200 with `status="degraded"`, `components.database.status="unhealthy"`, and zeroed stats, preserving the `{ stats: { agents_active, ideas_generated, debates_today } }` contract the moss.land governance widget consumes (MosslandOpenDevs/pixel-agent-lab#1, cause 2).

### Added
- **Startup schema self-heal** (`db/connection.py` `ensure_schema()`): the API (via a FastAPI lifespan hook) and every scheduler CLI command except `backup-db` now run the idempotent `create_tables()` (`CREATE TABLE IF NOT EXISTS`) before serving/working, with a short retry so simultaneously booting PM2 processes cannot fail each other on the boot-time CREATE race. A missing or emptied SQLite file degrades to an empty-but-working database that the signal/debate pipeline repopulates on its own, instead of "no such table" 500s on every DB-backed endpoint until an operator intervenes. `backup-db` is deliberately excluded — a backup command must never mutate the database it snapshots.
- **Rolling local DB backups** (`db/backup.py`): the 5-minute health task now snapshots `data/orchestrator.db` into `data/backup/` (gitignored) at a ~24h cadence, keeping the newest 7. Hardened against every reviewed failure mode:
  - Snapshots use the sqlite3 online-backup API copied **incrementally** (`pages`/`sleep`) so concurrent writers are not starved during a large copy (the production DB does not run WAL), with a 30s busy timeout.
  - Each snapshot is written to a `.tmp` name and **renamed into place only after `PRAGMA quick_check` passes** — an unclean death mid-copy or a corrupt source can never leave a garbage file that gates the interval or occupies a retention slot, and a failed attempt is retried on the next 5-minute tick instead of silently skipping a day.
  - **Regression-aware pruning**: if the history tables (ideas/plans/debate_sessions — the ones the pipeline cannot regenerate) shrank below 50% of the newest existing snapshot, the new snapshot is still written but pruning is suspended with a loud error. Without this, a wiped database auto-refilled by the 30-minute signals task would look "meaningful" again and daily rotation would destroy the last pre-incident backups within `keep` days.
  - Backups are skipped when the database is missing, empty, dataless, or fails the integrity check. Manual trigger: `python -m agentic_orchestrator.scheduler backup-db`.

### Tests
- Added `tests/test_db_resilience.py` (30 tests): /status degradation + widget contract, lifespan self-heal (including a broken-DB startup), snapshot/skip/prune/interval behavior, first-ever-backup paths, partial-copy cleanup + retry-next-tick, integrity-failure discard, regression-aware pruning, `ensure_schema` retry semantics, and scheduler-CLI dispatch guarantees (schema-heal ordering, `backup-db` read-only exclusion, non-zero exit).

### Operator notes
- **Restoring after DB loss**: stop the writers (`pm2 stop moss-ao-signals moss-ao-trends moss-ao-debate moss-ao-backlog`), copy the newest `data/backup/orchestrator-*.db` over `data/orchestrator.db`, then restart. Until a backup exists there is nothing to restore — the pipeline will repopulate an empty database over time.
- Never clean the deploy directory with `git clean -fdx` without excluding the data directory (`git clean -fdx -e data -e .env`); the production database has never been tracked in git.

---

## [0.6.9] - 2026-06-27

### Added
- **Code-generation verification gate** (`project/verifier.py`, `project/repair.py`): generated source is now verified and auto-repaired before it is written to disk and committed. The scaffold runs a per-file pipeline — deterministic repair → verify → (optional) one LLM repair retry that feeds the diagnostics back to the model — across Solidity, Python, and TypeScript/JavaScript.
  - **`CodeVerifier`**: Python via the built-in `compile()` (always available); Solidity via conservative static checks (missing `pragma`, invalid `.length()` calls, truncation detected by brace/paren imbalance) plus optional `solc` for import-free contracts; TS/JS via optional `esbuild` syntax checks. A missing toolchain degrades to a `SKIPPED` result, never a false failure. String/comment contents are never misread thanks to a small Solidity tokenizer.
  - **`CodeRepairer`**: deterministic fixes for the bug classes seen in generator output — adds missing SPDX/`pragma`, rewrites invalid `.length()` to the `.length` property, replaces the removed `now` global with `block.timestamp`, normalizes OpenZeppelin v5 idioms to the pinned v4 (`utils/` → `security/` imports, drops the v5 `Ownable(...)` base call), and injects `@openzeppelin/contracts` into `contracts/package.json` when any contract imports it. Fixes run only outside string literals and comments.
- **`ready_with_warnings` project status**: projects whose code could not be fully repaired are marked `ready_with_warnings` (instead of silently `ready`) and never block delivery. The per-file verification summary is persisted to `Project.extra_metadata["verification"]`, a one-line summary to `generation_log` and `.moss-project.json`, and surfaced in the Projects UI (badge color + a "Code Verification" panel in the project detail modal).

### Fixed
- **LLM-path contracts were missing the Hardhat toolchain**: `generate_smart_contracts_full()` emitted `.sol` files (plus a deploy script and tests that assume Hardhat) but no `contracts/package.json` or `hardhat.config.ts`, so `hardhat compile` could never resolve imports. Both are now emitted, with `@openzeppelin/contracts` pinned.
- **Hardhat templates** (`project/templates.py`, fallback contract in `project/generator.py`): the contracts `package.json` template now declares `@openzeppelin/contracts@^4.9.6`, and the fallback `Main` contract uses the OZ v4 no-arg `Ownable` constructor (it previously mixed v4 import paths with a v5 `Ownable(msg.sender)` call and could not compile against a single OZ version).

### Tests
- Added `tests/test_project_verifier.py`, `tests/test_project_repair.py`, and `tests/test_project_verification_gate.py` (34 new tests) covering the verifier, deterministic repairer, dependency injection, and the scaffold gate's deterministic and LLM-retry paths.

---

## [0.6.8] - 2026-04-30

### Security
- **Removed residual hardcoded Tailscale IP from source files**: `e0a4f4e` had stripped the internal Ollama IP from `ecosystem.config.js`, but the same address remained in `OllamaConfig.base_url`, the `os.getenv("OLLAMA_HOST", ...)` fallback, and a comment in `ollama.py`, plus a comment in `hierarchy.py`. All four references replaced with `localhost`/generic wording so the public repo no longer leaks internal network topology. (commit `8e2c9c2`)

### Fixed
- **Scheduler honors `OLLAMA_HOST` again**: After the security cleanup in `e0a4f4e`, PM2-spawned debate / trends / backlog workers were silently falling back to `http://localhost:11434` and returning HTTP 404 on every model call (the planning phase produced 17-character empty plans as a result). `ecosystem.config.js` now ships an inline `.env` parser that runs before the `env:` blocks are evaluated, so `OLLAMA_HOST` from `.env` is picked up without requiring the operator to export it in the shell first. No new dependency added (intentionally avoided `dotenv` package). (commit `48cf50f`)

### Added
- **`qwen2.5:14b` as the new top-tier local planner**: pulled on the remote Ollama server and registered in `LLMHierarchy.LOCAL_MODELS` with `tier=FREE`. `TASK_MODEL_MAP` now prefers it for `final_plan`, `quality_check`, `technical_review`, `moderation`, and `final_decision`, with `qwen3.5:9b` as the automatic fallback. Older models stay in place for divergence/translation/classification where extra parameters do not help. (commit `a8b3aea`)

### Operator notes
- Set `OLLAMA_HOST=http://<your-ollama-host>:11434` in `.env` (gitignored). Without it, all Ollama-backed work will hit `localhost`.
- `qwen2.5:14b` (~9 GB) must be present on the remote Ollama server. Pull via `curl -X POST $OLLAMA_HOST/api/pull -d '{"name":"qwen2.5:14b"}'`.

---

## [0.6.7] - 2026-04-13

### Security
- **API authentication on mutating endpoints**: `POST /plans/{id}/approve` and `POST /plans/{id}/generate-project` now require an `X-API-Key` header matching the `MOSS_API_KEY` env var. When the key is unset the endpoints fail closed with HTTP 503 (operator must opt in).
- **CORS hardening**: Replaced `allow_origins=["*"] + allow_credentials=True` with a whitelist read from `MOSS_CORS_ORIGINS` (default: `https://ao.moss.land,http://localhost:3000,http://127.0.0.1:3000`). Methods and headers reduced to the set actually used.
- **Server-side proxy for the Generate Project button**: Added `/proxy/plans/[id]/generate-project` and `/proxy/plans/[id]/approve` Next.js route handlers under `website/src/app/proxy/...`. The browser calls the proxy, which injects the API key server-side. The key never reaches the browser.
- **Path traversal & symlink hardening in project generator** (`project/templates.py`, `project/scaffold.py`): LLM-supplied file paths are validated via a new `_safe_relative_path()` helper that rejects `..`, absolute paths, control characters, Windows drive letters, and back-slashes. Each resolved path is re-checked against the project root and parent directories are inspected for symlinks before writing. Project name slugification consolidated into `slugify_project_name()`.
- **`.gitignore` hardening**: Explicitly ignore `data/orchestrator.db`, SQLite WAL/journal/SHM siblings, `data/backup/`, and `data/jobs.json` so they cannot be committed by accident (previously relied on staying untracked).

### Changed
- Pruned 15 expired trend snapshots under `data/trends/2026/01/` (90-day retention policy).
- `.env.example` and `website/.env.local` document the new `MOSS_API_KEY`, `MOSS_CORS_ORIGINS`, and `MOSS_BACKEND_URL` variables.

---

## [0.6.6] - 2026-02-01

### Added
- **Threads Adapter**: New signal adapter for Meta Threads (`threads.py`) — scrapes public profile pages to collect posts from tracked accounts (`@choi.openai`, `@unclejobs.ai`, `@feelfree_ai`) using embedded JSON extraction via httpx (no external library needed)
- Registered Threads adapter in aggregator, API `/adapters` endpoint, and adapter exports

---

## [0.6.5] - 2026-02-01

### Fixed

#### Backend Stability & Performance (System Audit)
- **Ollama Throttle Lock Bottleneck (H3)**: Lock is now released during `asyncio.sleep()` in `_wait_for_throttle`, preventing all coroutines from serializing when multiple agents request LLM simultaneously
- **Debate Timeout (H4)**: Added 45-minute overall timeout (`DEBATE_TIMEOUT_SECONDS`) to prevent infinite-running debates in production mode
- **API Error Response Consistency (H5)**: Replaced dict-based error returns (`{"error": "..."}`) with proper `HTTPException(status_code=404)` for debate detail, idea detail, idea lineage, and plan detail endpoints
- **Duplicate Project Generation (M1)**: Added duplicate check in `_create_project_record()` - returns existing project ID if one already exists with "generating" or "ready" status for the same plan
- **Job State Persistence (M2)**: Project generation job statuses now persist to `data/project_jobs.json` and survive server restarts
- **Plan Detail Missing `title_ko` (M3)**: Added `title_ko` and `final_plan_ko` fields to `/plans/{id}` response
- **Signal Pagination (M5)**: Replaced Python-level slicing with SQL `LIMIT/OFFSET` in `SignalRepository.get_recent()` and added `count_recent_filtered()` for accurate totals
- **Debate Pagination**: Debates endpoint now uses SQL-level pagination via `get_all_sessions()`
- **LLM Fallback Infinite Loop (L2)**: Fallback now wrapped in try/except - raises immediately if fallback also fails
- **Score Default 5.0 (L3)**: Removed arbitrary 5.0 default score when extraction fails; now logs warning and skips instead

### Changed
- **Config test_mode Unified (H2)**: Set `debate.test_mode: false` to match `throttling.test_mode: false` (production mode)
- **print → logger (L1)**: Replaced all `print()` calls with `logger.error()`/`logger.info()` in `ollama.py`, `router.py`, `aggregator.py`

---

## [0.6.4] - 2026-01-25

### Added

#### Dynamic Detail Pages for External Link Access
- **Direct URL Access**: External links now resolve to dedicated detail pages
  - `/signals/{id}` - Signal detail page
  - `/ideas/{id}` - Idea detail page
  - `/plans/{id}` - Plan detail page
  - `/projects/{id}` - Project detail page
- **SEO-Optimized Metadata**: Open Graph and Twitter card support for link sharing
- **New Backend Endpoint**: `GET /signals/{signal_id}` for single signal retrieval
- **Shared Layout Component**: `DetailPageLayout` with navigation, loading/error states
- **Multilingual Support**: Full EN/KO localization for detail pages

---

## [0.6.3] - 2026-01-25

### Added

#### Production-Quality Code Generation
- **Enhanced Plan Parser**: Deep LLM parsing with comprehensive extraction
  - New dataclasses: `DataEntity`, `ExternalService`, `UIComponent`, `SmartContractSpec`
  - `parse_deep_with_llm()` for detailed entity, service, and component extraction
  - External service detection (Twitter API, Coingecko, Etherscan, WebSocket, etc.)
- **Full Project Generator**: Production-ready code instead of scaffolds
  - `generate_full_project()` - Main entry point for high-quality generation
  - Complete FastAPI/Express backend with business logic
  - Complete Next.js/React frontend with all pages and components
  - Solidity smart contracts with Hardhat test framework
  - External service integration layers
  - Database schemas and migrations
  - Docker configuration

#### Priority-Based Project Generation
- **Auto-Generation for High-Priority Plans**: Score >= 8.0
  - Plans auto-approved and project generation triggered
  - Configurable threshold via `config.yaml` (`project.auto_generate.min_score`)
- **Manual Approval for Lower-Priority Plans**: Score < 8.0
  - Plans created with "draft" status
  - Requires manual approval before project generation

#### New API Endpoints for Manual Control
- `POST /plans/{plan_id}/approve` - Manually approve draft plans
  - Option to trigger project generation immediately (`generate_project=true`)
  - Allows users to control which low-scoring plans get developed
- `GET /plans/pending-approval` - List draft plans awaiting manual approval
  - Shows idea scores for decision context

### Changed
- Commit message updated from "scaffold" to "production-quality code"
- Project generation pipeline now produces complete, runnable code

---

## [0.6.2] - 2026-01-25

### Added

#### Pipeline Projects Stage
- **Pipeline Modal Support**: Projects stage now fully supported in pipeline status modal
  - Fetch and display projects with status badges
  - "View All Projects" button navigates to `/projects`
  - Empty state with helpful guidance
- **View Code on GitHub Button**: New prominent button in ProjectDetail modal
  - Links directly to project code directory: `github.com/.../tree/main/projects/{project-name}`
  - Separate from Issue link for clarity

#### Auto-Push to GitHub
- **Automatic Git Commit/Push**: Generated projects are now auto-committed and pushed
  - After scaffold generation, automatically runs `git add`, `git commit`, `git push`
  - Commit message: `feat: auto-generate project scaffold for {project-name}`
  - Push failure doesn't block project creation (warning logged)

### Fixed
- **PipelineDetail Projects Stage**: Fixed modal showing only "#" text when clicking Projects
  - Added `projects` stageId handling in data fetch
  - Added proper description, empty state emoji, and navigation

---

## [0.6.1] - 2026-01-25

### Added

#### Projects UI Integration
- **Projects Page**: New `/projects` page with status filtering (all/ready/generating/error)
  - Tech stack badges (frontend/backend/blockchain)
  - Directory path display
  - Files generated count
  - Click to open project detail modal
- **Dashboard Integration**: "Recent Projects" section showing latest 5 projects
  - Direct link to `/projects` page
  - Status indicators and tech stack display
- **Ideas Page Projects Tab**: Projects section added to Ideas page for quick access

### Fixed
- **API Client Timeout**: Increased timeout from 3s to 10s to handle network latency
  - Resolves "Using mock stats/pipeline due to API error" warnings
  - Prevents premature request abortion on slower connections
- **Projects Table Creation**: Fixed 500 error on `/projects` endpoint
  - Created missing `projects` table in database
  - Table now auto-created with other models

### Technical
- Added `ProjectsSection` component for reusable project list display
- Updated `ApiClient` with 10-second timeout (AbortController)
- Database migrations ensure `projects` table exists

---

## [0.6.0] "Project Generator" - 2026-01-25

### Added

#### Plan → Project Automatic Generation
- **Project Scaffold Module**: New `project/` package for automatic project generation from approved Plans
  - `parser.py` - Parses Plan markdown into structured data (TechStack, APIEndpoint, ProjectTask)
  - `templates.py` - Tech stack templates (Next.js, React, Vue, FastAPI, Express, Hardhat, Anchor)
  - `generator.py` - LLM-based code generation with task-specific model routing
  - `scaffold.py` - Orchestrates the full project generation pipeline
- **Task-Specific LLM Models**: Different models for different tasks
  - `glm-4.7-flash` - Fast plan parsing and structure extraction
  - `qwen2.5:32b` - Main code generation (components, APIs, models)
  - `llama3.3:70b` - Complex architecture design
  - `phi4:14b` - Simple tasks and fallback
- **Hybrid Trigger System**:
  - **Auto-generation**: Plans with score ≥ 8.0 automatically generate projects
  - **Manual button**: Lower-scored plans can trigger generation via UI
- **Database Schema**: Added `projects` table
  - `plan_id`, `name`, `directory_path`, `tech_stack` (JSON), `status`, `files_generated`
- **Project Repository**: Full CRUD operations for projects

#### New API Endpoints
- `POST /plans/{plan_id}/generate-project` - Trigger async project generation
- `GET /plans/{plan_id}/project` - Get project for a specific plan
- `GET /projects` - List all generated projects
- `GET /projects/{project_id}` - Project details
- `GET /jobs/{job_id}` - Check async job status

#### Frontend Updates
- **Generate Project Button**: Added to `PlanDetail.tsx` for approved plans
- **Project Status Display**: Shows generating spinner, ready state with tech stack badges, error state with retry
- **Job Polling**: Automatic status polling during generation
- **API Client Methods**: `generateProject()`, `getProjects()`, `getProjectDetail()`, `getJobStatus()`, `getPlanProject()`

### Changed
- Scheduler now integrates project auto-generation after debate completion
- Plan creation now properly saves `final_plan` and `final_plan_ko` content
- Pipeline flow extended: Ideas → Plans → Projects (for score ≥ 8.0)

### Configuration
New `project` section in `config.yaml`:
```yaml
project:
  auto_generate:
    enabled: true
    min_score: 8.0
    max_concurrent: 1
  llm:
    parsing: "glm-4.7-flash"
    code_generation: "qwen2.5:32b"
    architecture: "llama3.3:70b"
    fallback: "phi4:14b"
  output_dir: "projects"
```

### Technical
- Added `ProjectScaffold`, `ProjectCodeGenerator`, `PlanParser`, `TemplateManager` classes
- Added `Project` model and `ProjectRepository` to database layer
- Added `_auto_generate_project()` and `_load_project_config()` to scheduler
- Modified `_auto_score_and_save_ideas()` to pass `final_plan_content` for project generation
- Added `ApiProject`, `GenerateProjectResponse`, `ProjectJobStatus` TypeScript types

---

## [0.5.1] "Bilingual" - 2026-01-24

### Added

#### Bilingual Content Support (EN/KO)
- **Bidirectional Translation**: ContentTranslator now detects source language and translates accordingly
  - Korean content → English (main field) + Korean (`*_ko` field)
  - English content → English (main field) + Korean translation (`*_ko` field)
- **Database Schema**: Added Korean fields to Ideas and Plans
  - `Idea`: `title_ko`, `summary_ko`, `description_ko`
  - `Plan`: `title_ko`, `final_plan_ko`
- **Frontend Localization**: UI respects EN/KO toggle for all content display
  - Ideas list, detail modal
  - Plans list, detail modal
  - Trends list, detail modal
- **Migration Script**: `migrate_bilingual.py` to backfill existing data with translations
- **IdeaContent Component**: Structured JSON idea display with sections:
  - Core Analysis with colored borders
  - Opportunity/Risk grid with visual indicators
  - Proposal with feature lists and tech stack badges
  - Roadmap timeline
  - KPIs with target metrics

### Fixed
- **TrendHeatmap Size**: Reduced cell height from `aspect-square` to `h-6` for better fit
- **AdapterDetailModal**: Fixed empty modal on first open - now auto-selects first adapter
- **Trend Analysis**: Changed LLM prompt to generate English-only content (Korean via translation)
- **Pipeline Modal**: Fixed VIEW ALL button for signals and trends stages
- **Date Locale Display**: Fixed dates showing Korean format in EN locale
  - Updated `date.ts` with `toBrowserLocale()` helper (en→en-US, ko→ko-KR)
  - Default locale changed from 'ko-KR' to 'en'
  - All date formatting functions now respect user locale
- **Debate JSON Content**: Fixed raw JSON displaying in debate modals
  - Added `extractReadableContent()` helper to parse JSON and extract readable fields
  - Applied to LiveDebateViewer, DebateConversation, DebateTimeline components
- **Markdown Rendering**: Added markdown support in debate messages
  - Created `MarkdownContent` component using `marked` library
  - `**bold**` renders as cyan text, `*italic*` as purple
  - Styled lists, code blocks, headers, blockquotes

### Technical
- Added `ContentTranslator` class with `ensure_bilingual()`, `translate_to_english()`, `translate_to_korean()` methods
- Added `_detect_language()` helper for Korean/English detection
- Updated `_auto_score_and_save_ideas()` to use bilingual translation
- Added `getLocalizedText()` helper to frontend components
- Added `IdeaContent.tsx` component for structured JSON parsing and display
- Disabled signal translation for performance (signals are English-only)

---

## [0.5.0] - 2026-01-24

### Added

#### Enhanced Creativity Framework (Phase 1)
- **SCAMPER Creativity Prompts**: Divergence phase now uses structured SCAMPER techniques
  - Round 1: Substitute & Combine (replace components, merge concepts)
  - Round 2: Adapt & Modify (cross-industry inspiration, scale changes)
  - Round 3: Put to Other Use, Eliminate & Reverse (paradox thinking)
- **Lateral Thinking Prompts**: Alternating creativity techniques per round
  - Blue Sky Thinking (constraint-free imagination)
  - Paradox Approach (reverse problem solving)
  - Cross-Domain Innovation (industry pattern borrowing)
- **Higher Temperature**: Divergence temperature increased to 0.95 (from 0.9) for more creative outputs

#### Coingecko Market Adapter
- **Trending Coins**: Real-time search trend detection
- **Top Movers**: Top 5 gainers and losers (24h, >10% change threshold)
- **Volume Spikes**: Unusual trading activity detection (volume >50% of market cap)
- **Global Market Stats**: Total market cap changes, BTC dominance alerts
- **Tracked Coins**: 16 specific coins including MOC (Mossland)

#### Signal Time Decay
- **Freshness Weighting**: Signal scores now decay based on age
  - 0-1 hours: 100% weight
  - 1-6 hours: 90% weight
  - 6-12 hours: 80% weight
  - 12-24 hours: 60% weight
  - 24-48 hours: 40% weight
  - 48+ hours: 20% weight
- **Decay Logging**: Debug info shows decay distribution per analysis cycle

#### Dashboard UX Improvements
- **Skeleton Loaders**: Trends page and Ideas page now show proper loading skeletons
  - Trend cards with score, title, keywords placeholders
  - Pipeline view with stage indicators
  - List items with badge and content placeholders

### Changed
- Signal aggregator now includes Coingecko adapter by default
- Trend analysis applies time decay before processing signals

### Technical
- Added `SCAMPER_TECHNIQUES` and `LATERAL_THINKING` dictionaries to `DebateProtocol`
- Added `get_creativity_technique()` method to `DebateProtocol`
- Added `CoingeckoAdapter` class with trending, movers, global stats, tracked coins methods
- Added `_calculate_time_decay()` and `_apply_time_decay_to_signals()` functions to scheduler
- Added `TrendSkeleton`, `PipelineSkeleton`, `ListItemSkeleton`, `ListSkeleton` React components

---

## [0.4.2] - 2026-01-24

### Added

#### Idea Creativity & Diversity Improvements
- **Diversity-Aware Agent Selection**: Personality-axis balanced selection ensures diverse agent types in each debate round
- **Challenger Role Guarantee**: Each round now includes at least one challenger-type agent to prevent groupthink
- **Idea Similarity Feedback**: Agents receive Jaccard similarity scores and differentiation hints when generating ideas
- **Enhanced Novelty Weight**: Convergence phase now weights novelty at 30% (up from 20%) as the most important criterion

#### Signal Quality Improvements
- **Content Validation Layer**: Filters signals by minimum length, language (Korean/English), and spam patterns
- **Semantic Duplicate Removal**: Jaccard similarity-based deduplication removes semantically similar content from different sources
- **Engagement Thresholds**: Social adapters now filter low-engagement posts (Reddit: 10+ score, 3+ comments; Farcaster: 3+ likes or 1+ recast)
- **Sentiment Analysis**: Keyword-based sentiment detection (positive/negative/neutral) integrated into signal scoring

### Changed
- Signal deduplication now uses 3-phase approach: hash dedup → content validation → semantic dedup
- Convergence evaluation criteria restructured with explicit weighted scoring formula
- Twitter API search now filters tweets by engagement metrics

### Technical
- Added `_select_agents_with_diversity()`, `_ensure_challenger_presence()` methods to `MultiStageDebate`
- Added `_calculate_idea_similarity()`, `_get_similarity_feedback()` methods for differentiation hints
- Added `_validate_signal_content()`, `_is_semantic_duplicate()` methods to `SignalAggregator`
- Added `_analyze_sentiment()`, `_score_sentiment()` methods to `SignalScorer`
- Added `_meets_engagement_threshold()` methods to social adapters

---

## [0.4.1] - 2026-01-24

### Added

#### Expanded Signal Adapters (9 Adapters Total)
- **Twitter/X Adapter**: Nitter RSS pool with 10 instances, 20+ tracked accounts
- **Discord Adapter**: Bot API and webhook support, 7 tracked servers
- **Lens Protocol Adapter**: GraphQL API, 10 tracked profiles
- **Farcaster Adapter**: Neynar API, 10 tracked users and channels
- **OnChain Enhancements**: DEX volume, whale alerts, stablecoin flows via DefiLlama

#### Idea Quality Improvements
- **JSON Output Format**: Structured LLM responses for better parsing
- **Content Validation**: Required sections with minimum character counts
- **Title Quality Scoring**: 0-10 scale based on length, tech keywords, Mossland relevance

#### Dashboard UX Improvements
- **Adapter Detail Modal**: Click signals.conf to view detailed adapter info with health status
- **Skeleton Loading**: Activity feed now shows skeleton animation while loading
- **Real Activity Data**: `/activity` API returns actual DB data instead of mock timestamps

#### New API Endpoints
- `GET /adapters` - List all signal adapters with status, sources, and health info

### Changed
- Activity feed no longer uses mock data; displays real timestamps (HH:MM:SS format)
- Dashboard loads activity data with skeleton loading state

### Technical
- Added `AdapterInfo` type and `fetchAdapters()` API client method
- Added `isLoading` prop to `ActivityFeed` component

---

## [0.4.0] "Signal Storm" - 2026-01-22

### Added

#### Multi-Stage Debate System (34 Agents)
- **3 Debate Phases**: Divergence (12 agents) → Convergence (12 agents) → Planning (10 agents)
- **4-Axis Personality System**: Creativity, Analytical, Risk Tolerance, Collaboration (0-10 scale)
- **Debate Protocol**: `debate/protocol.py` - phases, message types, configuration
- **Multi-Stage Orchestration**: `debate/multi_stage.py` - complete debate flow management

#### Diverse Signal Sources (5 Adapters)
- **RSS Adapter**: 17 feeds across AI, Crypto, Finance, Security, Dev categories
- **GitHub Events Adapter**: Repository activity, trending projects, issue/PR analysis
- **On-Chain Adapter**: MOC token transactions, smart contract events, DeFi metrics
- **Social Media Adapter**: X (Twitter) mentions, community sentiment analysis
- **News API Adapter**: Real-time news aggregation, keyword-based filtering

#### Hybrid LLM Router
- **Local Models**: Ollama integration (Qwen 32B, Llama 3, Mistral)
- **Cloud APIs**: Claude, GPT-4, Gemini fallback
- **Intelligent Routing**: Automatic fallback between local and cloud
- **Budget Management**: Cost tracking and limits

#### PM2 Process Management
- **6 Services**: signals (30min), debate (6hr), backlog (daily), web, api, health (5min)
- **Scheduler Module**: `scheduler/tasks.py` - async task implementations
- **CLI Entry Point**: `scheduler/__main__.py` - command line interface
- **Ecosystem Config**: `ecosystem.config.js` - PM2 configuration

#### FastAPI Backend
- **REST API**: `/health`, `/status`, `/signals`, `/debates`, `/agents`, `/docs`
- **API Module**: `api/main.py` - FastAPI application
- **Port 3001**: Separate from web dashboard

#### CLI-Style Web Interface
- **Retro Terminal Theme**: JetBrains Mono font, scanlines, glow effects
- **Terminal Components**: `TerminalWindow.tsx`, status indicators
- **Agents Page**: `/agents` - displays all 34 agent personas
- **Mobile Responsive**: Adapted for all screen sizes

### Changed

- Dashboard redesigned with CLI/terminal aesthetic
- Navigation updated with `$` prompt style
- Footer updated with version "Signal Storm"
- Replaced GitHub Actions scheduling with PM2

### Removed

- `.github/workflows/backlog.yml` - replaced by PM2 moss-ao-backlog
- `.github/workflows/orchestrator.yml` - replaced by PM2 moss-ao-debate

### Technical Details

- Python 3.12 required for API server
- Virtual environment setup: `.venv/`
- Service names prefixed with `moss-ao-` to avoid conflicts

## [0.4.0] - 2026-01-04

### Added

#### Multi-Agent Debate System for PLAN Generation
- **4 Debate Roles**: Founder, VC (a16z/Sequoia level), Accelerator (YC/Techstars level), Founder Friend
- **3 AI Providers**: Claude, ChatGPT, Gemini rotate roles each round for diverse perspectives
- **Role Rotation**: Each round assigns different AI to different roles
- **Early Termination**: Debate ends when founder judges "Sufficiently Improved" or max 5 rounds
- **Discussion Records**: Full debate history saved as collapsible GitHub comments

#### Debate Module (`src/agentic_orchestrator/debate/`)
- `roles.py` - Role definitions with bilingual prompts (English + Korean)
- `moderator.py` - Round rotation matrix and termination logic
- `debate_session.py` - Full debate session orchestration
- `discussion_record.py` - GitHub comment formatting

#### Plan Rejection Workflow
- **`reject:plan` Label**: Reject a PLAN and regenerate from original idea
- **`ao backlog reject <plan_number>`**: CLI command to reject plans
- **Automatic Reset**: Rejected plan closes, original idea gets `promote:to-plan` restored

#### Bilingual Support
- All debate prompts in English with Korean translation request
- Discussion records display in "English / 한국어" format
- Plan extraction uses `[PLAN_START]`/`[PLAN_END]` markers for reliability

### Changed

- PlanGenerator now uses multi-agent debate when all 3 providers available
- Falls back to single-agent generation if providers unavailable
- Rejection processing runs before promotion processing in `run_cycle()`
- `_find_existing_plan_for_idea()` only searches open issues (ignores closed/rejected)

### Configuration

New `debate` section in `config.yaml`:
```yaml
debate:
  enabled: true
  max_rounds: 5
  min_rounds: 1
  require_all_approval: false
```

## [0.3.0] - 2026-01-04

### Added

#### Trend-Based Idea Generation
- **RSS Feed Integration**: Fetches articles from 17 RSS feeds across 5 categories (AI, Crypto, Finance, Security, Dev)
- **Trend Analysis**: Uses Claude to identify trending topics from news articles
- **Multi-Period Analysis**: Analyzes trends over 24 hours, 1 week, and 1 month periods
- **Trend-Based Ideas**: Generates Web3 micro-service ideas based on current trends
- **Trend Storage**: Stores trend analysis results as Markdown files with YAML frontmatter

#### New Trends Module
- `FeedFetcher` - RSS/Atom feed parsing with feedparser
- `TrendAnalyzer` - LLM-based trend extraction using Claude
- `TrendStorage` - Markdown file storage in `data/trends/YYYY/MM/`
- `TrendBasedIdeaGenerator` - Generates ideas from trending topics

#### New Labels
- `source:trend` - Tags ideas generated from trend analysis

#### New CLI Commands
- `ao backlog analyze-trends` - Fetch and analyze RSS feeds
- `ao backlog generate-trends` - Generate trend-based ideas
- `ao backlog trends-status` - Show trend analysis history

#### Updated CLI
- `ao backlog run` now supports `--trend-ideas` and `--analyze-trends` options
- `ao backlog status` shows trend-based idea count

#### GitHub Actions
- Schedule changed to 8 AM KST (23:00 UTC) daily
- New `run-with-trends` command (default daily run)
- Added `generate-trends`, `analyze-trends`, `trends-status` commands

### Changed

- Default daily run: 1 traditional idea + 2 trend-based ideas with trend analysis
- Trend data stored in `data/trends/` directory (90-day retention)

### Configuration

New `trends` section in `config.yaml`:
```yaml
trends:
  ideas:
    traditional_count: 1
    trend_based_count: 2
  periods: [24h, 1w, 1m]
  storage:
    directory: data/trends
    retention_days: 90
  feeds:
    ai: [OpenAI News, Google Blog, arXiv AI, TechCrunch, Hacker News]
    crypto: [CoinDesk, Cointelegraph, Decrypt, The Defiant, CryptoSlate]
    finance: [CNBC Finance]
    security: [The Hacker News, Krebs on Security]
    dev: [The Verge, Ars Technica, Stack Overflow Blog]
```

### Dependencies

- Added `feedparser>=6.0.0` for RSS/Atom parsing

## [0.2.1] - 2025-01-04

### Added

#### Stability Improvements
- **Idempotency Protection**: Prevents duplicate plan/dev creation by checking labels and existing artifacts
- **Lock Timeout Mechanism**: Detects and removes stale locks from crashed processes
- **Environment Validation**: Early validation of required environment variables with helpful error messages
- **Partial Failure Rollback**: Automatically closes plan issues if subsequent operations fail

#### New Tests
- 22 new tests for v0.2.1 features (idempotency, lock timeout, environment validation, rollback)
- Total test count increased from 83 to 105

### Changed

- Lock file now includes PID and timestamp for stale lock detection
- Config.get() now properly supports nested key lookups with defaults
- CLI commands validate environment before execution

### Technical Details

- Lock timeout defaults to 300 seconds (configurable via config.yaml)
- Process liveness check using signal 0
- Rollback adds `rollback:failed` label to closed issues

## [0.2.0] - 2025-01-03

### Added

#### Backlog-Based Workflow
- **GitHub Issues as UI/DB**: Ideas and plans are now stored as GitHub Issues
- **Human-in-the-Loop**: Label-based promotion system for stage transitions
- **GitHubClient**: Full GitHub API integration for Issues and Labels
- **BacklogOrchestrator**: New orchestrator for backlog-based workflow

#### Promotion System
- `promote:to-plan` label for promoting ideas to planning stage
- `promote:to-dev` label for promoting plans to development stage
- `processed:to-plan` and `processed:to-dev` labels for tracking
- Automatic label management after processing

#### New CLI Commands
- `ao backlog run`: Run full orchestration cycle
- `ao backlog generate`: Generate new idea issues
- `ao backlog process`: Process pending promotions
- `ao backlog status`: Show backlog status
- `ao backlog setup`: Set up required labels in repository

#### GitHub Integration
- Issue templates for ideas (`idea.yml`) and plans (`plan.yml`)
- Scheduled workflow (`backlog.yml`) for automated execution
- Labels documentation (`docs/labels.md`)

#### Concurrency Control
- File-based locking to prevent simultaneous runs
- Duplicate prevention via processed labels
- Safe for cron/scheduled execution

### Changed

- Workflow model changed from auto-progression to human-guided
- README.md rewritten for backlog-based workflow
- Updated `.env.example` with GitHub configuration variables

### Technical Details

- Uses `httpx` for async-capable HTTP client
- 83 unit tests passing
- Full dry-run support for testing

## [0.1.0] - 2025-01-03

### Added

#### Core Orchestrator
- State machine with stages: IDEATION → PLANNING_DRAFT → PLANNING_REVIEW → DEV → QA → DONE
- YAML-based state persistence (`.agent/state.yaml`)
- Iteration tracking with configurable limits for planning and development cycles
- Quality metrics tracking (review scores, test results)

#### LLM Provider Adapters
- **Claude Provider**: Supports both CLI mode (Claude Code) and API mode
- **OpenAI Provider**: GPT models for independent review (default: gpt-5.2-chat-latest)
- **Gemini Provider**: Fast agentic tasks (default: gemini-3-flash-preview)
- Automatic retry with exponential backoff for rate limits
- Fallback model support for all providers
- Quota exhaustion detection with proper error handling

#### Stage Handlers
- **Ideation**: Generates Web3 service ideas for Mossland ecosystem
- **Planning Draft**: Creates PRD, Architecture, Tasks, Acceptance Criteria
- **Planning Review**: External review using OpenAI/Gemini
- **Development**: Implements features using Claude Code
- **Quality Assurance**: Runs tests, code review, security checks
- **Done**: Creates completion report

#### CLI Commands
- `ao init`: Initialize new project
- `ao step`: Execute single pipeline step
- `ao loop`: Run in continuous mode with guardrails
- `ao status`: Show current status (supports --json)
- `ao resume`: Resume from paused state
- `ao reset`: Reset orchestrator state
- `ao push`: Push changes to remote

#### Error Handling
- Rate limit detection with automatic wait-and-retry
- Quota exhaustion alerts (`alerts/quota.md`)
- Sensitive data masking in logs and commits
- Maximum retry limits to prevent infinite loops

#### Infrastructure
- Prompt templates for all stages
- GitHub Actions CI workflow (test, lint)
- GitHub Actions orchestrator workflow (scheduled/manual)
- Comprehensive unit tests

### Configuration
- Environment variables via `.env`
- YAML configuration (`config.yaml`)
- Dry-run mode for testing
- Pinned model versions for reproducibility

## [Unreleased]

### Planned
- Enhanced smart contract development support
- Multi-project orchestration
- Web dashboard for monitoring
- Slack/Discord notifications
- Cost tracking and budget limits
