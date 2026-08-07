#!/usr/bin/env bash
#
# Fetch both probes' CSVs to this machine and print the joined report.
#
# The two halves of the measurement live on different hosts on purpose (see
# probe_uptime.py), and the office VM cannot be relied on to push its half --
# it is the side that goes offline. So the report is pulled, from a laptop that
# can reach both.
#
#   scripts/monitor/pull-report.sh              # whole history
#   scripts/monitor/pull-report.sh --since 2026-08-01
#
set -euo pipefail

UPTIME_HOST="${AO_MONITOR_UPTIME_HOST:-mossland}"
NETPATH_HOST="${AO_MONITOR_NETPATH_HOST:-atrn@100.109.139.25}"
SSH_KEY="${AO_MONITOR_SSH_KEY:-$HOME/.ssh/mossland_ed25519}"
WORK="${AO_MONITOR_WORKDIR:-$HOME/.ao-monitor-report}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$WORK/uptime" "$WORK/netpath"

echo "· fetching uptime samples from $UPTIME_HOST" >&2
scp -q -o BatchMode=yes -i "$SSH_KEY" \
    "$UPTIME_HOST:ao-monitor/data/uptime-*.csv" "$WORK/uptime/" 2>/dev/null \
    || echo "  (none yet)" >&2

echo "· fetching network-path samples from $NETPATH_HOST" >&2
scp -q -o BatchMode=yes -i "$SSH_KEY" \
    "$NETPATH_HOST:ao-monitor/data/netpath-*.csv" "$WORK/netpath/" 2>/dev/null \
    || echo "  (none yet -- office VM may be offline; report will say 불명)" >&2

echo >&2
exec python3 "$HERE/report.py" \
    --uptime "$WORK/uptime" \
    --netpath "$WORK/netpath" \
    "$@"
