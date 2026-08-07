#!/usr/bin/env python3
"""Inside-out network path probe for the AO app server's office line.

``probe_uptime.py`` answers *whether* ao.moss.land was reachable. It cannot
answer *why*: from Lightsail a dead router, a dead ISP link, a DNS failure and
a wedged tailscale all look like one 504. Only the office box can tell them
apart, because only it sits on the near side of every hop.

So this runs on the office VM and walks the path outward, one layer at a time:

    1. gw      -- the LAN default gateway (192.168.1.1). Dead means the
                  problem is the LAN, the switch, or the router itself.
    2. inet    -- 1.1.1.1 by raw IP, no name lookup. Dead while gw is alive
                  means the router is up but its WAN side (or the ISP) is not.
    3. dns     -- getaddrinfo() through systemd-resolved, the same path the
                  application uses. Dead while inet is alive isolates DNS.
    4. tspeer  -- ``tailscale ping`` to the Lightsail node, i.e. the exact
                  data path nginx traverses in reverse. Dead while dns is
                  alive means the tunnel, not the line. The reply also names
                  the route, so a silent direct -> DERP relay demotion (slower
                  but still up) shows in the record.

The 2026-08-06 outage had DNS failing (``Could not resolve host: github.com``)
*and* raw-IP connections timing out at once, which already argued for a real
path loss rather than a resolver problem -- but that was reconstructed by hand
from two unrelated logs after the fact. These columns make the same call
automatically, every 30 seconds.

Nothing here alerts. This host is on the failing side of the very link being
measured, so it cannot be trusted to deliver a message; it only has to keep
writing to local disk, which stays possible throughout an outage. ``report.py``
joins these rows to the outside probe's afterwards.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import re
import socket
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_PEER = "100.107.17.114"  # wooram-lightsail-mossland-website (the nginx host)
DEFAULT_INTERNET_IP = "1.1.1.1"
DEFAULT_DNS_NAME = "github.com"
PING_TIMEOUT_S = 2
TS_PING_TIMEOUT_S = 3

CSV_HEADER = [
    "ts",
    "gw", "gw_ms",
    "inet", "inet_ms",
    "dns", "dns_ms",
    "tspeer", "tspeer_ms", "tspeer_path",
]

_RTT_RE = re.compile(r"time=([\d.]+)\s*ms")
_TS_VIA_RE = re.compile(r"\bvia\s+(\S+)")


@dataclass
class Layer:
    ok: bool
    ms: int
    detail: str = ""


def _run(cmd: list, timeout: float) -> "tuple[int, str]":
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return 1, ""


def detect_gateway() -> str:
    _, out = _run(["ip", "route"], timeout=5)
    for line in out.splitlines():
        if line.startswith("default"):
            parts = line.split()
            if len(parts) >= 3:
                return parts[2]
    return ""


def probe_ping(host: str) -> Layer:
    """One ICMP echo. Latency comes from ping's own RTT rather than wall clock
    so that process spawn cost is not mistaken for network latency."""
    if not host:
        return Layer(False, 0, "no-target")
    started = time.monotonic()
    rc, out = _run(
        ["ping", "-n", "-c", "1", "-W", str(PING_TIMEOUT_S), host],
        timeout=PING_TIMEOUT_S + 3,
    )
    match = _RTT_RE.search(out)
    if rc == 0 and match:
        return Layer(True, int(float(match.group(1))))
    return Layer(False, int((time.monotonic() - started) * 1000))


def probe_dns(name: str) -> Layer:
    started = time.monotonic()
    try:
        socket.getaddrinfo(name, 443, socket.AF_INET)
        return Layer(True, int((time.monotonic() - started) * 1000))
    except (socket.gaierror, OSError):
        return Layer(False, int((time.monotonic() - started) * 1000))


def probe_tailscale(peer: str) -> Layer:
    """``tailscale ping`` needs no listening port on the far side and reports
    the route it took, which distinguishes a healthy direct path from a DERP
    relay fallback."""
    started = time.monotonic()
    rc, out = _run(
        ["tailscale", "ping", "-c", "1", "--timeout", f"{TS_PING_TIMEOUT_S}s", peer],
        timeout=TS_PING_TIMEOUT_S + 4,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if rc != 0 or "pong" not in out:
        return Layer(False, elapsed_ms, "derp" if "derp" in out.lower() else "")
    match = _RTT_RE.search(out) or re.search(r"in\s+(\d+)ms", out)
    ms = int(float(match.group(1))) if match else elapsed_ms
    via = _TS_VIA_RE.search(out)
    path = via.group(1) if via else ""
    if path.lower().startswith("derp"):
        path = "derp"
    elif path:
        path = "direct"
    return Layer(True, ms, path)


def sample_once(gateway: str, internet_ip: str, dns_name: str, peer: str) -> list:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    gw = probe_ping(gateway)
    inet = probe_ping(internet_ip)
    dns = probe_dns(dns_name)
    tsp = probe_tailscale(peer)
    return [
        ts,
        int(gw.ok), gw.ms,
        int(inet.ok), inet.ms,
        int(dns.ok), dns.ms,
        int(tsp.ok), tsp.ms, tsp.detail,
    ]


def append_row(data_dir: Path, row: list) -> None:
    stamp = row[0][:7]  # YYYY-MM
    path = data_dir / f"netpath-{stamp}.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)


def load_config(path: Path) -> dict:
    cfg: dict = {}
    if not path.exists():
        return cfg
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        cfg[key.strip()] = value.strip().strip("'\"")
    return cfg


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=str(Path.home() / "ao-monitor"))
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--once", action="store_true",
                        help="take a single sample and print it instead of appending")
    args = parser.parse_args(argv)

    base = Path(args.dir).expanduser()
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_config(base / "config.env")
    gateway = cfg.get("AO_MONITOR_GATEWAY") or detect_gateway()
    internet_ip = cfg.get("AO_MONITOR_INTERNET_IP", DEFAULT_INTERNET_IP)
    dns_name = cfg.get("AO_MONITOR_DNS_NAME", DEFAULT_DNS_NAME)
    peer = cfg.get("AO_MONITOR_TS_PEER", DEFAULT_PEER)

    if args.once:
        print(dict(zip(CSV_HEADER, sample_once(gateway, internet_ip, dns_name, peer))))
        return 0

    lock_path = base / "netpath.lock"
    lock = lock_path.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0

    for index in range(max(1, args.samples)):
        if index:
            time.sleep(args.interval)
        append_row(data_dir, sample_once(gateway, internet_ip, dns_name, peer))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
