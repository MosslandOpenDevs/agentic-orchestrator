#!/usr/bin/env python3
"""Join the two probes into an outage report with a cause for each outage.

``probe_uptime.py`` (Lightsail) says *when* ao.moss.land was unreachable.
``probe_netpath.py`` (office VM) says *what* was broken at that moment. Neither
is useful alone: the outside probe cannot see past "504", and the inside probe
cannot tell whether anyone was actually affected.

This joins them on time and, for every outage, walks the layers outward to the
first one that failed:

    gw down                        -> LAN / switch / router itself
    gw up,  inet down              -> router WAN or the ISP
    inet up, dns down              -> DNS resolution only
    dns up,  tailscale down        -> the tunnel, not the line
    every layer up                 -> not the network: the app or the host

That last row is the one worth stating plainly. If a future outage shows every
network layer healthy, the office line is exonerated and the bug is ours.

Single-sample failures are counted separately from confirmed outages. Mining
nginx's error log for 2026-08-04..06 turned up 19 error clusters but only 2
were real minutes-long outages; the other 17 were one or two stray errors. A
report that lumps them together turns "twice in three days" into "six times a
day" and nobody believes the numbers after that.

Usage:
    report.py --uptime ~/ao-monitor/data --netpath ./netpath-data
    report.py --uptime ./data --since 2026-08-01 --json
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# Must match probe_uptime.FAIL_THRESHOLD so the report and the alerts agree on
# what counted as an outage.
CONFIRM_SAMPLES = 2

CAUSE_LAN = "LAN/라우터"
CAUSE_ISP = "ISP/라우터 WAN"
CAUSE_DNS = "DNS"
CAUSE_TAILSCALE = "Tailscale 터널"
CAUSE_APP = "앱/서버 (네트워크 정상)"
CAUSE_UNKNOWN = "불명 (내부 프로브 데이터 없음)"


@dataclass
class UptimeSample:
    ts: datetime
    ok: bool
    code: str
    ms: int


@dataclass
class NetSample:
    ts: datetime
    gw: bool
    inet: bool
    dns: bool
    tspeer: bool
    path: str


@dataclass
class Outage:
    start: datetime  # first failing sample
    end: datetime  # first sample that recovered (or last failing + interval)
    samples: int
    codes: Counter = field(default_factory=Counter)
    cause: str = CAUSE_UNKNOWN
    layer_detail: str = ""

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


# --------------------------------------------------------------------------
# loading


def _expand(spec: str, prefix: str) -> list:
    path = Path(spec).expanduser()
    if path.is_dir():
        return sorted(path.glob(f"{prefix}-*.csv"))
    return [Path(p) for p in sorted(glob.glob(os.path.expanduser(spec)))]


def _parse_ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def load_uptime(spec: str) -> list:
    rows = []
    for path in _expand(spec, "uptime"):
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    rows.append(
                        UptimeSample(
                            _parse_ts(row["ts"]),
                            row["ok"] == "1",
                            row.get("code", ""),
                            int(row.get("ms") or 0),
                        )
                    )
                except (ValueError, KeyError):
                    continue  # a torn final line during a crash is not fatal
    rows.sort(key=lambda r: r.ts)
    return rows


def load_netpath(spec: Optional[str]) -> list:
    if not spec:
        return []
    rows = []
    for path in _expand(spec, "netpath"):
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    rows.append(
                        NetSample(
                            _parse_ts(row["ts"]),
                            row["gw"] == "1",
                            row["inet"] == "1",
                            row["dns"] == "1",
                            row["tspeer"] == "1",
                            row.get("tspeer_path", ""),
                        )
                    )
                except (ValueError, KeyError):
                    continue
    rows.sort(key=lambda r: r.ts)
    return rows


# --------------------------------------------------------------------------
# analysis


def median_interval(samples: list) -> float:
    """Cadence measured from the data, so the report stays correct if the cron
    schedule is ever changed."""
    if len(samples) < 3:
        return 30.0
    # zip(strict=) is 3.10+, and the report is run from laptops still on 3.9.
    deltas = [
        (b.ts - a.ts).total_seconds()
        for a, b in zip(samples, samples[1:])  # noqa: B905
        if 0 < (b.ts - a.ts).total_seconds() <= 600
    ]
    return statistics.median(deltas) if deltas else 30.0


def find_outages(samples: list, interval: float) -> "tuple[list, int]":
    """Split failure runs into confirmed outages and single-sample blips."""
    outages, blips = [], 0
    run: list = []

    def flush() -> None:
        nonlocal blips
        if not run:
            return
        if len(run) < CONFIRM_SAMPLES:
            blips += len(run)
            return
        outages.append(
            Outage(
                start=run[0].ts,
                end=run[-1].ts + timedelta(seconds=interval),
                samples=len(run),
                codes=Counter(s.code for s in run),
            )
        )

    for sample in samples:
        if sample.ok:
            flush()
            run = []
        else:
            run.append(sample)
    flush()
    return outages, blips


def classify(outage: Outage, net: list, interval: float) -> None:
    """Attribute an outage to the outermost layer that was failing."""
    lo = outage.start - timedelta(seconds=interval * 2)
    hi = outage.end + timedelta(seconds=interval * 2)
    window = [n for n in net if lo <= n.ts <= hi]
    if not window:
        outage.cause = CAUSE_UNKNOWN
        return

    total = len(window)
    down = {
        "gw": sum(1 for n in window if not n.gw),
        "inet": sum(1 for n in window if not n.inet),
        "dns": sum(1 for n in window if not n.dns),
        "tspeer": sum(1 for n in window if not n.tspeer),
    }
    # "Failing" means most of the window, not a single sample -- one lost ICMP
    # echo inside a 16-minute outage must not rename the cause.
    majority = total / 2

    if down["gw"] > majority:
        outage.cause = CAUSE_LAN
    elif down["inet"] > majority:
        outage.cause = CAUSE_ISP
    elif down["dns"] > majority:
        outage.cause = CAUSE_DNS
    elif down["tspeer"] > majority:
        outage.cause = CAUSE_TAILSCALE
    else:
        outage.cause = CAUSE_APP
    outage.layer_detail = "정상 샘플 " + " · ".join(
        f"{k} {total - v}/{total}" for k, v in down.items()
    )


# --------------------------------------------------------------------------
# rendering


def _kst(dt: datetime) -> datetime:
    return dt.astimezone(KST)


def _dur(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    if total < 60:
        return f"{total}초"
    return f"{total // 60}분 {total % 60:02d}초"


def render(uptime: list, net: list, outages: list, blips: int,
           interval: float) -> str:
    out = []
    first, last = uptime[0].ts, uptime[-1].ts
    span = (last - first).total_seconds()
    expected = span / interval + 1 if interval else len(uptime)
    coverage = min(100.0, len(uptime) / expected * 100) if expected else 0.0
    downtime = sum((o.duration.total_seconds() for o in outages), 0.0)
    availability = 100.0 - (downtime / span * 100) if span else 100.0
    days = span / 86400 if span else 0

    out.append("=" * 68)
    out.append("  AO 앱 서버 가용성 리포트")
    out.append("=" * 68)
    out.append(f"  관측 구간   {_kst(first):%Y-%m-%d %H:%M} ~ {_kst(last):%Y-%m-%d %H:%M} KST"
               f"  ({days:.1f}일)")
    out.append(f"  샘플        {len(uptime):,}개 / {interval:.0f}초 간격"
               f"  (커버리지 {coverage:.1f}%)")
    out.append(f"  내부 프로브 {len(net):,}개")
    out.append("")
    out.append(f"  가용성      {availability:.3f}%")
    out.append(f"  총 다운타임 {_dur(timedelta(seconds=downtime))}")
    out.append(f"  확정 다운   {len(outages)}회"
               + (f"  (하루 평균 {len(outages)/days:.2f}회)" if days >= 1 else ""))
    out.append(f"  순간 블립   {blips}회  (1샘플짜리, 사용자 영향 거의 없음)")
    if coverage < 95:
        out.append("")
        out.append(f"  ⚠ 커버리지가 {coverage:.1f}% 입니다 — 프로버가 멈춘 구간이 있어")
        out.append("    실제 다운타임이 위 수치보다 클 수 있습니다.")

    if outages:
        out.append("")
        out.append("-" * 68)
        out.append("  다운 내역")
        out.append("-" * 68)
        out.append(f"  {'시작 (KST)':<17}{'길이':>9}  {'원인':<24}")
        for o in outages:
            out.append(f"  {_kst(o.start):%m-%d %H:%M:%S}  {_dur(o.duration):>9}  {o.cause:<24}")
            if o.layer_detail:
                out.append(f"  {'':>17}{'':>9}  └ {o.layer_detail}")

        out.append("")
        out.append("-" * 68)
        out.append("  원인별 집계")
        out.append("-" * 68)
        by_cause = defaultdict(lambda: [0, 0.0])
        for o in outages:
            by_cause[o.cause][0] += 1
            by_cause[o.cause][1] += o.duration.total_seconds()
        for cause, (count, secs) in sorted(by_cause.items(), key=lambda kv: -kv[1][1]):
            share = secs / downtime * 100 if downtime else 0
            out.append(f"  {cause:<28}{count:>3}회  {_dur(timedelta(seconds=secs)):>10}"
                       f"  ({share:.0f}%)")

        out.append("")
        out.append("-" * 68)
        out.append("  시간대 분포 (KST, 다운 시작 시각)")
        out.append("-" * 68)
        hours = Counter(_kst(o.start).hour for o in outages)
        peak = max(hours.values()) if hours else 1
        for hour in range(24):
            n = hours.get(hour, 0)
            if n:
                out.append(f"  {hour:02d}시  {'█' * int(n / peak * 30):<30} {n}")

    if net:
        derp = sum(1 for n in net if n.path == "derp")
        if derp:
            out.append("")
            out.append(f"  ※ tailscale 경로가 DERP 릴레이로 강등된 샘플 {derp:,}건"
                       f" ({derp/len(net)*100:.1f}%) — 직결이 안 되면 느려집니다.")

    out.append("")
    return "\n".join(out)


def to_json(uptime: list, outages: list, blips: int, interval: float) -> str:
    first, last = uptime[0].ts, uptime[-1].ts
    span = (last - first).total_seconds()
    downtime = sum((o.duration.total_seconds() for o in outages), 0.0)
    return json.dumps(
        {
            "from": first.isoformat(),
            "to": last.isoformat(),
            "samples": len(uptime),
            "interval_s": interval,
            "availability_pct": round(100.0 - (downtime / span * 100) if span else 100.0, 4),
            "downtime_s": int(downtime),
            "outages": [
                {
                    "start": o.start.isoformat(),
                    "end": o.end.isoformat(),
                    "duration_s": int(o.duration.total_seconds()),
                    "cause": o.cause,
                    "layers": o.layer_detail,
                }
                for o in outages
            ],
            "blips": blips,
        },
        ensure_ascii=False,
        indent=2,
    )


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--uptime", required=True,
                        help="directory or glob of uptime-*.csv (from Lightsail)")
    parser.add_argument("--netpath", default=None,
                        help="directory or glob of netpath-*.csv (from the office VM)")
    parser.add_argument("--since", default=None, help="YYYY-MM-DD (KST)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    uptime = load_uptime(args.uptime)
    if not uptime:
        print(f"no uptime samples found under {args.uptime}", file=sys.stderr)
        return 2
    net = load_netpath(args.netpath)

    if args.since:
        cutoff = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=KST)
        uptime = [s for s in uptime if s.ts >= cutoff]
        net = [s for s in net if s.ts >= cutoff]
        if not uptime:
            print(f"no samples at or after {args.since}", file=sys.stderr)
            return 2

    interval = median_interval(uptime)
    outages, blips = find_outages(uptime, interval)
    for outage in outages:
        classify(outage, net, interval)

    if args.json:
        print(to_json(uptime, outages, blips, interval))
    else:
        print(render(uptime, net, outages, blips, interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
