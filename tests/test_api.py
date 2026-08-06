"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator import __version__
from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.models import (
    Base,
    DebateMessage,
    DebateSession,
    Idea,
    Plan,
    Signal,
    Trend,
)
from agentic_orchestrator.timeutil import utcnow

# Create test database
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database with fresh tables for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # noqa: N806
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session

    session = TestingSessionLocal()
    yield session
    session.close()

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_signals(test_db):
    """Create sample signals in the database."""
    signals = [
        Signal(
            source="rss",
            category="crypto",
            title="Bitcoin hits new high",
            summary="BTC reaches $100k",
            score=9.5,
            collected_at=utcnow(),
        ),
        Signal(
            source="github",
            category="ai",
            title="New AI model released",
            summary="GPT-5 announced",
            score=8.5,
            collected_at=utcnow(),
        ),
        Signal(
            source="rss",
            category="crypto",
            title="ETH upgrade complete",
            summary="Ethereum 3.0 live",
            score=7.5,
            collected_at=utcnow(),
        ),
    ]
    for signal in signals:
        test_db.add(signal)
    test_db.commit()
    return signals


@pytest.fixture
def sample_trends(test_db):
    """Create sample trends in the database."""
    trends = [
        Trend(
            period="24h",
            name="Bitcoin Rally",
            description="BTC showing strong momentum",
            score=9.0,
            signal_count=5,
            category="crypto",
            analyzed_at=utcnow(),
        ),
        Trend(
            period="24h",
            name="AI Developments",
            description="Major AI announcements",
            score=8.5,
            signal_count=3,
            category="ai",
            analyzed_at=utcnow(),
        ),
    ]
    for trend in trends:
        test_db.add(trend)
    test_db.commit()
    return trends


@pytest.fixture
def sample_ideas(test_db):
    """Create sample ideas in the database."""
    ideas = [
        Idea(
            title="DeFi Dashboard",
            summary="Build a DeFi analytics dashboard",
            source_type="trend_based",
            status="pending",
            score=8.0,
        ),
        Idea(
            title="AI Trading Bot",
            summary="Automated trading using AI",
            source_type="traditional",
            status="in_debate",
            score=7.5,
        ),
    ]
    for idea in ideas:
        test_db.add(idea)
    test_db.commit()
    return ideas


@pytest.fixture
def sample_debates(test_db, sample_ideas):
    """Create sample debate sessions in the database."""
    idea = sample_ideas[0]
    session = DebateSession(
        idea_id=idea.id,
        phase="divergence",
        round_number=1,
        max_rounds=3,
        status="active",
        participants=["agent1", "agent2"],
    )
    test_db.add(session)
    test_db.commit()

    # Add messages
    messages = [
        DebateMessage(
            session_id=session.id,
            agent_id="agent1",
            agent_name="Founder",
            message_type="propose",
            content="I propose we build this.",
        ),
        DebateMessage(
            session_id=session.id,
            agent_id="agent2",
            agent_name="VC",
            message_type="support",
            content="I support this proposal.",
        ),
    ]
    for msg in messages:
        test_db.add(msg)
    test_db.commit()

    return [session]


@pytest.fixture
def sample_plans(test_db, sample_ideas):
    """Create sample plans in the database."""
    idea = sample_ideas[0]
    plan = Plan(
        idea_id=idea.id,
        title="DeFi Dashboard Plan",
        version=1,
        status="draft",
        prd_content="Product requirements...",
        architecture_content="System design...",
    )
    test_db.add(plan)
    test_db.commit()
    return [plan]


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        # Track the package version rather than a literal, which had drifted.
        assert data["version"] == __version__


class TestRootEndpoint:
    """Tests for / endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MOSS.AO API"
        # Assert the version is present and well-formed rather than a hardcoded
        # value, so a version bump doesn't break this test.
        assert isinstance(data["version"], str) and data["version"]
        assert "endpoints" in data
        assert "/signals" in data["endpoints"].values()
        assert "/trends" in data["endpoints"].values()
        assert "/ideas" in data["endpoints"].values()


class TestStatusEndpoint:
    """Tests for /status endpoint."""

    def test_status_endpoint(self, client, sample_signals):
        """Test status endpoint returns system status."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["operational", "degraded"]
        assert "components" in data
        assert "stats" in data
        assert "agents_active" in data["stats"]


class TestSignalsEndpoint:
    """Tests for /signals endpoint."""

    def test_get_signals_empty(self, client):
        """Test getting signals when none exist."""
        response = client.get("/signals")
        assert response.status_code == 200
        data = response.json()
        assert data["signals"] == []
        assert data["total"] == 0

    def test_get_signals_with_data(self, client, sample_signals):
        """Test getting signals with data."""
        response = client.get("/signals")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 3
        assert data["total"] == 3

    def test_get_signals_with_limit(self, client, sample_signals):
        """Test getting signals with limit."""
        response = client.get("/signals?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 2
        assert data["limit"] == 2

    def test_get_signals_filter_by_source(self, client, sample_signals):
        """Test filtering signals by source."""
        response = client.get("/signals?source=rss")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 2
        for signal in data["signals"]:
            assert signal["source"] == "rss"

    def test_get_signals_filter_by_category(self, client, sample_signals):
        """Test filtering signals by category."""
        response = client.get("/signals?category=ai")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 1
        assert data["signals"][0]["category"] == "ai"

    def test_get_signals_filter_by_min_score(self, client, sample_signals):
        """Test filtering signals by minimum score."""
        response = client.get("/signals?min_score=8.0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["signals"]) == 2
        for signal in data["signals"]:
            assert signal["score"] >= 8.0


class TestTrendsEndpoint:
    """Tests for /trends endpoint."""

    def test_get_trends_empty(self, client):
        """Test getting trends when none exist."""
        response = client.get("/trends")
        assert response.status_code == 200
        data = response.json()
        assert data["trends"] == []

    def test_get_trends_with_data(self, client, sample_trends):
        """Test getting trends with data."""
        response = client.get("/trends")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trends"]) == 2
        assert data["period"] == "all"  # /trends defaults to period="all"

    def test_get_trends_filter_by_category(self, client, sample_trends):
        """Test filtering trends by category."""
        response = client.get("/trends?category=crypto")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trends"]) == 1
        assert data["trends"][0]["category"] == "crypto"


class TestIdeasEndpoint:
    """Tests for /ideas endpoint."""

    def test_get_ideas_empty(self, client):
        """Test getting ideas when none exist."""
        response = client.get("/ideas")
        assert response.status_code == 200
        data = response.json()
        assert data["ideas"] == []

    def test_get_ideas_with_data(self, client, sample_ideas):
        """Test getting ideas with data."""
        response = client.get("/ideas")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ideas"]) == 2
        assert "status_counts" in data

    def test_get_ideas_filter_by_status(self, client, sample_ideas):
        """Test filtering ideas by status."""
        response = client.get("/ideas?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ideas"]) == 1
        assert data["ideas"][0]["status"] == "pending"

    def test_get_idea_detail(self, client, sample_ideas):
        """Test getting idea detail."""
        idea_id = sample_ideas[0].id
        response = client.get(f"/ideas/{idea_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["idea"]["title"] == "DeFi Dashboard"

    def test_get_idea_detail_not_found(self, client):
        """Test getting non-existent idea returns 404."""
        response = client.get("/ideas/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestPlansEndpoint:
    """Tests for /plans endpoint."""

    def test_get_plans_empty(self, client):
        """Test getting plans when none exist."""
        response = client.get("/plans")
        assert response.status_code == 200
        data = response.json()
        assert data["plans"] == []

    def test_get_plans_with_data(self, client, sample_plans):
        """Test getting plans with data."""
        response = client.get("/plans")
        assert response.status_code == 200
        data = response.json()
        assert len(data["plans"]) == 1

    def test_get_plan_detail(self, client, sample_plans):
        """Test getting plan detail."""
        plan_id = sample_plans[0].id
        response = client.get(f"/plans/{plan_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "DeFi Dashboard Plan"
        assert "prd_content" in data


class TestDebatesEndpoint:
    """Tests for /debates endpoint."""

    def test_get_debates_empty(self, client):
        """Test getting debates when none exist."""
        response = client.get("/debates")
        assert response.status_code == 200
        data = response.json()
        assert data["debates"] == []

    def test_get_debates_with_data(self, client, sample_debates):
        """Test getting debates with data."""
        response = client.get("/debates")
        assert response.status_code == 200
        data = response.json()
        assert len(data["debates"]) == 1

    def test_get_debates_filter_by_status(self, client, sample_debates):
        """Test filtering debates by status."""
        response = client.get("/debates?status=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["debates"]) == 1

    def test_get_debate_detail(self, client, sample_debates):
        """Test getting debate detail with messages."""
        session_id = sample_debates[0].id
        response = client.get(f"/debates/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["debate"]["phase"] == "divergence"
        assert data["message_count"] == 2
        assert len(data["messages"]) == 2


class TestUsageEndpoint:
    """Tests for /usage endpoint."""

    def test_get_usage_empty(self, client):
        """Test getting usage when none recorded."""
        response = client.get("/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["today"]["total_cost"] == 0
        assert data["month_total"] == 0


class TestActivityEndpoint:
    """Tests for /activity endpoint."""

    def test_get_activity_empty(self, client):
        """Test getting activity when none exist."""
        response = client.get("/activity")
        assert response.status_code == 200
        data = response.json()
        assert data["activities"] == []


class TestAgentsEndpoint:
    """Tests for /agents endpoint."""

    def test_get_all_agents(self, client):
        """Test getting all agents."""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 34  # 16 + 8 + 10
        assert len(data["agents"]) == 34
        # Verify agent structure
        agent = data["agents"][0]
        assert "id" in agent
        assert "name" in agent
        assert "role" in agent
        assert "phase" in agent
        assert "personality" in agent
        assert "thinking" in agent["personality"]
        assert "decision" in agent["personality"]

    def test_get_agents_by_phase(self, client):
        """Test getting agents by phase."""
        response = client.get("/agents?phase=divergence")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 16
        for agent in data["agents"]:
            assert agent["phase"] == "divergence"

    def test_get_convergence_agents(self, client):
        """Test getting convergence agents."""
        response = client.get("/agents?phase=convergence")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 8
        for agent in data["agents"]:
            assert agent["phase"] == "convergence"

    def test_get_planning_agents(self, client):
        """Test getting planning agents."""
        response = client.get("/agents?phase=planning")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        for agent in data["agents"]:
            assert agent["phase"] == "planning"


class TestLiteralRouteOrdering:
    """Literal paths must out-rank their parameterized siblings.

    Starlette matches routes in registration order, so a literal route declared
    *after* a same-prefix parameterized route is unreachable: ``/signals/timeline``
    silently binds ``signal_id="timeline"``. These tests assert the intended
    payload shape, which is what actually distinguishes the two handlers.
    """

    def test_signals_timeline_reaches_timeline_handler(self, client, sample_signals):
        """GET /signals/timeline must not bind signal_id='timeline'."""
        response = client.get("/signals/timeline?period=24h")
        assert response.status_code == 200

        data = response.json()
        # Timeline shape, not the single-signal shape.
        assert set(data) >= {"slots", "total", "period", "timestamp"}
        assert "sentiment" not in data
        assert data["period"] == "24h"
        assert len(data["slots"]) == 24
        for slot in data["slots"]:
            assert set(slot) == {"label", "count", "hour"}

        # Cover the numbers the widget draws, not just the shape: all three
        # sample signals were collected now, so they must all be counted once.
        assert data["total"] == len(sample_signals)
        assert sum(s["count"] for s in data["slots"]) == len(sample_signals)

    def test_signals_timeline_7d_period(self, client, sample_signals):
        """The 7d period returns seven daily slots, not a signal detail."""
        response = client.get("/signals/timeline?period=7d")
        assert response.status_code == 200

        data = response.json()
        assert data["period"] == "7d"
        assert len(data["slots"]) == 7
        for slot in data["slots"]:
            assert set(slot) == {"label", "count"}

        assert data["total"] == len(sample_signals)
        assert sum(s["count"] for s in data["slots"]) == len(sample_signals)

    def test_signals_detail_still_routes(self, client, sample_signals):
        """Moving the literal route must not break /signals/{signal_id}."""
        response = client.get(f"/signals/{sample_signals[0].id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_signals[0].id
        assert data["title"] == "Bitcoin hits new high"

    def test_signals_unknown_id_still_404s(self, client):
        response = client.get("/signals/does-not-exist")
        assert response.status_code == 404

    def test_plans_pending_approval_reaches_list_handler(self, client, sample_plans):
        """GET /plans/pending-approval must not bind plan_id='pending-approval'."""
        response = client.get("/plans/pending-approval")
        assert response.status_code == 200

        data = response.json()
        # List shape, not the single-plan shape.
        assert set(data) >= {"plans", "total", "message"}
        assert "prd_content" not in data
        assert isinstance(data["plans"], list)

        # sample_plans creates one draft plan, which is pending approval.
        assert data["total"] == 1
        assert data["plans"][0]["id"] == sample_plans[0].id
        assert data["plans"][0]["status"] == "draft"

    def test_plans_pending_approval_excludes_approved(self, client, test_db, sample_plans):
        """Only draft plans are pending approval."""
        sample_plans[0].status = "approved"
        test_db.commit()

        response = client.get("/plans/pending-approval")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert data["plans"] == []

    def test_plan_detail_still_routes(self, client, sample_plans):
        """Moving the literal route must not break /plans/{plan_id}."""
        response = client.get(f"/plans/{sample_plans[0].id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_plans[0].id
        assert data["title"] == "DeFi Dashboard Plan"
        assert data["prd_content"] == "Product requirements..."

    def test_plans_unknown_id_still_404s(self, client):
        response = client.get("/plans/does-not-exist")
        assert response.status_code == 404

    def test_no_literal_route_is_shadowed(self):
        """Guard against future regressions of the same class.

        Any literal path segment must be registered before a parameterized
        sibling that would swallow it.
        """
        from agentic_orchestrator.api.main import app

        seen: list[tuple[tuple[str, ...], set]] = []
        shadowed: list[str] = []

        for route in app.routes:
            path = getattr(route, "path", None)
            if path is None:
                continue
            methods = set(getattr(route, "methods", None) or ())
            parts = tuple(path.strip("/").split("/"))
            for earlier, earlier_methods in seen:
                if len(earlier) != len(parts):
                    continue
                # Starlette keeps scanning past a path match whose method does not
                # match, so routes sharing no verb can never shadow one another.
                if not (earlier_methods & methods):
                    continue
                # An earlier route shadows this one when every segment either
                # matches exactly or is a parameter capturing a literal.
                if (
                    all(
                        e == p or (e.startswith("{") and not p.startswith("{"))
                        for e, p in zip(earlier, parts, strict=True)
                    )
                    and earlier != parts
                ):
                    shadowed.append(f"{path} is shadowed by /{'/'.join(earlier)}")
            seen.append((parts, methods))

        assert not shadowed, "Unreachable routes: " + "; ".join(shadowed)


class TestVersionReporting:
    """The API version must track pyproject.toml, not a hand-copied literal."""

    def test_health_version_matches_package(self, client):
        from agentic_orchestrator import __version__

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["version"] == __version__

    def test_root_version_matches_package(self, client):
        from agentic_orchestrator import __version__

        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["version"] == __version__

    def test_openapi_version_matches_package(self, client):
        from agentic_orchestrator import __version__

        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.json()["info"]["version"] == __version__

    def test_package_version_matches_pyproject(self):
        """__version__ tracks pyproject.toml rather than a hard-coded literal."""
        import tomllib
        from pathlib import Path

        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        declared = tomllib.loads(pyproject.read_text())["project"]["version"]
        assert __version__ == declared, (
            f"__version__ is {__version__!r} but pyproject.toml declares {declared!r}. "
            f"_resolve_version() reads this same pyproject.toml first, so a mismatch means "
            f"it fell through to installed metadata — check that the checkout is readable "
            f"and that [project].name is still 'agentic-orchestrator'."
        )


@pytest.fixture
def stub_adapter_health(monkeypatch):
    """Keep /adapters tests hermetic.

    The handler probes ``health_check()`` on every adapter, and several of those
    (GitHub, DefiLlama, Hacker News, Coingecko, Lens, Discord) issue real outbound
    HTTP with a 10s timeout. Left live, these tests would hit third-party APIs on
    every run — slow and flaky offline, and rate-limited on shared CI IPs. The
    assertions here are about the adapter *listing*, which needs no live probe.
    """
    from agentic_orchestrator import adapters as adapters_pkg

    async def _fake_health_check(self):
        return {"status": "stubbed", "last_fetch": None}

    for name in adapters_pkg.__all__:
        obj = getattr(adapters_pkg, name)
        if isinstance(obj, type) and issubclass(obj, adapters_pkg.BaseAdapter):
            monkeypatch.setattr(obj, "health_check", _fake_health_check, raising=False)


class TestAdaptersEndpoint:
    """/adapters must enumerate every adapter the aggregator registers."""

    def test_adapters_match_aggregator_registration(self, client, stub_adapter_health):
        from agentic_orchestrator.signals.aggregator import SignalAggregator

        response = client.get("/adapters")
        assert response.status_code == 200
        data = response.json()

        exposed = {a["name"] for a in data["adapters"]}
        registered = {a.name for a in SignalAggregator()._default_adapters()}

        assert exposed == registered, f"missing from /adapters: {registered - exposed}"
        assert data["total"] == len(registered)

    def test_coingecko_adapter_is_exposed(self, client, stub_adapter_health):
        """Regression: CoingeckoAdapter was registered but never listed."""
        response = client.get("/adapters")
        assert response.status_code == 200

        adapters = {a["name"]: a for a in response.json()["adapters"]}
        assert "coingecko" in adapters

        coingecko = adapters["coingecko"]
        assert coingecko["category"] == "crypto"
        # TRACKED_COINS must feed the shared sources/source_count contract.
        assert coingecko["source_count"] > 0
        assert len(coingecko["sources"]) == coingecko["source_count"]


class TestPaidTierVisibility:
    """A silently-dead paid tier must be visible without reading logs.

    Between 2026-08-05 and 2026-08-06 the debate tier was inert (stale PM2
    env pinned MOSS_LOCAL_LLM_ONLY=true) and no endpoint said so: /status
    reported "operational" and /usage showed $0.00, which is also what a
    quiet day looks like. These endpoints now distinguish the two.
    """

    def test_status_reports_the_tier_as_degraded_under_the_kill_switch(
        self, client, monkeypatch
    ):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "true")
        router = client.get("/status").json()["components"]["llm_router"]
        assert router["status"] == "degraded"
        assert router["local_only"] is True
        assert "debate" in router["degraded_tiers"]
        assert "MOSS_LOCAL_LLM_ONLY" in router["paid_tiers"]["debate"]["reason"]

    def test_status_reports_healthy_when_the_tier_can_spend(self, client, monkeypatch):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        router = client.get("/status").json()["components"]["llm_router"]
        assert router["status"] == "healthy"
        assert router["degraded_tiers"] == []

    def test_status_stays_operational_when_only_the_tier_is_down(self, client, monkeypatch):
        # Top-level status still tracks the database. A dead paid tier is a
        # quality problem, not an outage, and must not page as one.
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "true")
        assert client.get("/status").json()["status"] == "operational"

    def test_usage_explains_a_zero_ledger(self, client, monkeypatch):
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "true")
        data = client.get("/usage").json()
        assert data["today"]["total_cost"] == 0
        assert data["llm_routing"]["status"] == "degraded"
        assert "MOSS_LOCAL_LLM_ONLY" in data["llm_routing"]["paid_tiers"]["debate"]["reason"]

    def test_usage_never_leaks_the_api_key(self, client, monkeypatch):
        # The report is derived from key *presence*; the value must not ride
        # along on a public endpoint.
        monkeypatch.setenv("MOSS_LOCAL_LLM_ONLY", "false")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-do-not-leak")
        assert "sk-secret-do-not-leak" not in client.get("/usage").text
        assert "sk-secret-do-not-leak" not in client.get("/status").text
