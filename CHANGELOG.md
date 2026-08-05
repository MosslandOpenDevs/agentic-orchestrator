# Changelog

[한국어](CHANGELOG.ko.md) | **English**

All notable changes to the Mossland Agentic Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Docs-only deploys no longer take a pre-deploy DB snapshot. Nothing restarts on a docs sync and `reset --hard` cannot touch the untracked DB, so the snapshot protected nothing — while each one rotated the 7-slot backup window, meaning a burst of docs merges could churn days of restore points into minutes. Code deploys still snapshot first. Gate mutation-verified.

## [0.6.15] - 2026-08-05

### Fixed
- **Scaffold no longer pushes to origin/main from the production server.** `_git_commit_and_push` ran unconditionally after every generated project — `git add` + `commit` + `git push origin main` on whatever checkout the scheduler runs in. It has only been failing (with warning spam) since /projects/ became gitignored; before that this path is exactly where the server's local "feat: generate production-quality code…" commits on main came from. config.yaml has carried `git.auto_push: false` all along — nothing read it. The scaffold now honors it (default false, fail-closed when config is unreadable, explicit constructor argument wins), and the gate placement itself is pinned by a test.
- **Idea scoring joins structured outputs.** The score parser had the same fenced-JSON fragility as trends, with a worse blast radius: its except-path *invents* a neutral 5.0 score, so a parse failure silently files every idea in the backlog band regardless of quality. The route now attaches `SCORE_RESPONSE_SCHEMA` (grammar-enforced; all four dimensions required) and a 1,024-token output budget; the neutral fallback remains as a transport-error path only.
- **Social-share previews pointed at localhost.** `metadataBase` was never set, so Next.js resolved the relative `og-image.png` against `http://localhost:3000` in production builds — every OG/Twitter card for ao.moss.land carried a localhost image URL (visible in the served HTML). Set to `https://ao.moss.land`.
- Documentation told two lies about the embedding model, now corrected in CLAUDE.md and code comments: no code path calls an embedding API (signal "semantic dedup" is title-token Jaccard, `signals/aggregator.py::_is_semantic_duplicate`), and the production Ollama host does not have `qwen3-embedding:0.6b` pulled. The hierarchy entry stays as an explicitly-labeled reserved slot.

### Added
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
