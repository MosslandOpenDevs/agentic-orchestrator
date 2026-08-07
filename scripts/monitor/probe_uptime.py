#!/usr/bin/env python3
"""Outside-in availability probe for the AO app server.

The app server is an office VM reachable only over the tailnet;
nginx on Lightsail proxies ao.moss.land to it. When the office line drops both
upstream ports die at once and every request 504s -- but nothing on the failing
side can report that, and nothing outside was watching. The 2026-08-04 and
2026-08-06 outages (~16 minutes each) were only reconstructed after the fact
from nginx error logs, which logrotate discards after two weeks.

This probe runs on Lightsail -- deliberately OUTSIDE the office network, on the
very host nginx runs on -- so it measures what a visitor actually experiences
and keeps recording while the office line is down.

Every sample lands in a monthly CSV. Discord is notified only on a state
CHANGE, so a healthy month is silent. One dropped sample never alerts: DOWN is
declared after ``FAIL_THRESHOLD`` consecutive failures and UP after
``OK_THRESHOLD`` consecutive successes, which keeps single-packet loss out of
the record while still catching a real outage inside a minute.

Cause attribution is deliberately NOT done here -- from outside every failure
looks identical. ``probe_netpath.py`` runs on the office box for that, and
``report.py`` joins the two.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import json
import socket
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

# The probe target (the app server's tailnet address) is deliberately NOT
# hardcoded: this repo is public and real addresses live in CLAUDE.local.md
# and each box's config.env. The script refuses to run without it rather than
# guessing.
DEFAULT_TIMEOUT = 5.0

# A real outage is minutes long; a lost packet is one sample. Requiring two
# consecutive agreeing samples costs at most one probe interval of detection
# latency and removes essentially all single-sample noise from the record.
FAIL_THRESHOLD = 2
OK_THRESHOLD = 2

KST = ZoneInfo("Asia/Seoul")
CSV_HEADER = ["ts", "ok", "code", "ms"]

COLOR_DOWN = 0xE03131
COLOR_UP = 0x2F9E44
COLOR_INFO = 0x4C6EF5

# Discord sits behind Cloudflare, which rejects the default Python-urllib
# User-Agent outright: HTTP 403, body "error code: 1010". Measured on the
# Lightsail host 2026-08-07 -- byte-identical request, default UA -> 403, this
# UA -> 204. curl succeeded throughout, which is why the webhook looked fine
# while every alert this script sent would have been dropped.
USER_AGENT = "MOSS-AO-Monitor/1.0 (+https://ao.moss.land)"


# --------------------------------------------------------------------------
# config


def load_config(path: Path) -> dict:
    """Read a shell-style KEY=VALUE file.

    The webhook URL is a secret, so it lives in a file the operator writes by
    hand rather than in the repo or in the crontab line.
    """
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


# --------------------------------------------------------------------------
# state


@dataclass
class ProbeState:
    """Declared state plus the streak that would flip it."""

    state: str = "unknown"  # unknown | up | down
    pending: str = ""  # state the current streak is counting toward
    streak: int = 0
    pending_since: str = ""  # ts of the sample that opened the streak
    down_since: str = ""  # ts of the first failed sample of the open outage
    outages: int = 0

    @classmethod
    def load(cls, path: Path) -> "ProbeState":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # A truncated state file must not wedge the probe; the worst case
            # is one spurious transition notification.
            return cls()
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path: Path) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(path)


@dataclass
class Sample:
    ts: datetime
    ok: bool
    code: str
    ms: int


# --------------------------------------------------------------------------
# probing


def probe(target: str, timeout: float) -> Sample:
    """One HTTP probe. Any failure at all counts as down -- from outside, a
    connect timeout and a 500 are the same thing to a visitor."""
    started = time.monotonic()
    code = "000"
    ok = False
    try:
        req = urllib.request.Request(target, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = str(resp.status)
            resp.read(2048)
            ok = 200 <= resp.status < 300
    except urllib.error.HTTPError as exc:
        code = str(exc.code)
    except (urllib.error.URLError, socket.timeout, OSError):
        code = "000"
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return Sample(datetime.now(timezone.utc), ok, code, elapsed_ms)


def append_sample(data_dir: Path, sample: Sample) -> None:
    path = data_dir / f"uptime-{sample.ts:%Y-%m}.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new:
            writer.writerow(CSV_HEADER)
        writer.writerow(
            [sample.ts.strftime("%Y-%m-%dT%H:%M:%SZ"), int(sample.ok), sample.code, sample.ms]
        )


# --------------------------------------------------------------------------
# notification


def notify_discord(webhook: str, title: str, description: str, color: int,
                   fields: Optional[list] = None,
                   log_path: Optional[Path] = None) -> bool:
    """Post one embed. Never raises -- alerting must not stop the recording,
    since the samples are the part that cannot be reconstructed later.

    A swallowed failure is still written to ``log_path``. An alert channel that
    fails quietly is indistinguishable from a month with no incidents, which is
    the exact failure this whole monitor exists to end; the log is what makes
    "no alerts" checkable.
    """
    if not webhook:
        return False
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if fields:
        embed["fields"] = fields
    payload = json.dumps({"embeds": [embed]}).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if 200 <= resp.status < 300:
                return True
        reason = f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read()[:120].decode("utf-8", "replace").strip()
        except Exception:  # noqa: BLE001
            pass
        reason = f"HTTP {exc.code} {body}"
    except Exception as exc:  # noqa: BLE001 - see docstring
        reason = f"{type(exc).__name__}: {exc}"

    if log_path is not None:
        try:
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(f"{stamp}\t{title}\t{reason}\n")
        except OSError:
            pass
    return False


def _kst(ts: str) -> str:
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def _human_duration(seconds: float) -> str:
    total = int(seconds)
    if total < 60:
        return f"{total}초"
    minutes, secs = divmod(total, 60)
    if minutes < 60:
        return f"{minutes}분 {secs}초"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}시간 {minutes}분"


# --------------------------------------------------------------------------
# state machine


def apply_sample(state: ProbeState, sample: Sample, target: str, webhook: str,
                 log_path: Optional[Path] = None) -> None:
    observed = "up" if sample.ok else "down"
    ts = sample.ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    if observed == state.state:
        state.pending, state.streak, state.pending_since = "", 0, ""
        return

    if state.pending == observed:
        state.streak += 1
    else:
        state.pending, state.streak, state.pending_since = observed, 1, ts

    threshold = FAIL_THRESHOLD if observed == "down" else OK_THRESHOLD
    if state.streak < threshold:
        return

    previous = state.state
    state.state = observed

    if observed == "down":
        state.down_since = state.pending_since or ts
        state.outages += 1
        notify_discord(
            webhook,
            "🔴 AO 앱 서버 DOWN",
            f"`{target}` 에 연속 {threshold}회 도달 실패",
            COLOR_DOWN,
            [
                {"name": "최초 실패", "value": _kst(state.down_since), "inline": True},
                {"name": "응답", "value": f"`{sample.code}`", "inline": True},
            ],
            log_path=log_path,
        )
    else:
        recovered_at = state.pending_since or ts
        # A first-ever run that starts healthy is a baseline, not a recovery.
        if previous == "down" and state.down_since:
            down = datetime.strptime(state.down_since, "%Y-%m-%dT%H:%M:%SZ")
            up = datetime.strptime(recovered_at, "%Y-%m-%dT%H:%M:%SZ")
            notify_discord(
                webhook,
                "🟢 AO 앱 서버 복구",
                f"`{target}` 정상 응답",
                COLOR_UP,
                [
                    {"name": "다운 구간", "value": _kst(state.down_since), "inline": False},
                    {
                        "name": "지속 시간",
                        "value": _human_duration((up - down).total_seconds()),
                        "inline": True,
                    },
                    {"name": "복구", "value": _kst(recovered_at), "inline": True},
                ],
                log_path=log_path,
            )
        state.down_since = ""

    state.pending, state.streak, state.pending_since = "", 0, ""


# --------------------------------------------------------------------------
# entrypoint


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=str(Path.home() / "ao-monitor"),
                        help="working directory (config.env, data/, probe.lock)")
    parser.add_argument("--samples", type=int, default=2,
                        help="samples per invocation (cron fires once a minute)")
    parser.add_argument("--interval", type=float, default=30.0,
                        help="seconds between samples within one invocation")
    parser.add_argument("--test-notify", action="store_true",
                        help="post a test embed to Discord and exit")
    args = parser.parse_args(argv)

    base = Path(args.dir).expanduser()
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_config(base / "config.env")
    target = cfg.get("AO_MONITOR_TARGET", "")
    if not target:
        print("AO_MONITOR_TARGET is not set in config.env "
              "(real addresses live in CLAUDE.local.md, not in this repo)",
              file=sys.stderr)
        return 2
    timeout = float(cfg.get("AO_MONITOR_TIMEOUT", DEFAULT_TIMEOUT))
    webhook = cfg.get("AO_MONITOR_DISCORD_WEBHOOK", "")
    notify_log = data_dir / "notify.log"

    if args.test_notify:
        if not webhook:
            print("AO_MONITOR_DISCORD_WEBHOOK is not set in config.env", file=sys.stderr)
            return 2
        ok = notify_discord(
            webhook,
            "🔵 AO 모니터 테스트",
            "웹훅이 정상 연결되었습니다. 실제 알림은 상태가 바뀔 때만 옵니다.",
            COLOR_INFO,
            [{"name": "감시 대상", "value": f"`{target}`", "inline": False}],
            log_path=notify_log,
        )
        print("sent" if ok else f"FAILED -- reason logged to {notify_log}")
        return 0 if ok else 1

    # Overlapping cron invocations would interleave CSV rows and corrupt the
    # streak counter; skipping is always the right answer since the next tick
    # is a minute away.
    lock_path = base / "probe.lock"
    lock = lock_path.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0

    state_path = base / "data" / "uptime.state"
    state = ProbeState.load(state_path)

    for index in range(max(1, args.samples)):
        if index:
            time.sleep(args.interval)
        sample = probe(target, timeout)
        append_sample(data_dir, sample)
        apply_sample(state, sample, target, webhook, notify_log)

    state.save(state_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
