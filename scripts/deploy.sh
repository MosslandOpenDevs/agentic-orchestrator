#!/usr/bin/env bash
#
# MOSS.AO pull-based auto-deploy.
#
# Runs ON the application server (the box PM2 lives on) and brings the checkout
# up to origin/main. Idempotent: when the last successful deploy already matches
# the remote tip it does nothing and exits 0, so it is safe to run from PM2's
# cron every few minutes.
#
# Why pull-based instead of a push from CI: the app server has no public inbound
# route (it is reachable over Tailscale only), the repo is public (a self-hosted
# GitHub runner on a public repo is a known footgun), and repo-admin rights are
# needed to add runners/secrets. Fetching a public repo outbound needs none of
# that -- no deploy key, no open port, no GitHub configuration at all.
#
# Deploy state is NOT the git HEAD. `git reset --hard` moves HEAD before the
# build and health check have run, so a poller killed mid-deploy (PM2
# max_memory_restart SIGKILL, OOM, reboot) would leave HEAD at the new commit
# with the old build still live -- and every later tick would read "up to date"
# and hide the failure forever. Instead the SHA of the last SUCCESSFUL deploy is
# recorded in DEPLOY_STATE_FILE (inside .git/, out of reach of the reset), it is
# written only after the health check passes, and a tick whose state disagrees
# with HEAD treats the previous deploy as unfinished and retries it. Repeated
# failures of the same target SHA back off exponentially (DEPLOY_RETRY_*)
# instead of re-running the full snapshot/build/restart/alert cycle every five
# minutes; a new commit on the remote resets the backoff at once.
#
# The script body only runs from main(), invoked on the last line: this file
# deploys itself, and bash reads scripts incrementally, so without the wrapper
# an in-place update mid-run would have bash continue at a byte offset of the
# NEW file. main() forces the whole file to be parsed before any of it runs.
#
# Usage:
#   scripts/deploy.sh              # deploy if the remote moved (normal cron use)
#   scripts/deploy.sh --check      # report what would happen, change nothing
#   scripts/deploy.sh --force      # ignore the CI gate, busy-scheduler,
#                                  # dirty-tree and local-commit guards and the
#                                  # failure backoff (manual use)
#
# Configuration (env, all optional -- ecosystem.config.js loads .env first):
#   DEPLOY_BRANCH          branch to track                     (default: main)
#   DEPLOY_REMOTE          git remote                          (default: origin)
#   DEPLOY_REQUIRE_CI      1 = only deploy CI-green commits     (default: 1)
#   DEPLOY_REQUIRE_CI_JOBS check-run names that must have passed (comma list)
#   DEPLOY_GITHUB_REPO     owner/name used for the CI query
#   DEPLOY_API_URL         backend health URL                  (:3001)
#   DEPLOY_WEB_URL         frontend health URL                 (:3000)
#   DEPLOY_HEALTH_RETRIES  health poll attempts                (default: 20)
#   DEPLOY_HEALTH_INTERVAL seconds between attempts            (default: 3)
#   DEPLOY_ALERT_WEBHOOK   Slack/Discord webhook for failures   (default: none)
#   DEPLOY_VERBOSE         1 = also log no-op ticks            (default: 0)
#   DEPLOY_STATE_FILE      last-success SHA    (default: .git/moss-ao-deployed-sha)
#   DEPLOY_ATTEMPT_FILE    per-SHA attempt journal used for the failure backoff
#                                      (default: .git/moss-ao-deploy-attempt)
#   DEPLOY_RETRY_BASE_MIN  backoff after the 1st failure, minutes  (default: 5)
#   DEPLOY_RETRY_MAX_MIN   backoff cap, minutes                (default: 60)
#   DEPLOY_CI_UNKNOWN_ALERT consecutive undeterminable-CI ticks before
#                           escalating from "defer quietly" to ERROR+alert
#                                                            (default: 3)
#   PYTHON_BIN / PM2_BIN / NPM_BIN / UV_BIN / GITHUB_TOKEN
#
# Dependency install adapts to the checkout: `uv sync` when the venv is
# uv-managed (as on the production box, whose .venv contains no pip at all),
# `pip install -e .` otherwise.
#
# Data safety: this script only ever runs `git reset --hard`, which leaves
# untracked files alone. It must NEVER run `git clean` -- data/orchestrator.db,
# data/backup/, .env and website/.env.local live on the server and are untracked
# (see CLAUDE.md, the 2026-07 outage). tests/test_deploy.py guards that.

set -euo pipefail

# ---------------------------------------------------------------------------
# Env hygiene. When this script runs under PM2 (the moss-ao-deploy poller),
# PM2 injects the poller's OWN process config into the environment as plain
# variables -- cron_restart, autorestart, watch, ... -- and PM2 reads those
# same names back as config keys. Any `pm2 ... --update-env` (or `pm2 start`)
# executed with them present stamps the poller's config onto the target app:
# that is exactly how moss-ao-api/web ended up with the deploy cron attached
# and were force-restarted every 5 minutes (2026-08-05 incident; see
# docs/deployment.md, "cron_restart 오염"). Scrub them so no pm2 invocation
# anywhere in this script can inherit them.
# ---------------------------------------------------------------------------
unset -v cron_restart autorestart watch instances exec_mode \
         max_memory_restart node_args name namespace || true

log() {
  local line
  line="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  echo "${line}"
  mkdir -p "$(dirname "${DEPLOY_LOG}")" 2>/dev/null || true
  echo "${line}" >>"${DEPLOY_LOG}" 2>/dev/null || true
}

# Read one KEY=value out of a dotenv file: last occurrence wins, surrounding
# quotes and a trailing CR are stripped. Deliberately does NOT source the
# file -- deploy.sh must not inherit whatever else lives in .env.
env_value_from_file() {
  local file="$1" key="$2"
  sed -n "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//p" "${file}" 2>/dev/null \
    | tail -1 \
    | sed -e 's/\r$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"
}

# Only reaches the operator when a webhook is configured; never fatal itself.
alert() {
  [ -n "${DEPLOY_ALERT_WEBHOOK}" ] || return 0
  local text="$1"
  curl -fsS -m 10 -X POST -H 'Content-Type: application/json' \
    -d "$(printf '{"text":%s,"content":%s}' \
            "$(json_string "${text}")" "$(json_string "${text}")")" \
    "${DEPLOY_ALERT_WEBHOOK}" >/dev/null 2>&1 || true
}

json_string() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1" 2>/dev/null \
    || printf '"%s"' "$1"
}

# ---------------------------------------------------------------------------
# Single-flight lock. The lock directory records its owner's PID: a poller
# killed with SIGKILL (PM2 max_memory_restart, OOM) never runs its EXIT trap,
# and making every later tick wait out DEPLOY_LOCK_STALE_MIN would stall
# deploys for that long. A lock whose recorded owner is no longer alive is
# reclaimed immediately; the age check stays as a backstop for locks with an
# unreadable PID file (crash before the write, recycled PID).
# ---------------------------------------------------------------------------
acquire_lock() {
  mkdir -p "$(dirname "${DEPLOY_LOCK}")"
  if mkdir "${DEPLOY_LOCK}" 2>/dev/null; then
    printf '%s\n' "$$" >"${DEPLOY_LOCK}/pid" 2>/dev/null || true
    return 0
  fi

  local owner
  owner=$(cat "${DEPLOY_LOCK}/pid" 2>/dev/null || true)
  case "${owner}" in *[!0-9]*|'') owner="" ;; esac

  if [ -n "${owner}" ] && ! kill -0 "${owner}" 2>/dev/null; then
    log "WARN lock owner (pid ${owner}) is gone -- reclaiming its lock"
    rm -rf "${DEPLOY_LOCK}"
  elif [ -n "$(find "${DEPLOY_LOCK}" -maxdepth 0 -mmin "+${DEPLOY_LOCK_STALE_MIN}" 2>/dev/null)" ]; then
    log "WARN stale lock older than ${DEPLOY_LOCK_STALE_MIN}m -- reclaiming"
    rm -rf "${DEPLOY_LOCK}"
  else
    if [ "${DEPLOY_VERBOSE}" = "1" ]; then
      log "another deploy is running -- skipping"
    fi
    return 1
  fi

  if mkdir "${DEPLOY_LOCK}" 2>/dev/null; then
    printf '%s\n' "$$" >"${DEPLOY_LOCK}/pid" 2>/dev/null || true
    return 0
  fi
  log "could not reclaim lock; skipping"
  return 1
}

# CI gate: deploy only commits GitHub Actions has gone green on.
# Returns one of: success | failure | pending | none | unauthorized | unknown
#
# `unauthorized` exists because the two ways this call can fail need opposite
# responses. A transient network blip should be retried silently on the next
# tick. A missing or rejected token cannot heal on its own: the request goes
# out anonymous, GitHub rate-limits the server's shared IP with a 403, and the
# deploy defers -- forever, while the log says only "network/API". That is how
# a token dropping out of the poller's environment would silently stop every
# deploy with no other symptom.
ci_conclusion() {
  local sha="$1" url body http
  url="https://api.github.com/repos/${DEPLOY_GITHUB_REPO}/commits/${sha}/check-runs"

  # -sS (not -fsS): we need the body and status of an error response to tell
  # 403-rate-limited apart from a connection failure.
  body=$(curl -sS -m 20 -w $'\n%{http_code}' \
    -H 'Accept: application/vnd.github+json' \
    ${GITHUB_TOKEN:+-H "Authorization: Bearer ${GITHUB_TOKEN}"} \
    "${url}" 2>/dev/null) || { echo "unknown"; return 0; }

  http=${body##*$'\n'}
  body=${body%$'\n'*}

  case "${http}" in
    401|403) echo "unauthorized"; return 0 ;;
    2*) ;;
    *) echo "unknown"; return 0 ;;
  esac

  printf '%s' "${body}" | REQUIRED_JOBS="${DEPLOY_REQUIRE_CI_JOBS}" python3 -c '
import json, os, sys
try:
    runs = json.load(sys.stdin).get("check_runs", [])
except Exception:
    print("unknown"); raise SystemExit
# Zero checks is not evidence of success. GitHub commonly has not registered
# them yet when the 5-minute poller fires seconds after a push, so treat it the
# same as "still running": defer and look again next tick.
if not runs:
    print("none"); raise SystemExit

hard_fail = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
# Only these two mean "this check verified the commit". skipped/stale/null do
# not, and were previously counted as green by being absent from the bad set.
green = {"success", "neutral"}

if any(r.get("status") != "completed" for r in runs):
    print("pending"); raise SystemExit
if any(r.get("conclusion") in hard_fail for r in runs):
    print("failure"); raise SystemExit
if any(r.get("conclusion") not in green for r in runs):
    print("incomplete"); raise SystemExit

# Optional: pin the exact jobs that must have reported. Without it, a workflow
# that stops running the tests still reads as green.
required = [j.strip() for j in (os.environ.get("REQUIRED_JOBS") or "").split(",") if j.strip()]
passed = {r.get("name") for r in runs if r.get("conclusion") in green}
if any(job not in passed for job in required):
    print("missing-required"); raise SystemExit

print("success")
' 2>/dev/null || echo "unknown"
}

# Consecutive ticks where CI status could not be determined, per target SHA.
# One blip is noise; a run of them means the gate is stuck and no deploy will
# ever happen until someone looks.
ci_unknown_streak() {
  local sha="$1" prev_sha prev_n
  read -r prev_sha prev_n < <(cat "${DEPLOY_CI_UNKNOWN_FILE}" 2>/dev/null || echo "")
  if [ "${prev_sha:-}" = "${sha}" ]; then
    prev_n=$(( ${prev_n:-0} + 1 ))
  else
    prev_n=1
  fi
  printf '%s %s\n' "${sha}" "${prev_n}" >"${DEPLOY_CI_UNKNOWN_FILE}" 2>/dev/null || true
  echo "${prev_n}"
}

# A debate takes ~30 min and runs as its own PM2 cron process. Reinstalling
# Python packages underneath it can break a live import, so back-end changes
# wait for the next tick; a website-only change cannot affect it and proceeds.
scheduler_busy() {
  "${PM2_BIN}" jlist 2>/dev/null | python3 -c '
import json, sys
watch = {"moss-ao-debate", "moss-ao-trends", "moss-ao-backlog", "moss-ao-signals"}
try:
    procs = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
busy = [p["name"] for p in procs
        if p.get("name") in watch
        and (p.get("pm2_env") or {}).get("status") == "online"]
print(",".join(busy))
' 2>/dev/null || echo ""
}

# uv-managed checkout? The venv records how it was built, and that is the
# authoritative answer. uv.lock used to imply "uv" on its own, which was fine
# while the lockfile was untracked (a property of the machine); it is committed
# now, so every checkout has one and it can only decide the case where no venv
# exists yet.
uses_uv() {
  [ -x "${UV_BIN}" ] || return 1
  if [ -f "${REPO_ROOT}/.venv/pyvenv.cfg" ]; then
    grep -qs '^uv = ' "${REPO_ROOT}/.venv/pyvenv.cfg"
    return
  fi
  [ -f "${REPO_ROOT}/uv.lock" ]
}

# Swap the staged frontend build into place: two renames, run immediately
# before the web restart, so the live .next is only ever replaced whole --
# never partially overwritten by a build in progress.
promote_web_build() {
  if [ ! -d website/.next.new ]; then
    # The build wrote straight into .next: this checkout's next.config.ts does
    # not honour NEXT_DIST_DIR (or the build tool is stubbed, as in the test
    # harness). Nothing to swap -- same behaviour as the pre-staging deploy.
    log "WARN website/.next.new missing after build -- built in place, nothing to swap"
    return 0
  fi
  rm -rf website/.next.old
  if [ -d website/.next ]; then
    mv website/.next website/.next.old \
      || { log "ERROR could not move the live .next aside"; return 1; }
  fi
  if ! mv website/.next.new website/.next; then
    log "ERROR could not promote the staged build"
    [ -d website/.next.old ] && mv website/.next.old website/.next 2>/dev/null
    return 1
  fi
  rm -rf website/.next.old
}

# Build + restart for whatever the current checkout is. Used for the deploy and,
# unchanged, for the rollback -- so a rollback restores a consistent build too.
#
# `set -e` does not apply inside a function invoked as an `if` condition, so
# every step propagates its own failure explicitly.
build_and_restart() {
  local py="$1" web="$2" pydeps="$3" nodedeps="$4"

  if [ "${pydeps}" = "1" ]; then
    # The production checkout's .venv is created and owned by `uv` and has no
    # pip inside it, so `pip install -e .` there fails outright; a plain
    # pip/venv checkout is still the documented local setup. Use whichever
    # this checkout actually is.
    if uses_uv; then
      # --frozen installs strictly from the committed uv.lock and never
      # rewrites it. Without it a re-resolution would modify a *tracked* file
      # in the server checkout, and the dirty-tree guard would then abort every
      # subsequent 5-minute tick until someone SSHed in. It also means
      # production installs exactly the graph CI verified.
      log "uv sync --frozen (dependencies changed)"
      "${UV_BIN}" sync --frozen --quiet || { log "ERROR uv sync failed"; return 1; }
    else
      log "pip install -e . (dependencies changed)"
      "${PYTHON_BIN}" -m pip install -e . --quiet || { log "ERROR pip install failed"; return 1; }
    fi
  fi

  if [ "${web}" = "1" ]; then
    if [ "${nodedeps}" = "1" ]; then
      log "npm ci (dependencies changed)"
      (cd website && "${NPM_BIN}" ci --no-audit --no-fund) \
        || { log "ERROR npm ci failed"; return 1; }
    fi
    # NEXT_PUBLIC_* is baked in at build time, so the frontend always needs a
    # rebuild -- restarting alone would serve the previous bundle. The build
    # goes into a staging dir (website/.next.new -- next.config.ts honours
    # NEXT_DIST_DIR) rather than the live .next that moss-ao-web is serving
    # from, so a failed or SIGKILLed build can never leave the live dir
    # half-written; promote_web_build swaps it in right before the restart.
    #
    # The live .next/types were generated for the OLD commit and are matched
    # by website/tsconfig.json, so a page deleted in this deploy would fail
    # the staged build's typecheck against them. They are typecheck-time
    # only, never served -- drop them. The previous build cache is seeded
    # into the staging dir to keep builds incremental.
    rm -rf website/.next/types
    if [ -d website/.next/cache ] && [ ! -d website/.next.new ]; then
      mkdir -p website/.next.new
      cp -R website/.next/cache website/.next.new/cache 2>/dev/null || true
    fi
    log "npm run build"
    (cd website && NEXT_DIST_DIR=".next.new" "${NPM_BIN}" run build) \
      || { log "ERROR npm run build failed"; return 1; }
  fi

  # No --update-env on these restarts. It would merge THIS process's
  # environment into the target app's stored definition -- and under PM2 that
  # environment carries the deploy poller's own config keys (cron_restart & co,
  # scrubbed at the top but a future edit could reintroduce one) plus
  # deploy-only values like GITHUB_TOKEN. The apps' env is registered once from
  # ecosystem.config.js; a plain restart preserves it (2026-08-05 incident).
  if [ "${py}" = "1" ]; then
    log "pm2 restart moss-ao-api"
    "${PM2_BIN}" restart moss-ao-api >/dev/null \
      || { log "ERROR pm2 restart moss-ao-api failed"; return 1; }
  fi
  if [ "${web}" = "1" ]; then
    promote_web_build || return 1
    log "pm2 restart moss-ao-web"
    "${PM2_BIN}" restart moss-ao-web >/dev/null \
      || { log "ERROR pm2 restart moss-ao-web failed"; return 1; }
  fi
  # The scheduler processes (signals/trends/debate/backlog/health) are launched
  # fresh from .venv/bin/python on every cron tick, so they pick up new code
  # without a restart -- restarting them would only kill work in flight.
}

health_ok() {
  local i=0
  while [ "${i}" -lt "${DEPLOY_HEALTH_RETRIES}" ]; do
    local api_ok=1 web_ok=1
    # /ready, not /health: liveness stayed 200 through the 2026-07 incident
    # while every DB-backed endpoint returned 500, so a deploy that broke the
    # database would still have been recorded as DEPLOYED. /ready reads a real
    # table and answers 503 when it cannot.
    if [ "${ROLLING_BACK:-0}" = "1" ]; then
      # Rolling back: the target commit may predate /ready, and a 404 there
      # would report a perfectly good rollback as CRITICAL. Accept either.
      curl -fsS -m 5 "${DEPLOY_API_URL}/ready" >/dev/null 2>&1 \
        || curl -fsS -m 5 "${DEPLOY_API_URL}/health" >/dev/null 2>&1 \
        || api_ok=0
    elif [ "${PY_CHANGED}" = "1" ]; then
      curl -fsS -m 5 "${DEPLOY_API_URL}/ready" >/dev/null 2>&1 || api_ok=0
    fi
    if [ "${WEB_CHANGED}" = "1" ] || [ "${ROLLING_BACK:-0}" = "1" ]; then
      curl -fsS -m 8 -o /dev/null "${DEPLOY_WEB_URL}/" 2>/dev/null || web_ok=0
    fi
    if [ "${api_ok}" = "1" ] && [ "${web_ok}" = "1" ]; then
      return 0
    fi
    i=$((i + 1))
    sleep "${DEPLOY_HEALTH_INTERVAL}"
  done
  return 1
}

# Roll back to the last KNOWN-GOOD deploy (the state file), not merely to the
# pre-tick HEAD: after a crashed deploy HEAD may already sit at the broken
# target, and "rolling back" to it would change nothing.
rollback() {
  ROLLING_BACK=1
  log "ROLLBACK -> ${DEPLOYED:0:8}"
  git reset --hard --quiet "${DEPLOYED}"
  if build_and_restart "${PY_CHANGED}" "${WEB_CHANGED}" "${DEPS_CHANGED}" "${NODE_DEPS_CHANGED}"; then
    if health_ok; then
      log "rollback healthy at ${DEPLOYED:0:8}"
      alert "MOSS.AO deploy of ${TARGET:0:8} failed; rolled back to ${DEPLOYED:0:8} (healthy)"
      return 0
    fi
  fi
  log "CRITICAL rollback did not come back healthy -- manual intervention needed"
  alert "MOSS.AO CRITICAL: deploy of ${TARGET:0:8} failed AND rollback to ${DEPLOYED:0:8} is unhealthy"
  return 1
}

# Persist TARGET as the last successful deploy and clear the failure journal.
# Called only once everything (or the docs-only sync) has fully succeeded --
# this write is what makes a deploy "done" as far as later ticks are concerned.
record_success() {
  printf '%s\n' "${TARGET}" >"${DEPLOY_STATE_FILE}" || {
    log "ERROR cannot write ${DEPLOY_STATE_FILE} -- next tick will re-run this deploy"
    return 1
  }
  rm -f "${DEPLOY_ATTEMPT_FILE}" 2>/dev/null || true
}

# Any CI verdict that defers is transient by design; one that never clears
# means auto-deploy has silently stopped. Upstream counted only the
# undeterminable case; this counts every deferring verdict through the same
# per-target streak file so there is one mechanism and one knob.
note_stalled_ci() {
  local message="$1" reason="$2" streak
  streak=$(ci_unknown_streak "${TARGET}")
  log "${message} (${streak} in a row)"
  if [ "${streak}" -ge "${DEPLOY_CI_UNKNOWN_ALERT}" ] \
     && [ $(( streak % DEPLOY_CI_UNKNOWN_ALERT )) -eq 0 ]; then
    log "ERROR CI has been undeployable for ${streak} consecutive ticks (${reason}) -- deploys are stalled"
    alert "MOSS.AO deploys stalled: ${reason} for ${streak} consecutive ticks on ${TARGET:0:8}"
  fi
}

clear_ci_streak() {
  rm -f "${DEPLOY_CI_UNKNOWN_FILE}" 2>/dev/null || true
}

ecosystem_reminder() {
  [ -s "${ECOSYSTEM_PENDING}" ] || return 0
  local n
  n=$(wc -l <"${ECOSYSTEM_PENDING}" 2>/dev/null | tr -d ' ' || echo '?')
  log "REMINDER ecosystem.config.js changed in ${n} deploy(s) and PM2 has not been"
  log "         re-registered; process definitions (cron, env) are still the old ones."
  log "         From a LOGIN SHELL only -- never from inside a PM2-managed process,"
  log "         which injects config keys like cron_restart that --update-env would"
  log "         copy onto every app (see docs/deployment.md):"
  log "           pm2 restart ecosystem.config.js --update-env && pm2 save"
  log "           rm ${ECOSYSTEM_PENDING}"
}

main() {
  SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
  cd "${REPO_ROOT}"

  DEPLOY_BRANCH=${DEPLOY_BRANCH:-main}
  DEPLOY_REMOTE=${DEPLOY_REMOTE:-origin}
  DEPLOY_REQUIRE_CI=${DEPLOY_REQUIRE_CI:-1}
# Comma-separated GitHub check-run names that must have passed, e.g.
# "test (3.12),test (3.13),lint,website". Empty = accept whatever reported.
DEPLOY_REQUIRE_CI_JOBS=${DEPLOY_REQUIRE_CI_JOBS:-}
# Outstanding ecosystem.config.js changes that still need a manual PM2
# re-register. Cleared by the operator once done.
ECOSYSTEM_PENDING=${ECOSYSTEM_PENDING:-${REPO_ROOT}/logs/.ecosystem-pending}
  DEPLOY_GITHUB_REPO=${DEPLOY_GITHUB_REPO:-MosslandOpenDevs/agentic-orchestrator}
  DEPLOY_API_URL=${DEPLOY_API_URL:-http://127.0.0.1:3001}
  DEPLOY_WEB_URL=${DEPLOY_WEB_URL:-http://127.0.0.1:3000}
  DEPLOY_HEALTH_RETRIES=${DEPLOY_HEALTH_RETRIES:-20}
  DEPLOY_HEALTH_INTERVAL=${DEPLOY_HEALTH_INTERVAL:-3}
  DEPLOY_ALERT_WEBHOOK=${DEPLOY_ALERT_WEBHOOK:-}
  DEPLOY_VERBOSE=${DEPLOY_VERBOSE:-0}
  DEPLOY_LOG=${DEPLOY_LOG:-${REPO_ROOT}/logs/deploy.log}
  DEPLOY_LOCK=${DEPLOY_LOCK:-${REPO_ROOT}/logs/.deploy.lock}
  DEPLOY_LOCK_STALE_MIN=${DEPLOY_LOCK_STALE_MIN:-90}

  # Deploy state lives inside the git dir -- the one place in the checkout
  # that `git reset --hard` can never touch and no build ever writes to.
  GIT_DIR_ABS=$(git rev-parse --absolute-git-dir 2>/dev/null || echo "${REPO_ROOT}/.git")
  DEPLOY_STATE_FILE=${DEPLOY_STATE_FILE:-${GIT_DIR_ABS}/moss-ao-deployed-sha}
  DEPLOY_ATTEMPT_FILE=${DEPLOY_ATTEMPT_FILE:-${GIT_DIR_ABS}/moss-ao-deploy-attempt}
  DEPLOY_RETRY_BASE_MIN=${DEPLOY_RETRY_BASE_MIN:-5}
  DEPLOY_RETRY_MAX_MIN=${DEPLOY_RETRY_MAX_MIN:-60}
  DEPLOY_CI_UNKNOWN_FILE=${DEPLOY_CI_UNKNOWN_FILE:-${GIT_DIR_ABS}/moss-ao-deploy-ci-unknown}
  # Consecutive undeterminable-CI ticks before this stops being treated as
  # noise. 3 ticks x 5 min = ~15 minutes of total deploy paralysis, which is
  # long enough to rule out a blip and short enough to matter.
  DEPLOY_CI_UNKNOWN_ALERT=${DEPLOY_CI_UNKNOWN_ALERT:-3}

  # The PM2 poller inherits GITHUB_TOKEN because ecosystem.config.js loads
  # .env; a manual `bash scripts/deploy.sh` over SSH does not. Without it the
  # CI query goes out anonymous and the server's shared IP is rate-limited
  # (403) -- which used to surface only as "status unavailable", so a manual
  # deploy simply never happened and never said why. Fill it in from .env
  # rather than requiring every operator to remember `set -a; . ./.env`.
  if [ -z "${GITHUB_TOKEN:-}" ] && [ -r "${REPO_ROOT}/.env" ]; then
    GITHUB_TOKEN=$(env_value_from_file "${REPO_ROOT}/.env" GITHUB_TOKEN)
    if [ -n "${GITHUB_TOKEN}" ]; then
      export GITHUB_TOKEN
    else
      unset GITHUB_TOKEN
    fi
  fi

  PYTHON_BIN=${PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python}
  PM2_BIN=${PM2_BIN:-pm2}
  NPM_BIN=${NPM_BIN:-npm}
  UV_BIN=${UV_BIN:-$(command -v uv 2>/dev/null || echo "${HOME}/.local/bin/uv")}

  FORCE=0
  CHECK_ONLY=0

  while [ $# -gt 0 ]; do
    case "$1" in
      --force) FORCE=1 ;;
      --check) CHECK_ONLY=1 ;;
      -h|--help) sed -n '2,65p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
      *) echo "unknown option: $1" >&2; exit 64 ;;
    esac
    shift
  done

  acquire_lock || exit 0
  trap 'rm -rf "${DEPLOY_LOCK}" 2>/dev/null || true' EXIT

  # -------------------------------------------------------------------------
  # 1. Is there anything to deploy?
  # -------------------------------------------------------------------------
  git fetch --quiet "${DEPLOY_REMOTE}" "${DEPLOY_BRANCH}" || {
    log "WARN git fetch failed -- will retry next tick"
    exit 0
  }

  CURRENT=$(git rev-parse HEAD)
  TARGET=$(git rev-parse "${DEPLOY_REMOTE}/${DEPLOY_BRANCH}")

  # Last-success baseline (see the header). A missing/invalid state file
  # (first run, manual surgery) falls back to HEAD -- and that fallback is
  # persisted BEFORE anything can move HEAD: were "reset succeeded, build
  # failed, poller died" to happen now, the next tick's fallback would
  # otherwise be the already-advanced HEAD and the failed deploy would never
  # be retried, which is the exact hole the state file closes.
  DEPLOYED=$(cat "${DEPLOY_STATE_FILE}" 2>/dev/null || true)
  if [ -z "${DEPLOYED}" ] || ! git cat-file -e "${DEPLOYED}^{commit}" 2>/dev/null; then
    if [ -n "${DEPLOYED}" ]; then
      log "WARN state file SHA (${DEPLOYED}) is not a commit here -- assuming HEAD was deployed"
    fi
    DEPLOYED=${CURRENT}
    printf '%s\n' "${DEPLOYED}" >"${DEPLOY_STATE_FILE}" || {
      log "ERROR cannot write ${DEPLOY_STATE_FILE} -- refusing to run without retry protection"
      exit 1
    }
  fi

  if [ "${DEPLOYED}" = "${TARGET}" ] && [ "${CURRENT}" = "${TARGET}" ]; then
    ecosystem_reminder
    if [ "${DEPLOY_VERBOSE}" = "1" ] || [ "${CHECK_ONLY}" = "1" ]; then
      log "up to date at ${TARGET:0:8}"
    fi
    exit 0
  fi

  SUBJECT=$(git log -1 --format='%s' "${TARGET}")
  if [ "${CURRENT}" = "${TARGET}" ]; then
    log "incomplete deploy detected: HEAD is ${TARGET:0:8} but last success is ${DEPLOYED:0:8} -- retrying"
  else
    log "update available: ${DEPLOYED:0:8} -> ${TARGET:0:8} (${SUBJECT})"
  fi

  # Union of both diffs: DEPLOYED..TARGET carries the work a crashed deploy
  # never finished (HEAD may already equal TARGET), CURRENT..TARGET carries
  # anything a hand-moved HEAD would otherwise hide.
  CHANGED=$(
    {
      git diff --name-only "${DEPLOYED}" "${TARGET}"
      git diff --name-only "${CURRENT}" "${TARGET}"
    } | sort -u
  )

  # -------------------------------------------------------------------------
  # Failure backoff. Re-deploying a SHA that just failed -- full cycle:
  # forced DB snapshot, build, double restart, rollback, webhook -- every
  # 5-minute tick helps nobody. Attempts are journaled per target SHA (below,
  # before any work starts); after n failed attempts the next try waits
  # DEPLOY_RETRY_BASE_MIN * 2^(n-1) minutes, capped at DEPLOY_RETRY_MAX_MIN.
  # A new commit on the remote resets the journal at once; --force ignores
  # the wait entirely.
  # -------------------------------------------------------------------------
  ATTEMPT_SHA=""
  ATTEMPT_COUNT=0
  if [ -f "${DEPLOY_ATTEMPT_FILE}" ]; then
    read -r ATTEMPT_SHA ATTEMPT_COUNT <"${DEPLOY_ATTEMPT_FILE}" 2>/dev/null || true
    if [ "${ATTEMPT_SHA:-}" != "${TARGET}" ]; then
      ATTEMPT_COUNT=0
    fi
    case "${ATTEMPT_COUNT:-}" in *[!0-9]*|'') ATTEMPT_COUNT=0 ;; esac
  fi
  if [ "${ATTEMPT_COUNT}" -gt 0 ] && [ "${FORCE}" = "0" ] && [ "${CHECK_ONLY}" = "0" ]; then
    BACKOFF_EXP=$((ATTEMPT_COUNT - 1))
    if [ "${BACKOFF_EXP}" -gt 10 ]; then BACKOFF_EXP=10; fi
    BACKOFF_MIN=$((DEPLOY_RETRY_BASE_MIN * (1 << BACKOFF_EXP)))
    if [ "${BACKOFF_MIN}" -gt "${DEPLOY_RETRY_MAX_MIN}" ]; then BACKOFF_MIN=${DEPLOY_RETRY_MAX_MIN}; fi
    if [ -z "$(find "${DEPLOY_ATTEMPT_FILE}" -mmin "+${BACKOFF_MIN}" 2>/dev/null)" ]; then
      log "deploy of ${TARGET:0:8} already failed ${ATTEMPT_COUNT} time(s) -- backing off (retry ${BACKOFF_MIN}m after the last attempt)"
      exit 0
    fi
    log "retrying ${TARGET:0:8} after ${ATTEMPT_COUNT} failed attempt(s)"
  fi

  # -------------------------------------------------------------------------
  # 2. Guards
  # -------------------------------------------------------------------------
  BRANCH_NOW=$(git rev-parse --abbrev-ref HEAD)
  if [ "${BRANCH_NOW}" != "${DEPLOY_BRANCH}" ] && [ "${FORCE}" = "0" ]; then
    log "ABORT checkout is on '${BRANCH_NOW}', not '${DEPLOY_BRANCH}' -- not touching it"
    exit 0
  fi

  # Tracked-file edits made by hand on the server would be silently discarded by
  # the reset below, so stop and let a human look. Untracked files (.env, the DB)
  # are never at risk and are deliberately not checked.
  if [ -n "$(git status --porcelain --untracked-files=no)" ] && [ "${FORCE}" = "0" ]; then
    log "ABORT working tree has local modifications to tracked files:"
    git status --short --untracked-files=no | while read -r l; do log "       ${l}"; done
    log "       resolve on the server, or re-run with --force to discard them"
    alert "MOSS.AO deploy blocked: local modifications on the server checkout"
    exit 0
  fi

  # Commits made by hand on the server -- HEAD ahead of, or diverged from,
  # the remote branch -- would be thrown away by the reset below. Unlike
  # dirty tracked files they do survive in the reflog, but discarding them
  # silently is still wrong: stop and let a human reconcile.
  if [ "${CURRENT}" != "${TARGET}" ] && [ "${FORCE}" = "0" ] \
     && ! git merge-base --is-ancestor "${CURRENT}" "${TARGET}" 2>/dev/null; then
    log "ABORT HEAD ${CURRENT:0:8} carries local commits not on ${DEPLOY_REMOTE}/${DEPLOY_BRANCH}:"
    git log --oneline "${TARGET}..${CURRENT}" 2>/dev/null | head -10 \
      | while read -r l; do log "       ${l}"; done
    log "       push or drop them on the server, or re-run with --force to discard them"
    alert "MOSS.AO deploy blocked: local commits on the server checkout"
    exit 0
  fi

  if [ "${DEPLOY_REQUIRE_CI}" = "1" ] && [ "${FORCE}" = "0" ]; then
    CI=$(ci_conclusion "${TARGET}")
    case "${CI}" in
      success)    log "CI: green"; clear_ci_streak ;;
      pending)    note_stalled_ci "CI: still running -- deferring to next tick" \
                    "CI still running"; exit 0 ;;
      none)       note_stalled_ci \
                    "CI: no checks reported yet for ${TARGET:0:8} -- deferring to next tick" \
                    "no checks reported"; exit 0 ;;
      incomplete) note_stalled_ci \
                    "CI: checks reported but none verified the commit (skipped/stale) \
-- deferring to next tick" "checks verified nothing"; exit 0 ;;
      missing-required)
                  log "CI: required jobs (${DEPLOY_REQUIRE_CI_JOBS}) did not pass -- refusing"
                  clear_ci_streak
                  alert "MOSS.AO deploy skipped: required CI jobs missing on ${TARGET:0:8}"
                  exit 0 ;;
      failure)    log "CI: FAILED -- refusing to deploy ${TARGET:0:8}"
                  clear_ci_streak
                  alert "MOSS.AO deploy skipped: CI failed on ${TARGET:0:8} (${SUBJECT})"
                  exit 0 ;;
      unauthorized)
                  log "ERROR CI: GitHub rejected the status query (401/403). DEPLOYS ARE BLOCKED."
                  log "       GITHUB_TOKEN is missing, expired, or the anonymous rate limit was hit."
                  log "       This does not clear by itself -- fix the token in .env and restart"
                  log "       moss-ao-deploy, or set DEPLOY_REQUIRE_CI=0 to deploy without the gate."
                  alert "MOSS.AO deploys BLOCKED: GitHub CI status query unauthorized (401/403) on ${TARGET:0:8} -- GITHUB_TOKEN missing/expired or rate-limited"
                  exit 0 ;;
      *)          note_stalled_ci \
                    "CI: status unavailable (network/API) -- deferring to next tick" \
                    "CI status unavailable"; exit 0 ;;
    esac
  fi

  # What kind of change is this?
  PY_CHANGED=0
  WEB_CHANGED=0
  DEPS_CHANGED=0
  NODE_DEPS_CHANGED=0
  ECOSYSTEM_CHANGED=0
  while IFS= read -r f; do
    [ -n "${f}" ] || continue
    case "${f}" in
      src/*|config.yaml|pyproject.toml|uv.lock|prompts/*) PY_CHANGED=1 ;;
    esac
    case "${f}" in
      website/*) WEB_CHANGED=1 ;;
    esac
    case "${f}" in
      pyproject.toml|uv.lock) DEPS_CHANGED=1 ;;
      website/package.json|website/package-lock.json) NODE_DEPS_CHANGED=1 ;;
      ecosystem.config.js) ECOSYSTEM_CHANGED=1 ;;
    esac
  done <<EOF
${CHANGED}
EOF

  if [ "${PY_CHANGED}" = "1" ] && [ "${FORCE}" = "0" ]; then
    BUSY=$(scheduler_busy)
    if [ -n "${BUSY}" ]; then
      log "scheduler busy (${BUSY}) -- deferring back-end deploy to next tick"
      exit 0
    fi
  fi

  # Don't deploy into an environment that is already failing readiness.
  #
  # The post-deploy check gates on /ready, which reads the database. With the
  # database down a deploy cannot pass that check however good the code is: it
  # would restart the API, fail, roll back, and repeat five minutes later --
  # restart churn every tick for the length of an unrelated outage. Three
  # states, three answers: ready -> deploy; up but not ready -> the database is
  # the problem, a deploy can neither be verified nor help, so defer; API down
  # entirely -> deploying may be the fix, so proceed.
  if [ "${PY_CHANGED}" = "1" ] && [ "${FORCE}" = "0" ]; then
    if ! curl -fsS -m 5 "${DEPLOY_API_URL}/ready" >/dev/null 2>&1 \
       && curl -fsS -m 5 "${DEPLOY_API_URL}/health" >/dev/null 2>&1; then
      log "API is up but not ready (database unhealthy) -- deferring: a deploy \
could not be verified and would restart-and-roll-back every tick"
      alert "MOSS.AO deploy deferred: API not ready (database unhealthy)"
      exit 0
    fi
  fi

  if [ "${CHECK_ONLY}" = "1" ]; then
    log "--check: would deploy ${TARGET:0:8} (python=${PY_CHANGED} web=${WEB_CHANGED} \
pydeps=${DEPS_CHANGED} nodedeps=${NODE_DEPS_CHANGED} ecosystem=${ECOSYSTEM_CHANGED})"
    exit 0
  fi

  # -------------------------------------------------------------------------
  # 3. Deploy
  # -------------------------------------------------------------------------

  # Journal this attempt BEFORE any work starts: a poller SIGKILLed mid-build
  # never reaches a failure handler, and the next tick must still know this
  # SHA was already tried so the backoff above can kick in.
  printf '%s %s\n' "${TARGET}" "$((ATTEMPT_COUNT + 1))" >"${DEPLOY_ATTEMPT_FILE}" \
    || log "WARN cannot write ${DEPLOY_ATTEMPT_FILE} -- failure backoff disabled"

  # Pre-deploy snapshot: forced (not the ~daily "maybe" variant the health check
  # uses) so there is always a restore point from immediately before this change.
  # Docs-only syncs skip it: nothing restarts and reset --hard cannot touch the
  # untracked DB, so a snapshot protects nothing -- and each one rotates the
  # 7-slot backup window, so a burst of docs merges would churn days of restore
  # points into minutes.
  if [ "${PY_CHANGED}" = "1" ] || [ "${WEB_CHANGED}" = "1" ]; then
    if [ -x "${PYTHON_BIN}" ]; then
      # Exit codes are the contract with backup-db: 0 written, 2 nothing worth
      # snapshotting (no/empty/dataless DB -- benign), anything else a real
      # failure, including a corrupt source. Deploying after a failed snapshot
      # is the 2026-07 outage with no way back, so it refuses.
      SNAP_RC=0
      PYTHONPATH=./src "${PYTHON_BIN}" -m agentic_orchestrator.scheduler backup-db \
        >/dev/null 2>&1 || SNAP_RC=$?
      if [ "${SNAP_RC}" = "0" ]; then
        log "pre-deploy DB snapshot written to data/backup/"
      elif [ "${SNAP_RC}" = "2" ]; then
        log "pre-deploy DB snapshot: nothing to snapshot yet -- continuing"
      else
        log "ERROR pre-deploy DB snapshot failed (rc=${SNAP_RC}) -- refusing to \
deploy without a restore point"
        alert "MOSS.AO deploy skipped: pre-deploy DB snapshot failed on ${TARGET:0:8}"
        return 1
      fi
    else
      log "ERROR ${PYTHON_BIN} not found -- refusing to deploy without a DB snapshot"
      alert "MOSS.AO deploy skipped: ${PYTHON_BIN} missing, no DB snapshot possible"
      return 1
    fi
  else
    log "docs-only sync -- skipping DB snapshot (nothing restarts)"
  fi

  log "checking out ${TARGET:0:8}"
  git reset --hard --quiet "${TARGET}"

  if [ "${ECOSYSTEM_CHANGED}" = "1" ]; then
    # Record the debt rather than only announcing it once: the deploy state
    # advances either way and later ticks are no-ops, so a single log line was
    # the whole notification -- a cron or env change could sit unapplied
    # indefinitely with nothing left pointing at it. Guarded like log(), since
    # aborting here would leave the checkout moved but nothing rebuilt.
    printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${TARGET}" \
      >>"${ECOSYSTEM_PENDING}" 2>/dev/null \
      || log "WARN could not record the pending ecosystem change in ${ECOSYSTEM_PENDING}"
    alert "MOSS.AO: ecosystem.config.js changed in ${TARGET:0:8} -- PM2 needs a manual re-register"
  fi

  # Docs-only changes are synced (checkout updated above) but not deployed:
  # nothing to build or restart, and the log says SYNCED rather than DEPLOYED.
  if [ "${PY_CHANGED}" = "0" ] && [ "${WEB_CHANGED}" = "0" ]; then
    record_success || exit 1
    log "SYNCED ${DEPLOYED:0:8} -> ${TARGET:0:8} (docs only -- no deploy)"
    ecosystem_reminder
    exit 0
  fi

  if ! build_and_restart "${PY_CHANGED}" "${WEB_CHANGED}" "${DEPS_CHANGED}" "${NODE_DEPS_CHANGED}"; then
    log "ERROR build/restart failed"
    rollback || exit 1
    exit 1
  fi

  if ! health_ok; then
    log "ERROR health check failed after deploy"
    rollback || exit 1
    exit 1
  fi

  record_success || exit 1
  log "DEPLOYED ${DEPLOYED:0:8} -> ${TARGET:0:8}"
  ecosystem_reminder
  git log --oneline "${DEPLOYED}..${TARGET}" | head -10 | while read -r l; do log "       ${l}"; done
  exit 0
}

main "$@"
exit $?
