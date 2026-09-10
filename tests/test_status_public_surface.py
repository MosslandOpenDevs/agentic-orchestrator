"""What the unauthenticated endpoints may and may not publish.

``/status`` is listed in the links.moss.land registry as this service's status
endpoint and ``/usage`` is called by the public web client; neither takes a
credential, so both are read by anyone. Three properties have to hold together:

1. It must answer "is this pipeline actually running?" — the Q2 report's whole
   objection to cumulative counters was that they stay put when ingestion dies.
   That is what ``stats.last_signal_at`` is for.
2. Neither may publish deployment detail that has nothing to do with that
   question — specifically which vendor and which exact model each paid tier
   buys. Both route the router report through ``_public_router_view``.
3. Every instant published has to say that it is UTC. A marker-less ISO string
   is read as *local time* by the browser, so in KST a nine-hour-old value
   renders as current — a freshness field reporting the opposite of the truth.

All three are easy to lose in a refactor and none of them fails loudly, so they
are pinned here.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import agentic_orchestrator.api.main as api_main
from agentic_orchestrator.api.main import _public_router_view, app
from agentic_orchestrator.db.connection import Database


def _report(**tier_overrides):
    tier = {
        "name": "debate",
        "enabled": True,
        "provider": "openai",
        "model": "gpt-5.4-mini",
        "active": True,
        "reason": None,
        "reason_code": None,
    }
    tier.update(tier_overrides)
    return {
        "status": "healthy",
        "local_only": False,
        "degraded_tiers": [],
        "paid_tiers": {"debate": tier},
    }


class TestPublicRouterView:
    def test_vendor_and_model_are_not_published(self):
        view = _public_router_view(_report())
        debate = view["paid_tiers"]["debate"]
        assert "provider" not in debate
        assert "model" not in debate

    def test_the_operational_answer_survives(self):
        """Redaction must not cost the signal the endpoint exists to give."""
        view = _public_router_view(
            _report(
                active=False,
                reason="tier 'debate' is disabled (llm.paid_tiers.debate.enabled)",
                reason_code="disabled",
            )
        )
        assert view["status"] == "healthy"
        assert view["local_only"] is False
        assert view["degraded_tiers"] == []
        debate = view["paid_tiers"]["debate"]
        # "could a paid tier bill anything at all, or are we silently all-local?"
        assert debate["enabled"] is True
        assert debate["active"] is False
        assert debate["name"] == "debate"
        # The verdict survives; the config path that produced it does not.
        assert debate["reason_code"] == "disabled"
        assert debate["reason"] == "tier is disabled"
        assert "llm.paid_tiers" not in debate["reason"]

    def test_degraded_state_passes_through(self):
        report = _report(active=False)
        report["status"] = "degraded"
        report["degraded_tiers"] = ["debate"]
        view = _public_router_view(report)
        assert view["status"] == "degraded"
        assert view["degraded_tiers"] == ["debate"]

    def test_input_is_not_mutated(self):
        """Redaction must not corrupt the caller's own copy of the report."""
        report = _report()
        _public_router_view(report)
        assert report["paid_tiers"]["debate"]["model"] == "gpt-5.4-mini"
        assert report["paid_tiers"]["debate"]["provider"] == "openai"

    def test_degenerate_reports_pass_through_untouched(self):
        """A router that failed to report must not turn into a crash here."""
        assert _public_router_view({"status": "unknown"}) == {"status": "unknown"}
        assert _public_router_view({"paid_tiers": None}) == {"paid_tiers": None}

    def test_non_dict_tier_is_left_alone(self):
        report = {"status": "healthy", "paid_tiers": {"debate": "unavailable"}}
        assert _public_router_view(report)["paid_tiers"]["debate"] == "unavailable"


class TestNoPublicRouteLeaksTheModelPin:
    """The two guarantees the redactor exists for, checked on real output.

    An earlier version of this class scanned source text for unredacted call
    sites and got the exclusion condition wrong -- it skipped every line
    containing ``paid_tier_report()``, which is every line it was supposed to
    inspect, so reverting /status to the leaking call still passed. Both
    checks below run against actual values instead.
    """

    def test_call_sites_are_wrapped(self):
        """Every paid_tier_report() call that feeds a response is wrapped.

        Parsed, not grepped: a docstring mentioning the function is not a call,
        and a call is not excused by the words around it.
        """
        import ast
        import inspect

        from agentic_orchestrator.api import main

        tree = ast.parse(inspect.getsource(main))
        wrapped, bare = set(), []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "_public_router_view":
                for arg in node.args:
                    if (
                        isinstance(arg, ast.Call)
                        and getattr(arg.func, "id", None) == "paid_tier_report"
                    ):
                        wrapped.add(arg.lineno)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "paid_tier_report"
                and node.lineno not in wrapped
            ):
                bare.append(node.lineno)
        assert bare == [], f"paid_tier_report() called unwrapped at line(s) {bare}"

    def test_no_deployment_detail_survives_in_the_payload(self, monkeypatch):
        """Seed a distinctive vendor and model, then look for them in the output.

        Key-level redaction alone is not enough: the private `reason` string
        interpolates the provider name and its API-key environment variable,
        so a tier that is merely missing its key used to put both back.
        """
        import json

        from agentic_orchestrator.api.main import _public_router_view
        from agentic_orchestrator.llm import router as router_mod

        monkeypatch.setattr(
            router_mod,
            "_cached_paid_tiers",
            lambda: {
                "debate": {
                    "enabled": True,
                    "provider": "acmevendor",
                    "model": "acme-supermodel-9",
                }
            },
        )
        monkeypatch.setattr(router_mod, "local_llm_only", lambda: False)
        # No API key for this provider -> the "provider unavailable" branch,
        # which is exactly the reason string that used to leak.
        monkeypatch.setitem(router_mod._PROVIDER_KEY_ENV, "acmevendor", "ACME_API_KEY")
        monkeypatch.delenv("ACME_API_KEY", raising=False)

        report = router_mod.paid_tier_report()
        private = json.dumps(report)
        assert (
            "acmevendor" in private and "acme-supermodel-9" in private
        ), "the fixture is not exercising the path it claims to"
        assert "ACME_API_KEY" in private, "expected the leaky reason branch"

        public = json.dumps(_public_router_view(report))
        for secret in ("acmevendor", "acme-supermodel-9", "ACME_API_KEY"):
            assert secret not in public, f"{secret} survived redaction: {public}"

        # The operational answer must still be there.
        tier = _public_router_view(report)["paid_tiers"]["debate"]
        assert tier["enabled"] is True
        assert tier["active"] is False
        assert tier["reason_code"] == "provider_unavailable"
        assert tier["reason"] == "provider credentials are unavailable"


@pytest.fixture
def served_client(tmp_path, monkeypatch):
    """A client over a database that exists and answers, so every probe is 200."""
    db = Database(f"sqlite:///{tmp_path / 'served.db'}")
    db.create_tables()
    monkeypatch.setattr(api_main, "get_db", lambda: db)
    return TestClient(app)


@pytest.fixture
def tableless_client(tmp_path, monkeypatch):
    """Connectable, but with no schema: /status degrades and still answers 200."""
    db_file = tmp_path / "empty.db"
    db_file.touch()
    monkeypatch.setattr(api_main, "get_db", lambda: Database(f"sqlite:///{db_file}"))
    return TestClient(app)


def _parse_marked_utc(value):
    """Assert the string says it is UTC, and return the instant it names.

    Split out of the near-now check below because the two questions come apart:
    a response-generation stamp must be marked *and* recent, while a stored
    row's timestamp must be marked and equal to what was stored — which is a
    stronger check, and would fail a near-now assertion by construction.
    """
    assert isinstance(value, str), f"not a timestamp: {value!r}"
    assert value.endswith("Z"), f"no UTC marker: {value!r}"
    return datetime.fromisoformat(value[:-1] + "+00:00")


class TestPublishedInstantsCarryTheUTCMarker:
    """Property 3, checked on real responses rather than on the source.

    Measured live on 2026-09-09, ``/status`` published
    ``"timestamp": "2026-09-09T07:26:51.117534"`` directly beside a correctly
    marked ``stats.last_signal_at``: the first came from
    ``utcnow().isoformat()``, the second from ``utc_iso()``. Nothing about the
    difference fails loudly — the value stays plausible and merely means
    something nine hours away from what it says.
    """

    @staticmethod
    def _assert_marked_utc(value):
        # Marked *and* meant: it has to parse as an instant near now, not be a
        # local time with a "Z" stapled onto it.
        parsed = _parse_marked_utc(value)
        drift = abs((datetime.now(timezone.utc) - parsed).total_seconds())
        assert drift < 300, f"{value!r} is {drift:.0f}s away from now"

    def test_health(self, served_client):
        self._assert_marked_utc(served_client.get("/health").json()["timestamp"])

    def test_ready(self, served_client):
        self._assert_marked_utc(served_client.get("/ready").json()["timestamp"])

    def test_status(self, served_client):
        self._assert_marked_utc(served_client.get("/status").json()["timestamp"])

    def test_status_while_degraded(self, tableless_client):
        """The degraded answer is the one an operator reads under pressure, and
        it is produced by a different branch than the healthy one."""
        body = tableless_client.get("/status").json()

        assert body["status"] == "degraded"
        self._assert_marked_utc(body["timestamp"])


@pytest.fixture
def seeded_client(tmp_path, monkeypatch):
    """A client over a database holding one row of every model the API serves.

    Every timestamp is deliberately NOT "now": these are stored instants, and
    the property under test is that the value survives the round trip meaning
    the same moment it meant going in. A near-now assertion would pass on a
    serializer that ignored the column entirely.
    """
    from agentic_orchestrator.db.models import (
        DebateMessage,
        DebateSession,
        Idea,
        Plan,
        Project,
        Signal,
        Trend,
    )

    db = Database(f"sqlite:///{tmp_path / 'seeded.db'}")
    db.create_tables()

    stamp = datetime(2026, 9, 9, 7, 26, 51, 117534)
    session = db.get_session()
    session.add(
        Signal(
            id="sig-1",
            source="rss",
            category="ai",
            title="A seeded signal with a title long enough to look real",
            collected_at=stamp,
            created_at=stamp,
        )
    )
    session.add(
        Trend(id="trend-1", period="24h", name="A seeded trend", score=8.0, analyzed_at=stamp)
    )
    session.add(
        Idea(
            id="idea-1",
            title="A seeded idea",
            summary="A seeded idea summary",
            source_type="debate",
            created_at=stamp,
        )
    )
    session.add(
        DebateSession(
            id="debate-1",
            phase="divergence",
            topic="A seeded debate topic",
            started_at=stamp,
            completed_at=stamp,
        )
    )
    session.add(
        DebateMessage(
            id="msg-1",
            session_id="debate-1",
            agent_id="a1",
            agent_name="Agent One",
            message_type="propose",
            content="A seeded message",
            created_at=stamp,
        )
    )
    session.add(
        Plan(
            id="plan-1", idea_id="idea-1", title="A seeded plan", created_at=stamp, updated_at=stamp
        )
    )
    session.add(
        Project(
            id="project-1",
            plan_id="plan-1",
            name="seeded-project",
            created_at=stamp,
            completed_at=stamp,
        )
    )
    session.commit()
    session.close()

    monkeypatch.setattr(api_main, "get_db", lambda: db)
    return TestClient(app), stamp


class TestStoredInstantsCarryTheUTCMarkerToo:
    """The same property, on the endpoints that publish rows rather than "now".

    ``/status`` was made correct by #5002; every list endpoint was not, because
    the rule lived at the six call sites that answer a monitor rather than in
    ``to_dict()``, where the rows are actually serialised. Those are the
    timestamps the dashboard renders — a signal's ``collected_at`` is what the
    front-page banner ages — so this is where the nine-hour skew was visible.

    Checked through the real endpoints, and checked for *meaning*: the instant
    that comes back has to be the instant that went in. Stapling a "Z" onto a
    naive local time would satisfy the marker and fail here.
    """

    @staticmethod
    def _assert_is(value, stamp):
        parsed = _parse_marked_utc(value)
        assert parsed == stamp.replace(tzinfo=timezone.utc), f"{value!r} is not {stamp}"

    def test_signals_list(self, seeded_client):
        client, stamp = seeded_client
        body = client.get("/signals?hours=720").json()
        self._assert_is(body["signals"][0]["collected_at"], stamp)

    def test_signal_detail(self, seeded_client):
        """Guards the delegation: this handler used to hand-copy to_dict()."""
        client, stamp = seeded_client
        self._assert_is(client.get("/signals/sig-1").json()["collected_at"], stamp)

    def test_trends(self, seeded_client):
        client, stamp = seeded_client
        self._assert_is(client.get("/trends").json()["trends"][0]["analyzed_at"], stamp)

    def test_ideas(self, seeded_client):
        client, stamp = seeded_client
        self._assert_is(client.get("/ideas").json()["ideas"][0]["created_at"], stamp)

    def test_debates(self, seeded_client):
        client, stamp = seeded_client
        debate = client.get("/debates").json()["debates"][0]
        self._assert_is(debate["started_at"], stamp)
        self._assert_is(debate["completed_at"], stamp)

    def test_debate_messages(self, seeded_client):
        client, stamp = seeded_client
        body = client.get("/debates/debate-1").json()
        self._assert_is(body["messages"][0]["created_at"], stamp)

    def test_plans(self, seeded_client):
        client, stamp = seeded_client
        self._assert_is(client.get("/plans").json()["plans"][0]["created_at"], stamp)

    def test_plan_detail(self, seeded_client):
        client, stamp = seeded_client
        body = client.get("/plans/plan-1").json()
        self._assert_is(body["created_at"], stamp)
        self._assert_is(body["updated_at"], stamp)

    def test_projects(self, seeded_client):
        client, stamp = seeded_client
        project = client.get("/projects").json()["projects"][0]
        self._assert_is(project["created_at"], stamp)
        self._assert_is(project["completed_at"], stamp)

    def test_signals_timeline(self, seeded_client):
        client, _ = seeded_client
        body = client.get("/signals/timeline").json()
        TestPublishedInstantsCarryTheUTCMarker._assert_marked_utc(body["timestamp"])

    def test_pipeline_live(self, seeded_client):
        client, _ = seeded_client
        body = client.get("/pipeline/live").json()
        TestPublishedInstantsCarryTheUTCMarker._assert_marked_utc(body["timestamp"])


class TestTheOneFieldThatMustStayUnmarked:
    """``/usage`` history rows carry a calendar date, not an instant.

    A date has no moment to mark, and ``utc_iso`` does not merely produce a
    wrong string for one — it reads ``.tzinfo``, which a ``date`` does not
    have, and raises. This is pinned so the next grep-driven sweep over
    ``.isoformat()`` does not "finish the job" and 500 the endpoint.
    """

    def test_usage_history_dates_are_plain_calendar_days(self, served_client):
        import re

        for row in served_client.get("/usage").json().get("history", []):
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]), row["date"]

    def test_utc_iso_is_not_applicable_to_a_date(self):
        from datetime import date

        from agentic_orchestrator.timeutil import utc_iso

        with pytest.raises(AttributeError):
            utc_iso(date(2026, 9, 10))
