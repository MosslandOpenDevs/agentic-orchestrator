#!/usr/bin/env bash
#
# MOSS.AO pull-based auto-deploy.
#
# Runs ON the application server (the box PM2 lives on) and brings the checkout
# up to origin/main. Idempotent: when HEAD already equals the remote tip it does
# nothing and exits 0, so it is safe to run from PM2's cron every few minutes.
#
# Why pull-based instead of a push from CI: the app server has no public inbound
# route (it is reachable over Tailscale only), the repo is public (a self-hosted
# GitHub runner on a public repo is a known footgun), and repo-admin rights are
# needed to add runners/secrets. Fetching a public repo outbound needs none of
# that -- no deploy key, no open port, no GitHub configuration at all.
#
# Usage:
#   scripts/deploy.sh              # deploy if the remote moved (normal cron use)
#   scripts/deploy.sh --check      # report what would happen, change nothing
#   scripts/deploy.sh --force      # ignore the CI gate, busy-scheduler and
#                                  # dirty-tree guards (manual use)
#
# Configuration (env, all optional -- ecosystem.config.js loads .env first):
#   DEPLOY_BRANCH          branch to track                     (default: main)
#   DEPLOY_REMOTE          git remote                          (default: origin)
#   DEPLOY_REQUIRE_CI      1 = only deploy CI-green commits     (default: 1)
#   DEPLOY_GITHUB_REPO     owner/name used for the CI query
#   DEPLOY_API_URL         backend health URL                  (:3001)
#   DEPLOY_WEB_URL         frontend health URL                 (:3000)
#   DEPLOY_HEALTH_RETRIES  health poll attempts                (default: 20)
#   DEPLOY_HEALTH_INTERVAL seconds between attempts            (default: 3)
#   DEPLOY_ALERT_WEBHOOK   Slack/Discord webhook for failures   (default: none)
#   DEPLOY_VERBOSE         1 = also log no-op ticks            (default: 0)
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

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
cd "${REPO_ROOT}"

DEPLOY_BRANCH=${DEPLOY_BRANCH:-main}
DEPLOY_REMOTE=${DEPLOY_REMOTE:-origin}
DEPLOY_REQUIRE_CI=${DEPLOY_REQUIRE_CI:-1}
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
    -h|--help) sed -n '2,40p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 64 ;;
  esac
  shift
done

log() {
  local line
  line="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  echo "${line}"
  mkdir -p "$(dirname "${DEPLOY_LOG}")" 2>/dev/null || true
  echo "${line}" >>"${DEPLOY_LOG}" 2>/dev/null || true
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
# Single-flight lock. A crash mid-deploy would otherwise wedge every later tick,
# so a lock older than DEPLOY_LOCK_STALE_MIN is reclaimed.
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "${DEPLOY_LOCK}")"
if ! mkdir "${DEPLOY_LOCK}" 2>/dev/null; then
  if [ -n "$(find "${DEPLOY_LOCK}" -maxdepth 0 -mmin "+${DEPLOY_LOCK_STALE_MIN}" 2>/dev/null)" ]; then
    log "WARN stale lock older than ${DEPLOY_LOCK_STALE_MIN}m -- reclaiming"
    rm -rf "${DEPLOY_LOCK}"
    mkdir "${DEPLOY_LOCK}" 2>/dev/null || { log "could not reclaim lock; skipping"; exit 0; }
  else
    [ "${DEPLOY_VERBOSE}" = "1" ] && log "another deploy is running -- skipping"
    exit 0
  fi
fi
trap 'rm -rf "${DEPLOY_LOCK}" 2>/dev/null || true' EXIT

# ---------------------------------------------------------------------------
# 1. Is there anything to deploy?
# ---------------------------------------------------------------------------
git fetch --quiet "${DEPLOY_REMOTE}" "${DEPLOY_BRANCH}" || {
  log "WARN git fetch failed -- will retry next tick"
  exit 0
}

CURRENT=$(git rev-parse HEAD)
TARGET=$(git rev-parse "${DEPLOY_REMOTE}/${DEPLOY_BRANCH}")

if [ "${CURRENT}" = "${TARGET}" ]; then
  if [ "${DEPLOY_VERBOSE}" = "1" ] || [ "${CHECK_ONLY}" = "1" ]; then
    log "up to date at ${CURRENT:0:8}"
  fi
  exit 0
fi

CHANGED=$(git diff --name-only "${CURRENT}" "${TARGET}")
SUBJECT=$(git log -1 --format='%s' "${TARGET}")
log "update available: ${CURRENT:0:8} -> ${TARGET:0:8} (${SUBJECT})"

# ---------------------------------------------------------------------------
# 2. Guards
# ---------------------------------------------------------------------------
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

# CI gate: deploy only commits GitHub Actions has gone green on.
ci_conclusion() {
  local sha="$1" url auth
  url="https://api.github.com/repos/${DEPLOY_GITHUB_REPO}/commits/${sha}/check-runs"
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    auth="Authorization: Bearer ${GITHUB_TOKEN}"
  else
    auth="X-No-Auth: 1"
  fi
  curl -fsS -m 20 -H 'Accept: application/vnd.github+json' -H "${auth}" "${url}" 2>/dev/null \
    | python3 -c '
import json, sys
try:
    runs = json.load(sys.stdin).get("check_runs", [])
except Exception:
    print("unknown"); raise SystemExit
if not runs:
    print("none"); raise SystemExit
bad = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
if any(r.get("status") != "completed" for r in runs):
    print("pending")
elif any(r.get("conclusion") in bad for r in runs):
    print("failure")
else:
    print("success")
' 2>/dev/null || echo "unknown"
}

if [ "${DEPLOY_REQUIRE_CI}" = "1" ] && [ "${FORCE}" = "0" ]; then
  CI=$(ci_conclusion "${TARGET}")
  case "${CI}" in
    success) log "CI: green" ;;
    none)    log "CI: no checks reported for this commit -- proceeding" ;;
    pending) log "CI: still running -- deferring to next tick"; exit 0 ;;
    failure) log "CI: FAILED -- refusing to deploy ${TARGET:0:8}"
             alert "MOSS.AO deploy skipped: CI failed on ${TARGET:0:8} (${SUBJECT})"
             exit 0 ;;
    *)       log "CI: status unavailable (network/API) -- deferring to next tick"; exit 0 ;;
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
    src/*|config.yaml|pyproject.toml|prompts/*) PY_CHANGED=1 ;;
  esac
  case "${f}" in
    website/*) WEB_CHANGED=1 ;;
  esac
  case "${f}" in
    pyproject.toml) DEPS_CHANGED=1 ;;
    website/package.json|website/package-lock.json) NODE_DEPS_CHANGED=1 ;;
    ecosystem.config.js) ECOSYSTEM_CHANGED=1 ;;
  esac
done <<EOF
${CHANGED}
EOF

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

if [ "${PY_CHANGED}" = "1" ] && [ "${FORCE}" = "0" ]; then
  BUSY=$(scheduler_busy)
  if [ -n "${BUSY}" ]; then
    log "scheduler busy (${BUSY}) -- deferring back-end deploy to next tick"
    exit 0
  fi
fi

if [ "${CHECK_ONLY}" = "1" ]; then
  log "--check: would deploy ${TARGET:0:8} (python=${PY_CHANGED} web=${WEB_CHANGED} \
pydeps=${DEPS_CHANGED} nodedeps=${NODE_DEPS_CHANGED} ecosystem=${ECOSYSTEM_CHANGED})"
  exit 0
fi

# ---------------------------------------------------------------------------
# 3. Deploy
# ---------------------------------------------------------------------------

# Pre-deploy snapshot: forced (not the ~daily "maybe" variant the health check
# uses) so there is always a restore point from immediately before this change.
# Docs-only syncs skip it: nothing restarts and reset --hard cannot touch the
# untracked DB, so a snapshot protects nothing -- and each one rotates the
# 7-slot backup window, so a burst of docs merges would churn days of restore
# points into minutes.
if [ "${PY_CHANGED}" = "1" ] || [ "${WEB_CHANGED}" = "1" ]; then
  if [ -x "${PYTHON_BIN}" ]; then
    if PYTHONPATH=./src "${PYTHON_BIN}" -m agentic_orchestrator.scheduler backup-db >/dev/null 2>&1; then
      log "pre-deploy DB snapshot written to data/backup/"
    else
      log "WARN pre-deploy DB snapshot failed (continuing)"
    fi
  else
    log "WARN ${PYTHON_BIN} not found -- skipping DB snapshot"
  fi
else
  log "docs-only sync -- skipping DB snapshot (nothing restarts)"
fi

# uv-managed checkout? Either the lockfile is present (it is untracked on the
# server, so this is a property of the machine, not of the commit) or the venv
# itself records that uv built it.
uses_uv() {
  [ -x "${UV_BIN}" ] || return 1
  [ -f "${REPO_ROOT}/uv.lock" ] && return 0
  grep -qs '^uv = ' "${REPO_ROOT}/.venv/pyvenv.cfg"
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
      log "uv sync (pyproject.toml changed)"
      "${UV_BIN}" sync --quiet || { log "ERROR uv sync failed"; return 1; }
    else
      log "pip install -e . (pyproject.toml changed)"
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
    # rebuild -- restarting alone would serve the previous bundle.
    log "npm run build"
    (cd website && "${NPM_BIN}" run build) || { log "ERROR npm run build failed"; return 1; }
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
    if [ "${PY_CHANGED}" = "1" ] || [ "${ROLLING_BACK:-0}" = "1" ]; then
      curl -fsS -m 5 "${DEPLOY_API_URL}/health" >/dev/null 2>&1 || api_ok=0
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

rollback() {
  ROLLING_BACK=1
  log "ROLLBACK -> ${CURRENT:0:8}"
  git reset --hard --quiet "${CURRENT}"
  if build_and_restart "${PY_CHANGED}" "${WEB_CHANGED}" "${DEPS_CHANGED}" "${NODE_DEPS_CHANGED}"; then
    if health_ok; then
      log "rollback healthy at ${CURRENT:0:8}"
      alert "MOSS.AO deploy of ${TARGET:0:8} failed; rolled back to ${CURRENT:0:8} (healthy)"
      return 0
    fi
  fi
  log "CRITICAL rollback did not come back healthy -- manual intervention needed"
  alert "MOSS.AO CRITICAL: deploy of ${TARGET:0:8} failed AND rollback to ${CURRENT:0:8} is unhealthy"
  return 1
}

log "checking out ${TARGET:0:8}"
git reset --hard --quiet "${TARGET}"

if [ "${ECOSYSTEM_CHANGED}" = "1" ]; then
  log "NOTE ecosystem.config.js changed -- process definitions (cron, env) are"
  log "     NOT re-registered automatically. Run on the server when convenient:"
  log "     pm2 restart ecosystem.config.js --update-env && pm2 save"
  log "     (from a login shell only -- never from inside a PM2-managed process:"
  log "      PM2 injects config keys like cron_restart into the environment and"
  log "      --update-env would copy them onto every app; see docs/deployment.md)"
fi

# Docs-only changes are synced (checkout updated above) but not deployed:
# nothing to build or restart, and the log says SYNCED rather than DEPLOYED.
if [ "${PY_CHANGED}" = "0" ] && [ "${WEB_CHANGED}" = "0" ]; then
  log "SYNCED ${CURRENT:0:8} -> ${TARGET:0:8} (docs only -- no deploy)"
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

log "DEPLOYED ${CURRENT:0:8} -> ${TARGET:0:8}"
git log --oneline "${CURRENT}..${TARGET}" | head -10 | while read -r l; do log "       ${l}"; done
exit 0
