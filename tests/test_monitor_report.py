"""`classify()` must not call a network outage our own bug.

The report exists to answer one question an operator cannot answer from
nginx alone: was the office line down, or is this ours? Getting that backwards
is worse than not answering, because "앱/서버 (네트워크 정상)" sends someone
after an application bug that does not exist.

It was backwards for every short outage. `classify()` padded the sample window
by two probe intervals on each side and then required a strict majority of
that padded window to be down, so an outage shorter than the padding could not
reach a majority on any layer no matter what the network did. Measured over
2026-08-18..09-09 the verdict was a pure function of duration: all five
outages >= 3m30s were called LAN and all four <= 2m30s were called "network
fine" -- though every one of those four contains a sample with all four layers
down, and two were all-down throughout.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PY = REPO_ROOT / "scripts" / "monitor" / "report.py"


@pytest.fixture(scope="module")
def report():
    """Load scripts/monitor/report.py — an operator script, not a package.

    It must be in ``sys.modules`` before it executes: the file uses
    ``from __future__ import annotations``, so ``@dataclass`` resolves its
    field types by looking its own module up by name.
    """
    spec = importlib.util.spec_from_file_location("ao_monitor_report", REPORT_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:  # pragma: no cover - import failure is the test's problem
        del sys.modules[spec.name]
        raise
    yield module
    del sys.modules[spec.name]


T0 = datetime(2026, 9, 4, 8, 10, 37, tzinfo=timezone.utc)


def _outage(report, seconds: int):
    return report.Outage(start=T0, end=T0 + timedelta(seconds=seconds), samples=2)


def _net(report, offset: int, *, gw=True, inet=True, dns=True, tspeer=True):
    return report.NetSample(
        ts=T0 + timedelta(seconds=offset),
        gw=gw,
        inet=inet,
        dns=dns,
        tspeer=tspeer,
        path="direct" if tspeer else "",
    )


def _all_down(report, offset: int):
    return _net(report, offset, gw=False, inet=False, dns=False, tspeer=False)


class TestShortOutagesAreAttributable:
    """The regression: duration must not decide the verdict."""

    def test_ninety_second_outage_with_the_lan_down_is_lan(self, report):
        """The exact shape of 2026-09-01 12:50 KST, previously called our bug.

        Three in-span samples, every layer down in all of them. The old padded
        window added four healthy neighbours, so 3 down out of 7 missed the
        strict majority and fell through to CAUSE_APP.
        """
        outage = _outage(report, 95)
        net = [
            _net(report, -60),  # healthy, before the outage
            _net(report, -30),
            _all_down(report, 24),
            _all_down(report, 54),
            _all_down(report, 84),
            _net(report, 120),  # healthy, after it
            _net(report, 150),
        ]

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_LAN

    def test_the_healthy_neighbours_are_excluded_from_the_denominator(self, report):
        """layer_detail counts the outage, not the padding."""
        outage = _outage(report, 95)
        net = [_net(report, -30), _all_down(report, 24), _all_down(report, 54), _net(report, 150)]

        report.classify(outage, net)

        assert "gw 0/2" in outage.layer_detail

    @pytest.mark.parametrize("seconds", [60, 95, 150, 400, 900])
    def test_verdict_does_not_depend_on_duration(self, report, seconds):
        """Same network evidence, five durations, one answer.

        Starts at 60s because a 30-second probe cadence cannot fit two samples
        into anything shorter, and two is the floor for a verdict. That is a
        limit of the evidence, not of the classifier -- see
        TestAVerdictNeedsWitnesses.
        """
        outage = _outage(report, seconds)
        net = (
            [_net(report, -30)]
            + [_all_down(report, off) for off in range(15, seconds, 30)]
            + [_net(report, seconds + 60)]
        )

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_LAN


class TestAppIsAPositiveFinding:
    """CAUSE_APP must be evidence, never the fall-through."""

    def test_every_layer_up_in_every_sample_blames_the_app(self, report):
        outage = _outage(report, 95)
        net = [_net(report, 24), _net(report, 54), _net(report, 84)]

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_APP

    def test_a_partial_failure_is_not_reported_as_network_fine(self, report):
        """Some layers down, none for a majority: unproven, not exonerated.

        A router coming back mid-outage looks exactly like this. The old code
        put it in the same bucket as a clean network.
        """
        outage = _outage(report, 125)
        net = [
            _all_down(report, 24),
            _net(report, 54),
            _net(report, 84),
            _net(report, 114, inet=False),
        ]

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_PARTIAL
        assert outage.cause != report.CAUSE_APP

    def test_one_lost_echo_in_a_long_outage_does_not_name_a_layer(self, report):
        """The protection the majority rule was written for, still standing.

        One dropped echo in a 15-minute outage must not blame the LAN. It does
        stop the report calling the network clean, which is the intended
        trade: 29 good samples and one bad one is not "every layer answered".
        """
        outage = _outage(report, 900)
        net = [_net(report, off) for off in range(15, 900, 30)]
        net[7] = _net(report, 15 + 7 * 30, gw=False)

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_PARTIAL
        assert "gw 29/30" in outage.layer_detail

    def test_a_spotless_long_outage_is_still_ours(self, report):
        """The companion to the test above: zero tolerance, not zero reach.

        Without this, making CAUSE_APP evidence-based could quietly make it
        unreachable and nobody would notice.
        """
        outage = _outage(report, 900)

        report.classify(outage, [_net(report, off) for off in range(15, 900, 30)])

        assert outage.cause == report.CAUSE_APP


class TestAVerdictNeedsWitnesses:
    """A cause must rest on samples taken during the outage, and on enough of them."""

    def test_no_samples_inside_the_outage_is_unknown_not_app(self, report):
        outage = _outage(report, 95)

        report.classify(outage, [_net(report, -300), _net(report, 600)])

        assert outage.cause == report.CAUSE_UNKNOWN

    def test_a_single_sample_decides_nothing(self, report):
        """With n=1 every layer is trivially a majority.

        One healthy sample would exonerate the network and one dropped echo
        would convict a layer, on the same evidence either way.
        """
        outage = _outage(report, 95)

        report.classify(outage, [_net(report, 40)])

        assert outage.cause == report.CAUSE_UNKNOWN

    def test_the_recovery_sample_does_not_testify(self, report):
        """Outage.end is the first sample that RECOVERED, so it is not evidence.

        Shape of 2026-08-11 19:30:37 in the retained CSVs: the inside prober
        went quiet for the whole outage and the only row in the closed
        interval was taken after it ended. A closed window let that one
        healthy row decide the verdict.
        """
        outage = _outage(report, 120)
        net = [_net(report, 120), _net(report, 150)]

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_UNKNOWN


class TestLayerPriority:
    """Outermost-first walk is unchanged by the window fix."""

    def test_gateway_up_but_wan_down_is_the_isp(self, report):
        """2026-09-04 17:10 KST: gw answered, 1.1.1.1 did not."""
        outage = _outage(report, 94)
        net = [
            _all_down(report, 24),
            _net(report, 70, inet=False),
            _net(report, 88, inet=False),
        ]

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_ISP

    def test_tunnel_only_failure_is_the_tunnel(self, report):
        outage = _outage(report, 95)
        net = [_net(report, off, tspeer=False) for off in (24, 54, 84)]

        report.classify(outage, net)

        assert outage.cause == report.CAUSE_TAILSCALE
