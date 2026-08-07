#!/usr/bin/env bash
#
# Fetch both probes' CSVs to this machine and print the joined report.
#
# The two halves of the measurement live on different hosts on purpose (see
# probe_uptime.py), and the office VM cannot be relied on to push its half --
# it is the side that goes offline. So the report is pulled, from a laptop that
# can reach both.
#
# Host addresses are deliberately not in this public repo. Put them in
# scripts/monitor/local.env (gitignored; real values in CLAUDE.local.md):
#
#   AO_MONITOR_UPTIME_HOST=<ssh host/alias of the Lightsail nginx box>
#   AO_MONITOR_NETPATH_HOST=<user@tailnet-ip of the office VM>
#   AO_MONITOR_SSH_KEY=<identity file, optional if ssh config covers it>
#
#   scripts/monitor/pull-report.sh              # whole history
#   scripts/monitor/pull-report.sh --since 2026-08-01
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
[ -f "$HERE/local.env" ] && . "$HERE/local.env"

UPTIME_HOST="${AO_MONITOR_UPTIME_HOST:-}"
NETPATH_HOST="${AO_MONITOR_NETPATH_HOST:-}"
SSH_KEY="${AO_MONITOR_SSH_KEY:-}"
WORK="${AO_MONITOR_WORKDIR:-$HOME/.ao-monitor-report}"

if [ -z "$UPTIME_HOST" ] || [ -z "$NETPATH_HOST" ]; then
    echo "AO_MONITOR_UPTIME_HOST / AO_MONITOR_NETPATH_HOST are not set." >&2
    echo "Create $HERE/local.env (gitignored) -- real values in CLAUDE.local.md." >&2
    exit 2
fi

SSH_OPTS=(-q -o BatchMode=yes)
[ -n "$SSH_KEY" ] && SSH_OPTS+=(-i "$SSH_KEY")

mkdir -p "$WORK/uptime" "$WORK/netpath"

echo "· fetching uptime samples from $UPTIME_HOST" >&2
scp "${SSH_OPTS[@]}" \
    "$UPTIME_HOST:ao-monitor/data/uptime-*.csv" "$WORK/uptime/" 2>/dev/null \
    || echo "  (none yet)" >&2

echo "· fetching network-path samples from $NETPATH_HOST" >&2
scp "${SSH_OPTS[@]}" \
    "$NETPATH_HOST:ao-monitor/data/netpath-*.csv" "$WORK/netpath/" 2>/dev/null \
    || echo "  (none yet -- office VM may be offline; report will say 불명)" >&2

echo >&2
exec python3 "$HERE/report.py" \
    --uptime "$WORK/uptime" \
    --netpath "$WORK/netpath" \
    "$@"
