"""
FastAPI main application for Mossland Agentic Orchestrator API.

Endpoints:
- GET /health - System health status
- GET /status - Overall system status
- GET /signals - Recent signals
- GET /debates - Recent debate results
- GET /trends - Trend analysis results
- GET /ideas - Ideas list
- GET /plans - Plans list
- GET /usage - API usage statistics
- GET /agents - Agent personas information
"""

import asyncio
import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from time import monotonic
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import __version__
from ..pathutil import redact_paths
from ..timeutil import utc_iso, utcnow

logger = logging.getLogger(__name__)

from ..adapters.signalmap import feed_report as signalmap_feed_report
from ..db.connection import ensure_schema, get_db
from ..db.models import NON_PLAN_STATUSES
from ..db.repositories import (
    APIUsageRepository,
    DebateRepository,
    IdeaRepository,
    PlanRepository,
    ProjectRepository,
    SignalRepository,
    TrendRepository,
)
from ..llm.budget import BudgetController
from ..llm.router import paid_tier_report


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Self-heal the database schema on startup.

    Idempotent (CREATE TABLE IF NOT EXISTS): a no-op on a healthy database,
    and it turns a missing or emptied SQLite file into an empty-but-working
    one instead of every DB-backed endpoint 500ing with "no such table" until
    an operator intervenes (2026-07 incident). ``ensure_schema`` retries the
    boot-time CREATE race against the PM2 scheduler processes and never
    raises, so a broken database cannot prevent the API from starting.
    """
    if not ensure_schema(get_db()):
        logger.error("Database schema could not be ensured at startup; see previous errors")
    yield


# This service's `id` in the ecosystem registry (`links/ecosystem-registry.json`),
# not its display name -- "ao", not "MOSS.AO". /health publishes it so a consumer
# can join a health response to its registry entry without keeping a
# domain-to-service lookup table of its own, which is the one thing such a table
# is always slightly out of date about.
SERVICE_ID = "ao"

app = FastAPI(
    title="MOSS.AO API",
    description="Mossland Agentic Orchestrator API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


def get_session():
    """Dependency to get a database session."""
    db = get_db()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


# CORS middleware - whitelist via MOSS_CORS_ORIGINS (comma-separated).
# Defaults restrict to the production domain and local dev frontends.
_default_origins = "https://ao.moss.land,http://localhost:3000,http://127.0.0.1:3000"
_cors_origins = [
    o.strip() for o in os.environ.get("MOSS_CORS_ORIGINS", _default_origins).split(",") if o.strip()
]
if "*" in _cors_origins:
    logger.warning(
        "MOSS_CORS_ORIGINS contains '*'; disabling allow_credentials to comply with CORS spec."
    )
    _allow_credentials = False
else:
    _allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


# ---------------------------------------------------------------------------
# Write-endpoint authentication
# ---------------------------------------------------------------------------
# Set MOSS_API_KEY in the environment to require X-API-Key on mutating routes.
# When unset, mutating endpoints fail closed with 503 so the operator must
# explicitly opt in (legacy unauthenticated mode is no longer supported).
_API_KEY_ENV = "MOSS_API_KEY"


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Require X-API-Key header matching MOSS_API_KEY.

    Behavior:
    - If MOSS_API_KEY is not configured, return 503 (operator must configure).
    - If the header is missing or mismatched, return 401.
    - Compares with constant-time to mitigate timing attacks.
    """
    expected = os.environ.get(_API_KEY_ENV)
    if not expected:
        logger.error("Mutating endpoint called but %s is not configured.", _API_KEY_ENV)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured on the server.",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


# ---------------------------------------------------------------------------
# /adapters probe budget
# ---------------------------------------------------------------------------
# The endpoint is unauthenticated and every request used to fan out to eleven
# third-party APIs, sequentially, each with its own ~10s timeout. Bound both
# the per-probe wait and how often we probe at all.
_ADAPTER_PROBE_TIMEOUT = 5.0
_ADAPTERS_CACHE_TTL = 60.0
_adapters_cache: Dict[str, Any] = {"payload": None, "fetched_at": 0.0}
_adapters_cache_lock = asyncio.Lock()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    # Appended rather than slotted in beside `status`: field order here is the
    # JSON key order, and the three existing keys stay exactly where consumers
    # have always found them.
    service: str


class ReadinessResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    checks: dict


class StatusResponse(BaseModel):
    status: str
    timestamp: str
    components: dict
    stats: dict


class SignalResponse(BaseModel):
    id: str
    source: str
    title: str
    summary: Optional[str]
    score: float
    created_at: str


class DebateResponse(BaseModel):
    id: str
    topic: str
    phase: str
    ideas_count: int
    created_at: str


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    phase: str
    personality: dict


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness: the process is up. Deliberately does not touch the database.

    Use ``/ready`` to decide whether this build can actually serve traffic.

    Speaks the ecosystem health contract (``links/HEALTH_CONTRACT.md``):
    ``status``/``service``/``timestamp``, so one dashboard can read every
    Mossland service without a per-service parser. ``status`` is the contract's
    ``ok``, not the old ``healthy`` -- nothing read the literal (the Lightsail
    uptime probe and ``scripts/deploy.sh`` both judge on the HTTP code and
    discard the body), so the vocabulary could be aligned without stranding a
    consumer. A flat ``ok`` is honest here: this probe deliberately checks
    nothing, so it has nothing to be degraded about.
    """
    return HealthResponse(
        status="ok",
        timestamp=utc_iso(utcnow()),
        version=__version__,
        service=SERVICE_ID,
    )


@app.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """Readiness: 200 only when the API can serve database-backed traffic.

    In the 2026-07 incident every DB endpoint returned 500 while ``/health``
    kept answering 200, so anything gated on liveness alone -- the auto-deploy
    health check included -- called a dead site a success. This probe runs a
    real table read, which a missing schema fails and a bare ``SELECT 1`` does
    not, and returns 503 when it cannot.
    """
    from sqlalchemy import func

    from ..db.models import Signal

    try:
        with get_db().session() as session:
            session.query(func.count(Signal.id)).scalar()
    except Exception as exc:
        logger.exception("/ready database probe failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "version": __version__,
                "checks": {"database": f"unavailable ({type(exc).__name__})"},
            },
        ) from exc

    return ReadinessResponse(
        status="ready",
        timestamp=utc_iso(utcnow()),
        version=__version__,
        checks={"database": "ok"},
    )


def _public_router_view(report: dict) -> dict:
    """Router health for a public endpoint, with the vendor detail stripped.

    Used by every unauthenticated endpoint that reports router state --
    ``/status`` (listed in the links.moss.land registry as this service's
    status endpoint) and ``/usage`` (called by the public web client). The operational question it has to
    answer is the one paid_tier_report() was written for -- "could a paid tier
    bill anything at all, or are we silently all-local?" -- and that is fully
    answered by status / local_only / degraded_tiers plus each tier's
    enabled / active / reason.

    ``provider``, ``model`` and the detailed ``reason`` answer a different question (which vendor and
    which exact model this deployment buys) and are not needed to tell whether
    the service is running. The provider mix is already disclosed on purpose in
    the project description ("Ollama (Local) + OpenAI/Claude"); the per-tier
    model pin is not, and a public endpoint is not the place to publish it.

    ``/usage`` gets the same treatment: it is unauthenticated too and the
    public web client calls it, so an earlier version of this docstring
    calling it "the internal cost view" was simply wrong. Anything that wants
    the unredacted report must read ``paid_tier_report()`` directly, in
    process, and not hand it to an HTTP response.
    """
    tiers = report.get("paid_tiers")
    if not isinstance(tiers, dict):
        return report
    return {
        **report,
        "paid_tiers": {
            name: _public_tier_view(tier) if isinstance(tier, dict) else tier
            for name, tier in tiers.items()
        },
    }


# Public wording for each reason_code. The private ``reason`` names the exact
# switch -- provider, environment variable, config path -- which is the point
# of it for an operator reading a log, and exactly what must not go out on an
# endpoint anyone can read.
_PUBLIC_TIER_REASONS = {
    "not_configured": "tier is not configured",
    "local_only": "paid providers are disabled (local-only mode)",
    "disabled": "tier is disabled",
    "no_model": "tier has no model configured",
    "no_provider": "tier has no provider configured",
    "provider_unavailable": "provider credentials are unavailable",
    "budget_exhausted": "API budget exhausted",
}


def _public_tier_view(tier: dict) -> dict:
    """One tier, with vendor identity and the detailed reason removed.

    Dropping the ``provider``/``model`` keys is not enough on its own: the
    ``reason`` string interpolates the provider name and its API-key
    environment variable, so a tier that is merely missing a key would put
    both back on a public endpoint. ``reason_code`` says the same thing
    without naming anything deployment-specific, and the sentence published
    alongside it is derived from the code rather than from the private text.
    """
    out = {k: v for k, v in tier.items() if k not in ("provider", "model")}
    if "reason" in out or "reason_code" in out:
        code = out.get("reason_code")
        out["reason"] = _PUBLIC_TIER_REASONS.get(code) if code else None
    return out


@app.get("/status", response_model=StatusResponse)
async def system_status(session: Session = Depends(get_session)):
    """Get overall system status with real statistics.

    Never hard-fails: when the database is broken this reports
    ``status="degraded"`` with zeroed stats instead of a 500, so external
    monitors (e.g. the moss.land governance widget, which consumes
    ``stats.agents_active/ideas_generated/debates_today``) keep working.

    Fields are only ever ADDED here, never renamed or removed: this endpoint is
    what the links.moss.land registry points at for this service, and its
    readers are not all enumerable from inside this repository.
    """

    from sqlalchemy import case, func

    from ..db.models import (
        OPEN_IDEA_STATUSES,
        OPEN_PLAN_STATUSES,
        DebateSession,
        Idea,
        Plan,
        Signal,
    )

    # Calculate real stats
    now = utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)

    stats = {
        # Since 00:00 UTC. Kept because it is published and named honestly;
        # note that it is not a throughput figure -- just after midnight UTC
        # (09:00 KST) it collapses to near zero while the pipeline is running
        # perfectly, and a consumer that labels it "24h" is off by ~6x.
        "signals_today": 0,
        "debates_today": 0,
        # The rolling window, and the field name says which window it is.
        # A reader asking "is this running" needs a figure that measures 24
        # hours rather than a label that claims to.
        "signals_24h": 0,
        "debates_24h": 0,
        # Lifetime totals. Ideas and plans are never deleted, so these say
        # nothing about what the backlog is holding. plans_created counts plan
        # documents: placeholder rows (NON_PLAN_STATUSES) were never plans.
        "ideas_generated": 0,
        "plans_created": 0,
        # ...which is what these are for. Measured 2026-09-09, 3,282 ideas had
        # ever been created and 24 were still open; a dashboard rendering the
        # first figure under the word "Active" was wrong by two orders of
        # magnitude. The partition lives in db.models beside the status
        # vocabulary it splits.
        "ideas_open": 0,
        "plans_open": 0,
        # Persona-count constant, not DB-derived; stays meaningful when degraded.
        "agents_active": 34,
        # When the pipeline last actually did something. Cumulative counts do
        # not answer that -- they stay put when ingestion dies -- which is the
        # gap the Q2 report named ("cumulative figures alone cannot establish
        # whether a pipeline is running"). null when unknown, never a
        # fabricated "now".
        "last_signal_at": None,
    }
    try:
        # One pass over `signals` for all three figures rather than three.
        # This endpoint is public, uncached, and polled every 30s per open
        # dashboard tab; `/adapters` computes its own 24h window the same way
        # (a single `case()` aggregate) but behind a 60-second cache, so the
        # shape is borrowed and the cost is not.
        #
        # Two clocks, on purpose, and the difference is the point:
        #   signals_24h  -> created_at, when AO wrote the row. This is the
        #     ingest question, and it is the column `/adapters` already
        #     publishes under this exact field name. One name, one meaning,
        #     across the API.
        #   signals_today / last_signal_at -> collected_at, the upstream event
        #     time. Both are already published; changing what an existing
        #     field measures is not something to do silently, and this change
        #     adds fields rather than redefining them.
        # They differ only for SignalMap, which deliberately sets collected_at
        # to the upstream event time (docs/signalmap.md) -- measured 2026-09-09
        # the two disagreed for that source by 45% over 24 hours.
        signals_today, signals_24h, newest = session.query(
            func.sum(case((Signal.collected_at >= today, 1), else_=0)),
            func.sum(case((Signal.created_at >= last_24h, 1), else_=0)),
            func.max(Signal.collected_at),
        ).one()
        stats["signals_today"] = int(signals_today or 0)
        stats["signals_24h"] = int(signals_24h or 0)
        stats["last_signal_at"] = utc_iso(newest)

        debates_today, debates_24h = session.query(
            func.sum(case((DebateSession.started_at >= today, 1), else_=0)),
            func.sum(case((DebateSession.started_at >= last_24h, 1), else_=0)),
        ).one()
        stats["debates_today"] = int(debates_today or 0)
        stats["debates_24h"] = int(debates_24h or 0)

        stats["ideas_generated"] = session.query(func.count(Idea.id)).scalar() or 0
        stats["plans_created"] = PlanRepository(session).count_all()
        stats["ideas_open"] = (
            session.query(func.count(Idea.id)).filter(Idea.status.in_(OPEN_IDEA_STATUSES)).scalar()
            or 0
        )
        stats["plans_open"] = (
            session.query(func.count(Plan.id)).filter(Plan.status.in_(OPEN_PLAN_STATUSES)).scalar()
            or 0
        )

        # The stat queries above are the real probe (they fail on a missing
        # schema, which the bare "SELECT 1" health check does not detect);
        # health_check() adds a connection-level sanity check on top.
        db_healthy = get_db().health_check()
    except Exception:
        logger.exception("/status statistics queries failed; reporting degraded status")
        db_healthy = False

    try:
        # budget_ok is left unchecked (None) on purpose: reading the ledger is
        # a DB round trip, and budget exhaustion is already visible on /usage.
        # What this catches is the permanent kind of degradation — kill switch
        # engaged, tier disabled, API key missing.
        llm_router_status = _public_router_view(paid_tier_report())
    except Exception:
        logger.exception("/status could not read paid-tier configuration")
        llm_router_status = {"status": "unknown"}

    try:
        # Same shape of question as llm_router above, same constraints: config
        # and a small local state file, no network and no DB, because this
        # endpoint is public and hot.
        signal_feed_status = signalmap_feed_report()
    except Exception:
        logger.exception("/status could not read the SignalMap feed state")
        signal_feed_status = {"status": "unknown"}

    return StatusResponse(
        status="operational" if db_healthy else "degraded",
        timestamp=utc_iso(utcnow()),
        components={
            # "api" is honest by construction: this handler answered.
            "api": {"status": "healthy"},
            "database": {"status": "healthy" if db_healthy else "unhealthy"},
            # There is no "cache" component here any more, and there is
            # nothing to put back: the only cache in the process tree was an
            # in-memory dict with no consumers, and it has been removed. It
            # reported "unknown" for as long as it existed -- honest, but a
            # component that can only ever refuse to answer is not a
            # component. The llm_router below reports config-level state,
            # which needs no probe; this endpoint is public and hot and must
            # not start making network calls to find out anything.
            # Config-level, not a live probe: this endpoint is public and hot,
            # so it still must not make network calls. What it *can* answer for
            # free is whether a paid tier could bill anything at all — the
            # question nothing answered when a stale PM2 env pinned
            # MOSS_LOCAL_LLM_ONLY=true and every debate ran on local gemma
            # while /status kept reporting "operational" (2026-08-06).
            # "degraded" here = config says a tier should be spending, and it
            # cannot. Whether a call actually succeeded is /usage's job.
            "llm_router": llm_router_status,
            # SignalMap is an upstream we depend on but do not operate, and its
            # one interesting failure is invisible in every count we hold:
            # `sourceWatermark` stops moving while `generatedAt` keeps
            # advancing, i.e. it keeps publishing and stops collecting. Also
            # config-level — the value was recorded by the last poll, not
            # fetched here. Like llm_router, this never changes the top-level
            # status: a stale upstream degrades idea quality, it does not take
            # the site down, and it must not page as if it had.
            "signal_feed": signal_feed_status,
        },
        stats=stats,
    )


@app.get("/signals/timeline")
async def get_signals_timeline(
    period: str = Query(default="24h", pattern="^(24h|7d)$"),
    session: Session = Depends(get_session),
):
    """Get signal collection timeline for visualization.

    Returns hourly counts for 24h or daily counts for 7d period.
    """
    from datetime import timedelta

    from sqlalchemy import extract, func

    from ..db.models import Signal

    now = utcnow()

    if period == "24h":
        # Get hourly counts for last 24 hours
        start_time = now - timedelta(hours=24)
        results = (
            session.query(
                extract("hour", Signal.collected_at).label("hour"),
                func.count(Signal.id).label("count"),
            )
            .filter(Signal.collected_at >= start_time)
            .group_by(extract("hour", Signal.collected_at))
            .all()
        )

        # Build hourly slots
        hour_counts = {int(r.hour): r.count for r in results}
        slots = []
        for i in range(24):
            hour = (now.hour - 23 + i) % 24
            slots.append(
                {
                    "label": f"{hour:02d}:00",
                    "count": hour_counts.get(hour, 0),
                    "hour": hour,
                }
            )
    else:
        # Get daily counts for last 7 days
        start_time = now - timedelta(days=7)
        results = (
            session.query(
                func.date(Signal.collected_at).label("date"), func.count(Signal.id).label("count")
            )
            .filter(Signal.collected_at >= start_time)
            .group_by(func.date(Signal.collected_at))
            .all()
        )

        # Build daily slots
        date_counts = {str(r.date): r.count for r in results}
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        slots = []
        for i in range(7):
            date = now - timedelta(days=6 - i)
            date_str = date.strftime("%Y-%m-%d")
            slots.append(
                {
                    "label": days[date.weekday()],
                    "count": date_counts.get(date_str, 0),
                }
            )

    total = sum(s["count"] for s in slots)

    return {
        "slots": slots,
        "total": total,
        "period": period,
        "timestamp": utc_iso(now),
    }


@app.get("/signals/{signal_id}")
async def get_signal_detail(
    signal_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed information about a specific signal."""
    repo = SignalRepository(session)
    signal = repo.get_by_id(signal_id)

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Delegated, not hand-copied. This body spelled out the same thirteen keys
    # in the same order as ``Signal.to_dict()``. The two never actually
    # diverged -- but the rule had to be remembered in two places to keep it
    # that way, and the UTC-marker change is the first one that would have
    # split them. One definition, one place to get it wrong.
    return signal.to_dict()


@app.get("/signals")
async def get_signals(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    source: Optional[str] = None,
    category: Optional[str] = None,
    min_score: Optional[float] = Query(default=0.0, ge=0.0),
    hours: int = Query(default=24, ge=1, le=720),
    session: Session = Depends(get_session),
):
    """Get recent signals with filtering and pagination."""
    repo = SignalRepository(session)

    # Get signals with SQL-level pagination
    signals = repo.get_recent(
        hours=hours,
        limit=limit,
        offset=offset,
        source=source,
        category=category,
        min_score=min_score,
        # A list, so "recent" means newest-first. The repository default is
        # best-scoring-first, which three scheduler callers depend on; see its
        # docstring. This endpoint feeds the Signal Explorer and
        # PipelineDetail's "Recent Signals" panel, both of which were showing
        # the window's highest-scoring row rather than its newest.
        newest_first=True,
    )

    # Get total count for pagination info
    total = repo.count_recent_filtered(
        hours=hours,
        source=source,
        category=category,
        min_score=min_score,
    )

    return {
        "signals": [s.to_dict() for s in signals],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/debates")
async def get_debates(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    phase: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get recent debate sessions with filtering."""
    repo = DebateRepository(session)

    # Get sessions with SQL-level pagination
    sessions = repo.get_all_sessions(
        limit=limit,
        offset=offset,
        status=status if status != "active" else None,
        phase=phase,
    )

    if status == "active":
        sessions = repo.get_active_sessions()
        total = len(sessions)
        sessions = sessions[offset : offset + limit]
    else:
        total = repo.count_sessions(
            status=status if status != "active" else None,
            phase=phase,
        )

    paginated = sessions

    # Build response with message counts fetched in a single bulk query
    # (avoids an N+1 that would lazy-load every session's full message list).
    message_counts = repo.count_messages_for_sessions([s.id for s in paginated])
    debates = [
        debate.to_dict(message_count=message_counts.get(debate.id, 0)) for debate in paginated
    ]

    return {
        "debates": debates,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/debates/{session_id}")
async def get_debate_detail(
    session_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed debate session with messages."""
    repo = DebateRepository(session)

    debate = repo.get_session_by_id(session_id)
    if not debate:
        raise HTTPException(status_code=404, detail=f"Debate session not found: {session_id}")

    messages = repo.get_session_messages(session_id)

    return {
        "debate": debate.to_dict(message_count=len(messages)),
        "messages": [m.to_dict() for m in messages],
        "message_count": len(messages),
    }


@app.get("/trends")
async def get_trends(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    period: Optional[str] = Query(default="all", pattern="^(all|24h|7d|30d)$"),
    category: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get trend analysis results."""
    repo = TrendRepository(session)

    # DB-level pagination: push offset/limit into the query instead of fetching
    # `limit + offset` rows and slicing in memory.
    if category:
        trends = repo.get_by_category(category, limit=limit, offset=offset)
        total = repo.count_by_category(category)
    elif period == "all":
        trends = repo.get_all(limit=limit, offset=offset)
        total = repo.count_all()
    else:
        trends = repo.get_latest(period=period, limit=limit, offset=offset)
        total = repo.count_by_period(period)

    return {
        "trends": [t.to_dict() for t in trends],
        "total": total,
        "limit": limit,
        "offset": offset,
        "period": period,
    }


@app.get("/ideas")
async def get_ideas(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get ideas list with filtering."""
    repo = IdeaRepository(session)

    # Get status counts for summary and total count
    status_counts = repo.count_by_status()

    if status:
        ideas = repo.get_by_status(status, limit=limit, offset=offset)
        total = status_counts.get(status, 0)
    else:
        ideas = repo.get_all(limit=limit, offset=offset)
        total = repo.count_all()

    return {
        "ideas": [i.to_dict() for i in ideas],
        "total": total,
        "limit": limit,
        "offset": offset,
        "status_counts": status_counts,
    }


@app.get("/ideas/{idea_id}")
async def get_idea_detail(
    idea_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed idea information with related debates and plans.

    Returns full description and debate messages for the source debate session.
    """
    idea_repo = IdeaRepository(session)
    debate_repo = DebateRepository(session)
    plan_repo = PlanRepository(session)

    idea = idea_repo.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail=f"Idea not found: {idea_id}")

    # Get source debate session (via FK or metadata for backward compatibility)
    source_debate_id = idea.debate_session_id
    if not source_debate_id and idea.extra_metadata:
        source_debate_id = idea.extra_metadata.get("debate_session_id")

    debates = []
    seen_ids = set()

    # Add source debate with messages first
    if source_debate_id:
        source_debate = debate_repo.get_session_by_id(source_debate_id)
        if source_debate:
            messages = debate_repo.get_session_messages(source_debate_id)
            debate_dict = source_debate.to_dict(message_count=len(messages))
            debate_dict["messages"] = [m.to_dict() for m in messages]
            debates.append(debate_dict)
            seen_ids.add(source_debate_id)

    # Also get any debates linked via idea_id (backward compatibility)
    linked_debates = debate_repo.get_sessions_by_idea(idea_id)
    for d in linked_debates:
        if d.id not in seen_ids:
            messages = debate_repo.get_session_messages(d.id)
            debate_dict = d.to_dict(message_count=len(messages))
            debate_dict["messages"] = [m.to_dict() for m in messages]
            debates.append(debate_dict)
            seen_ids.add(d.id)

    plans = plan_repo.get_by_idea(idea_id)

    return {
        "idea": idea.to_dict(),
        "debates": debates,
        "plans": [p.to_dict() for p in plans],
    }


@app.get("/ideas/{idea_id}/lineage")
async def get_idea_lineage(
    idea_id: str,
    session: Session = Depends(get_session),
):
    """Get complete lineage for an idea showing signals → trend → idea → plans flow.

    Returns source signals, parent trend (if any), the idea, and generated plans.
    """
    from ..db.models import Signal, Trend

    idea_repo = IdeaRepository(session)
    plan_repo = PlanRepository(session)

    idea = idea_repo.get_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail=f"Idea not found: {idea_id}")

    # Get related signals based on idea metadata or source
    signals = []
    trend = None

    # Check if idea has source trend info in metadata
    trend_id = None
    if idea.extra_metadata:
        trend_id = idea.extra_metadata.get("trend_id")
        source_signal_ids = idea.extra_metadata.get("source_signal_ids", [])

        # Fetch source signals if IDs are stored
        if source_signal_ids:
            for signal_id in source_signal_ids[:10]:  # Limit to 10
                signal = session.query(Signal).filter(Signal.id == signal_id).first()
                if signal:
                    signals.append(
                        {
                            "id": signal.id,
                            "title": signal.title,
                            "score": signal.score,
                            "source": signal.source,
                        }
                    )

    # If we have a trend_id, fetch the trend
    if trend_id:
        trend_obj = session.query(Trend).filter(Trend.id == trend_id).first()
        if trend_obj:
            trend = {
                "id": trend_obj.id,
                "name": trend_obj.name,
                "score": trend_obj.score,
                "signal_count": trend_obj.signal_count,
            }

    # If no signals found yet, try to find related signals by keywords/title
    if not signals:
        # Search for signals with similar keywords
        keywords = []
        if idea.extra_metadata and idea.extra_metadata.get("keywords"):
            keywords = idea.extra_metadata.get("keywords", [])[:5]

        if keywords:
            from sqlalchemy import or_

            keyword_filters = [Signal.title.ilike(f"%{kw}%") for kw in keywords]
            related_signals = (
                session.query(Signal)
                .filter(or_(*keyword_filters))
                .order_by(Signal.score.desc())
                .limit(5)
                .all()
            )
            for signal in related_signals:
                signals.append(
                    {
                        "id": signal.id,
                        "title": signal.title,
                        "score": signal.score,
                        "source": signal.source,
                    }
                )

    # If still no trend found, try to find by name similarity
    if not trend and idea.title:
        # Simple search by title words
        words = idea.title.split()[:3]
        for word in words:
            if len(word) > 4:  # Skip short words
                found_trend = (
                    session.query(Trend)
                    .filter(Trend.name.ilike(f"%{word}%"))
                    .order_by(Trend.score.desc())
                    .first()
                )
                if found_trend:
                    trend = {
                        "id": found_trend.id,
                        "name": found_trend.name,
                        "score": found_trend.score,
                        "signal_count": found_trend.signal_count,
                    }
                    break

    # Get plans
    plans = plan_repo.get_by_idea(idea_id)

    return {
        "signals": signals,
        "trend": trend,
        "idea": {
            "id": idea.id,
            "title": idea.title,
            "score": idea.score,
            "status": idea.status,
        },
        "plans": [
            {
                "id": p.id,
                "title": p.title,
                "version": p.version,
                "status": p.status,
            }
            for p in plans
        ],
    }


@app.get("/plans")
async def get_plans(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get plans list with filtering.

    Without ``status`` this lists plan documents only. ``?status=placeholder``
    returns the placeholder rows, which are kept but are not plans.
    """
    repo = PlanRepository(session)

    if status:
        paginated = repo.get_by_status(status, limit=limit, offset=offset)
        total = repo.count_by_status(status)
    else:
        plans = repo.get_all(limit=limit, offset=offset)
        total = repo.count_all()
        paginated = plans

    return {
        "plans": [p.to_dict() for p in paginated],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/plans/pending-approval")
async def get_pending_approval_plans(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    """
    Get plans that are pending approval (draft status, not yet approved).

    A draft is a plan that was not auto-approved.
    Users can manually approve these via POST /plans/{plan_id}/approve.
    """
    plan_repo = PlanRepository(session)

    # Get draft plans
    plans = plan_repo.get_by_status("draft", limit=limit, offset=offset)

    # Get idea scores for context
    idea_repo = IdeaRepository(session)

    result = []
    for plan in plans:
        plan_dict = plan.to_dict()

        # Get associated idea score if available
        if plan.idea_id:
            idea = idea_repo.get_by_id(plan.idea_id)
            if idea:
                plan_dict["idea_score"] = idea.score
                plan_dict["idea_title"] = idea.title

        metadata = plan.extra_metadata or {}

        # Check if auto-approval threshold info is available
        if metadata:
            plan_dict["promotion_score"] = metadata.get("promotion_score")

        result.append(plan_dict)

    return {
        "plans": result,
        # The size of the queue, not the size of this page. `len(result)` meant
        # `?limit=5` reported five plans pending when there were 39, and with no
        # `offset` the queue was unreadable past the first page -- on the one
        # endpoint whose whole purpose is telling a human how much is waiting.
        "total": plan_repo.count_by_status("draft"),
        "limit": limit,
        "offset": offset,
        "message": "These plans are pending approval. Use POST /plans/{plan_id}/approve to approve.",
    }


@app.get("/plans/{plan_id}")
async def get_plan_detail(
    plan_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed plan information."""
    repo = PlanRepository(session)

    plan = repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

    # Include full plan content
    return {
        "id": plan.id,
        "idea_id": plan.idea_id,
        "title": plan.title,
        "title_ko": getattr(plan, "title_ko", None),
        "version": plan.version,
        "status": plan.status,
        "prd_content": plan.prd_content,
        "architecture_content": plan.architecture_content,
        "user_research_content": plan.user_research_content,
        "business_model_content": plan.business_model_content,
        "project_plan_content": plan.project_plan_content,
        "final_plan": plan.final_plan,
        "final_plan_ko": getattr(plan, "final_plan_ko", None),
        "github_issue_url": plan.github_issue_url,
        "created_at": utc_iso(plan.created_at),
        "updated_at": utc_iso(plan.updated_at),
    }


@app.get("/usage")
async def get_usage(
    days: int = Query(default=7, ge=1, le=90),
    session: Session = Depends(get_session),
):
    """Get API usage statistics."""
    repo = APIUsageRepository(session)

    today_usage = repo.get_today_usage()
    today_by_provider = repo.get_today_by_provider()
    month_total = repo.get_month_total()
    history = repo.get_usage_history(days=days)

    # An empty ledger has two very different meanings — "nothing needed to
    # spend" and "the paid tier has been quietly dead for a day" — and until
    # 2026-08-06 this endpoint could not tell them apart. Reporting the tier's
    # effective state next to the numbers makes $0.00 self-explanatory.
    # Unlike /status this does consult the budget, since /usage is a cold
    # endpoint and budget exhaustion is precisely a spending question.
    try:
        budget_ok = bool(BudgetController().get_budget_status().get("can_use_api"))
    except Exception:
        logger.exception("/usage could not read budget status")
        budget_ok = None
    try:
        # Redacted for the same reason as /status: this endpoint takes no
        # credential either, and the public web client calls it. The budget
        # verdict it adds is a spending question; which model each tier pins
        # is not, and does not belong on an endpoint anyone can read.
        llm_routing = _public_router_view(paid_tier_report(budget_ok=budget_ok))
    except Exception:
        logger.exception("/usage could not read paid-tier configuration")
        llm_routing = {"status": "unknown"}

    # Same class of blind spot as the empty ledger above, one stage further on.
    # The second-pass reviewer is what actually promotes an idea, and its
    # verdicts had no reader anywhere: promotion sat at zero for twelve days
    # while every surface still said healthy, because "rejects everything" and
    # "is merely strict" produce identical output everywhere else.
    try:
        promotion_review = IdeaRepository(session).second_pass_verdict_counts(days=days)
    except Exception:
        logger.exception("/usage could not read second-pass review stats")
        promotion_review = {"status": "unknown"}

    return {
        "today": today_usage,
        "today_by_provider": today_by_provider,
        "month_total": month_total,
        "history": history,
        "days": days,
        "llm_routing": llm_routing,
        "promotion_review": promotion_review,
    }


def _activity_time(moment) -> str:
    """Clock time for today; date-qualified for anything older.

    The activity feed renders this string verbatim (`[{activity.time}]`) and it
    was `%H:%M:%S` on every row. `/activity` is not a 24-hour window — it takes
    the most recent rows of each table, so it stretches as far back as whatever
    stopped moving. During the 2026-08 promotion stall the newest plan was
    twelve days old and the feed showed it as "08:45:09", which reads as this
    morning. A dashboard built to show whether the pipeline is moving was
    stating the opposite of the truth, in the one place someone would look.
    """
    if not moment:
        return ""
    now = utcnow()
    if moment.date() == now.date():
        return moment.strftime("%H:%M:%S")
    if moment.year == now.year:
        return moment.strftime("%m-%d %H:%M")
    return moment.strftime("%Y-%m-%d %H:%M")


@app.get("/activity")
async def get_activity(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """Get recent system activity for the activity feed.

    Generates activity from real data tables (signals, trends, ideas, debates, plans)
    instead of relying on explicit system logs.
    """
    from sqlalchemy import desc

    from ..db.models import DebateSession, Idea, Signal, Trend

    activities = []

    # Get recent signals (last 24 hours, limit to avoid too many)
    recent_signals = (
        session.query(Signal)
        .filter(Signal.collected_at.isnot(None))
        .order_by(desc(Signal.collected_at))
        .limit(20)
        .all()
    )
    for signal in recent_signals:
        activities.append(
            {
                "timestamp": signal.collected_at,
                "time": _activity_time(signal.collected_at),
                "type": "trend",  # signals show as 'trend' type for SIGNAL prefix
                "message": (
                    f"Signal collected: {signal.title[:80]}..."
                    if len(signal.title) > 80
                    else f"Signal collected: {signal.title}"
                ),
                "source": signal.source,
            }
        )

    # Get recent trends
    recent_trends = (
        session.query(Trend)
        .filter(Trend.analyzed_at.isnot(None))
        .order_by(desc(Trend.analyzed_at))
        .limit(10)
        .all()
    )
    for trend in recent_trends:
        activities.append(
            {
                "timestamp": trend.analyzed_at,
                "time": _activity_time(trend.analyzed_at),
                "type": "trend",
                "message": (
                    f"Trend analyzed: {trend.name[:60]}... (score: {trend.score:.1f})"
                    if len(trend.name) > 60
                    else f"Trend analyzed: {trend.name} (score: {trend.score:.1f})"
                ),
                "signal_count": trend.signal_count,
            }
        )

    # Get recent ideas
    recent_ideas = (
        session.query(Idea)
        .filter(Idea.created_at.isnot(None))
        .order_by(desc(Idea.created_at))
        .limit(10)
        .all()
    )
    for idea in recent_ideas:
        {"promoted": "🚀", "scored": "📊", "archived": "📦"}.get(idea.status, "💡")
        activities.append(
            {
                "timestamp": idea.created_at,
                "time": _activity_time(idea.created_at),
                "type": "idea",
                "message": (
                    f"Idea generated [{idea.status}]: {idea.title[:50]}..."
                    if len(idea.title) > 50
                    else f"Idea generated [{idea.status}]: {idea.title}"
                ),
                "score": idea.score,
            }
        )

    # Get recent debates
    recent_debates = (
        session.query(DebateSession).order_by(desc(DebateSession.started_at)).limit(10).all()
    )
    for debate in recent_debates:
        if debate.started_at:
            topic_short = (
                (debate.topic[:40] + "...")
                if debate.topic and len(debate.topic) > 40
                else (debate.topic or "Unknown topic")
            )
            activities.append(
                {
                    "timestamp": debate.started_at,
                    "time": _activity_time(debate.started_at),
                    "type": "debate",
                    "message": f"Debate started: {topic_short}",
                    "phase": debate.phase,
                }
            )
        if debate.completed_at:
            activities.append(
                {
                    "timestamp": debate.completed_at,
                    "time": _activity_time(debate.completed_at),
                    "type": "debate",
                    "message": f"Debate completed: {debate.status} - {len(debate.ideas_generated or [])} ideas generated",
                    "status": debate.status,
                }
            )

    # Recent plan documents. Through the repository, which leaves placeholder
    # rows out: they were never plans, so "Plan created" would be false.
    for plan in PlanRepository(session).get_all(limit=10):
        if not plan.created_at:
            continue
        activities.append(
            {
                "timestamp": plan.created_at,
                "time": _activity_time(plan.created_at),
                "type": "plan",
                "message": (
                    f"Plan created [{plan.status}]: {plan.title[:50]}..."
                    if len(plan.title) > 50
                    else f"Plan created [{plan.status}]: {plan.title}"
                ),
                "version": plan.version,
            }
        )

    # Sort all activities by timestamp descending
    activities.sort(key=lambda x: x.get("timestamp") or datetime.min, reverse=True)

    # Limit to requested amount
    activities = activities[:limit]

    # Remove timestamp field (only used for sorting) and ensure time format
    for activity in activities:
        activity.pop("timestamp", None)

    return {
        "activities": activities,
        "total": len(activities),
    }


def _signal_yield_by_source(session: Session) -> Optional[Dict[str, Dict[str, Any]]]:
    """What each source has actually stored, measured from the rows.

    The health probes answer "can this adapter reach its upstream right now".
    They cannot answer "is this source still producing", and the two come
    apart silently -- nitter.net answered 200 to 1,008 requests a day from
    2026-08-11 to 08-26 while the twitter adapter stored zero rows. A valid
    response to a feed that has gone empty is
    indistinguishable from a healthy one, and four of the twelve adapters
    (twitter, discord, lens, farcaster) have stored nothing in the 30 days
    this table retains. Three of them still report themselves enabled; twitter
    was switched off on 2026-09-10 on the strength of this measurement.

    Measured on ``created_at`` (when AO wrote the row), NOT ``collected_at``.
    For every adapter but one the two are the same, but SignalMap deliberately
    sets ``collected_at`` to the upstream event time (see docs/signalmap.md),
    so grouping on it reports the publisher's clock as our ingest clock: a
    backfill of older events would not move the count at all, and a perfectly
    healthy 30-minute ingest reads hours stale. Measured 2026-09-09, the two
    columns disagree for SignalMap by 45% over 24 hours (219 vs 398).

    Returns ``None`` when the database cannot be read, which is different from
    a source having produced nothing, and the caller keeps that difference.
    Read failures are swallowed on purpose: ``/adapters`` answering 200 while
    the DB-backed endpoints 500 is the documented fingerprint of a lost SQLite
    file (CLAUDE.md), and coupling this endpoint to the database would erase
    it.
    """
    from sqlalchemy import case, func

    from ..db.models import Signal

    try:
        cutoff = utcnow() - timedelta(hours=24)
        rows = (
            session.query(
                Signal.source,
                func.max(Signal.created_at),
                func.sum(case((Signal.created_at >= cutoff, 1), else_=0)),
            )
            .group_by(Signal.source)
            .all()
        )
        return {
            source: {"last_signal_at": utc_iso(last), "signals_24h": int(recent or 0)}
            for source, last, recent in rows
        }
    except Exception as e:
        logger.warning(f"Adapter yield unavailable: {redact_paths(str(e))}")
        return None


@app.get("/adapters")
async def get_adapters(session: Session = Depends(get_session)):
    """Get detailed signal adapter information."""

    from ..adapters import (
        CoingeckoAdapter,
        DiscordAdapter,
        FarcasterAdapter,
        GitHubEventsAdapter,
        LensAdapter,
        NewsAPIAdapter,
        OnChainAdapter,
        RSSAdapter,
        SignalMapAdapter,
        SocialMediaAdapter,
        ThreadsAdapter,
        TwitterAdapter,
    )

    # Define all adapters with their details
    adapter_classes = [
        {
            "class": RSSAdapter,
            "category": "news",
            "description": "RSS/Atom 피드 수집기",
            "description_en": "RSS/Atom feed collector",
        },
        {
            "class": GitHubEventsAdapter,
            "category": "dev",
            "description": "GitHub 트렌딩 및 릴리스 추적",
            "description_en": "GitHub trending & releases tracker",
        },
        {
            "class": OnChainAdapter,
            "category": "crypto",
            "description": "DefiLlama TVL, DEX 볼륨, 웨일 알림, 스테이블코인 흐름",
            "description_en": "DefiLlama TVL, DEX volume, whale alerts, stablecoin flows",
        },
        {
            "class": SocialMediaAdapter,
            "category": "social",
            "description": "Reddit 서브레딧 모니터링",
            "description_en": "Reddit subreddit monitoring",
        },
        {
            "class": NewsAPIAdapter,
            "category": "news",
            "description": "NewsAPI, Cryptopanic, Hacker News",
            "description_en": "NewsAPI, Cryptopanic, Hacker News",
        },
        {
            "class": TwitterAdapter,
            "category": "social",
            "description": "Twitter/X Nitter RSS 풀 (20+ 계정)",
            "description_en": "Twitter/X via Nitter RSS pool (20+ accounts)",
        },
        {
            "class": DiscordAdapter,
            "category": "social",
            "description": "Discord 서버 공지사항 (7개 서버)",
            "description_en": "Discord server announcements (7 servers)",
        },
        {
            "class": LensAdapter,
            "category": "web3",
            "description": "Lens Protocol GraphQL API (10개 프로필)",
            "description_en": "Lens Protocol GraphQL API (10 profiles)",
        },
        {
            "class": FarcasterAdapter,
            "category": "web3",
            "description": "Farcaster/Warpcast (10개 유저, 10개 채널)",
            "description_en": "Farcaster/Warpcast (10 users, 10 channels)",
        },
        {
            "class": CoingeckoAdapter,
            "category": "crypto",
            "description": "Coingecko 시장 데이터, 급등/급락, 트렌딩 코인",
            "description_en": "Coingecko market data, gainers/losers, trending coins",
        },
        {
            "class": ThreadsAdapter,
            "category": "social",
            "description": "Meta Threads 게시물 수집 (3개 계정)",
            "description_en": "Meta Threads posts (3 accounts)",
        },
        {
            "class": SignalMapAdapter,
            # A UI grouping label, not SignalData.category. "news" rather than a
            # truer word like "narrative" because AdapterDetailModal renders its
            # category tally by iterating a fixed icon map — an unlisted value
            # keeps its adapter card but drops it out of the counts.
            "category": "news",
            "description": "SignalMap 발행 피드 (canonical 토픽·엔티티·이벤트)",
            "description_en": "SignalMap export feed (canonical topics, entities, events)",
        },
    ]

    async def describe(adapter_info: dict) -> dict:
        """Static description plus a bounded health probe; never raises."""
        try:
            adapter = adapter_info["class"]()

            try:
                health = await asyncio.wait_for(
                    adapter.health_check(), timeout=_ADAPTER_PROBE_TIMEOUT
                )
            except asyncio.TimeoutError:
                health = {"status": "unknown", "error": "health probe timed out"}
            except Exception as probe_error:
                health = {"status": "unknown", "error": redact_paths(str(probe_error))}

            # Build detailed info
            info = {
                "name": adapter.name,
                "category": adapter_info["category"],
                "description": adapter_info["description"],
                "description_en": adapter_info["description_en"],
                "enabled": adapter.is_enabled(),
                "health": health,
            }

            # Add adapter-specific details
            if hasattr(adapter, "SUBREDDITS"):
                info["sources"] = adapter.SUBREDDITS
                info["source_count"] = len(adapter.SUBREDDITS)
            elif hasattr(adapter, "TRACKED_ACCOUNTS"):
                info["sources"] = adapter.TRACKED_ACCOUNTS
                info["source_count"] = len(adapter.TRACKED_ACCOUNTS)
            elif hasattr(adapter, "TRACKED_PROTOCOLS"):
                info["sources"] = adapter.TRACKED_PROTOCOLS
                info["source_count"] = len(adapter.TRACKED_PROTOCOLS)
            elif hasattr(adapter, "TRACKED_PROFILES"):
                info["sources"] = adapter.TRACKED_PROFILES
                info["source_count"] = len(adapter.TRACKED_PROFILES)
            elif hasattr(adapter, "TRACKED_USERS"):
                info["sources"] = adapter.TRACKED_USERS
                info["source_count"] = len(adapter.TRACKED_USERS)
            elif hasattr(adapter, "TRACKED_SERVERS"):
                info["sources"] = [srv["name"] for srv in adapter.TRACKED_SERVERS]
                info["source_count"] = len(adapter.TRACKED_SERVERS)
            elif hasattr(adapter, "TRACKED_COINS"):
                info["sources"] = adapter.TRACKED_COINS
                info["source_count"] = len(adapter.TRACKED_COINS)
            elif hasattr(adapter, "TRACKED_KINDS"):
                info["sources"] = adapter.TRACKED_KINDS
                info["source_count"] = len(adapter.TRACKED_KINDS)

            return info

        except Exception as e:
            return {
                "name": adapter_info["class"].__name__.replace("Adapter", "").lower(),
                "category": adapter_info["category"],
                "description": adapter_info["description"],
                "enabled": False,
                # A config-read failure here names the file by absolute path.
                "error": redact_paths(str(e)),
            }

    # One lock, one cache: this endpoint needs no authentication, and it used
    # to run all twelve probes sequentially on every request, each with its own
    # ~10s timeout. That made a single GET a minute-long third-party fan-out
    # and any number of concurrent GETs an amplifier pointed at other people's
    # APIs. Probes now run together under a short per-probe budget, and the
    # result is shared for _ADAPTERS_CACHE_TTL seconds.
    async with _adapters_cache_lock:
        cached = _adapters_cache.get("payload")
        fetched_at = _adapters_cache.get("fetched_at")
        if cached is not None and (monotonic() - fetched_at) < _ADAPTERS_CACHE_TTL:
            return cached

        adapters_info = list(await asyncio.gather(*(describe(a) for a in adapter_classes)))

        # Measured yield, joined on adapter.name == signals.source. A source
        # missing from a successful read has genuinely stored nothing, which
        # is a 0 and not an unknown -- the distinction is the whole point of
        # the field, so it survives into the response.
        measured = _signal_yield_by_source(session)
        for info in adapters_info:
            row = measured.get(info.get("name")) if measured is not None else None
            info["last_signal_at"] = row["last_signal_at"] if row else None
            info["signals_24h"] = (
                row["signals_24h"] if row else (0 if measured is not None else None)
            )

        payload = {
            "adapters": adapters_info,
            "total": len(adapters_info),
            "enabled_count": sum(1 for a in adapters_info if a.get("enabled", False)),
            "probed_at": utc_iso(utcnow()),
        }
        _adapters_cache["payload"] = payload
        _adapters_cache["fetched_at"] = monotonic()
        return payload


@app.get("/agents")
async def get_agents(phase: Optional[str] = None):
    """Get agent personas information."""
    from ..personas import get_convergence_agents, get_divergence_agents, get_planning_agents

    def agent_to_dict(agent, phase_name: str) -> dict:
        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "phase": phase_name,
            "handle": agent.handle,
            "expertise": agent.expertise,
            "personality": {
                "thinking": agent.personality.thinking.value,
                "decision": agent.personality.decision.value,
                "communication": agent.personality.communication.value,
                "action": agent.personality.action.value,
            },
        }

    agents = []

    if phase is None or phase == "divergence":
        for agent in get_divergence_agents():
            agents.append(agent_to_dict(agent, "divergence"))

    if phase is None or phase == "convergence":
        for agent in get_convergence_agents():
            agents.append(agent_to_dict(agent, "convergence"))

    if phase is None or phase == "planning":
        for agent in get_planning_agents():
            agents.append(agent_to_dict(agent, "planning"))

    return {
        "agents": agents,
        "total": len(agents),
    }


@app.get("/pipeline/live")
async def get_pipeline_live(session: Session = Depends(get_session)):
    """Get real-time pipeline status with conversion rates and current processing items.

    Returns:
        - stages: Current counts for each pipeline stage (signals, trends, ideas, plans)
        - conversion_rates: Conversion rates between stages
        - processing: Currently processing items
        - rates: Hourly/daily generation rates
    """
    from datetime import timedelta

    from sqlalchemy import desc, func

    from ..db.models import (
        DebateSession,
        DebateSessionStatus,
        Idea,
        Project,
        Signal,
        Trend,
    )

    now = utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_hour = now - timedelta(hours=1)
    now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Get counts for each stage
    total_signals = session.query(func.count(Signal.id)).scalar() or 0
    total_trends = session.query(func.count(Trend.id)).scalar() or 0
    total_ideas = session.query(func.count(Idea.id)).scalar() or 0
    # Plan documents only: placeholder rows would inflate this count and skew
    # both conversion rates built on it.
    plan_repo = PlanRepository(session)
    total_plans = plan_repo.count_all()
    total_projects = session.query(func.count(Project.id)).scalar() or 0

    # Get hourly rates
    signals_last_hour = (
        session.query(func.count(Signal.id)).filter(Signal.collected_at >= last_hour).scalar() or 0
    )

    trends_today = (
        session.query(func.count(Trend.id)).filter(Trend.analyzed_at >= today).scalar() or 0
    )

    ideas_today = session.query(func.count(Idea.id)).filter(Idea.created_at >= today).scalar() or 0

    plans_last_7d = plan_repo.count_created_since(last_7d)

    projects_last_7d = (
        session.query(func.count(Project.id)).filter(Project.created_at >= last_7d).scalar() or 0
    )

    # Calculate conversion rates
    signals_to_trends = (total_trends / total_signals * 100) if total_signals > 0 else 0
    trends_to_ideas = (total_ideas / total_trends * 100) if total_trends > 0 else 0
    ideas_to_plans = (total_plans / total_ideas * 100) if total_ideas > 0 else 0
    plans_to_projects = (total_projects / total_plans * 100) if total_plans > 0 else 0

    # Get currently processing items
    processing = []

    # Recent signals (last 5 minutes)
    recent_signals = (
        session.query(Signal)
        .filter(Signal.collected_at >= now - timedelta(minutes=5))
        .order_by(desc(Signal.collected_at))
        .limit(3)
        .all()
    )
    for signal in recent_signals:
        minutes_ago = (
            int((now - signal.collected_at).total_seconds() / 60) if signal.collected_at else 0
        )
        processing.append(
            {
                "type": "SIGNAL",
                "title": signal.title[:60] + "..." if len(signal.title) > 60 else signal.title,
                "time_ago": f"{minutes_ago}m ago" if minutes_ago > 0 else "just now",
                "source": signal.source,
            }
        )

    # Active debates. The literal used to be "in-progress", which nothing has
    # ever written: the scheduler writes "active" and DebateSessionStatus.ACTIVE
    # is "active", so this filter matched zero rows on every call and the
    # "processing now" list silently never mentioned a debate -- including
    # during the ~15 minutes every six hours when one is the only thing the
    # system is doing. The frontend found and fixed its own copy of this same
    # wrong literal (website/src/app/transparency/debates/page.tsx); the
    # backend kept it.
    active_debates = (
        session.query(DebateSession)
        .filter(
            DebateSession.status == DebateSessionStatus.ACTIVE.value,
            # Same 90-minute bound the debate task's own startup recovery
            # sweep uses to mark orphans failed. A SIGKILLed debate stays
            # `active` until the next 6-hourly cycle sweeps it, and the item
            # rendered here carries no timestamp (`time_ago` is the round
            # counter), so without this an orphan is indistinguishable from a
            # live debate on a list titled "processing now". This filter was
            # unreachable before the literal above was fixed; fixing it is
            # what makes the bound necessary.
            DebateSession.started_at >= now - timedelta(minutes=90),
        )
        .order_by(desc(DebateSession.started_at))
        .limit(2)
        .all()
    )
    for debate in active_debates:
        topic_short = (
            (debate.topic[:50] + "...")
            if debate.topic and len(debate.topic) > 50
            else (debate.topic or "Unknown")
        )
        processing.append(
            {
                "type": "DEBATE",
                "title": topic_short,
                "time_ago": f"R{debate.round_number}/{debate.max_rounds}",
                "phase": debate.phase,
            }
        )

    # Recent trends being analyzed (last 30 minutes)
    recent_trends = (
        session.query(Trend)
        .filter(Trend.analyzed_at >= now - timedelta(minutes=30))
        .order_by(desc(Trend.analyzed_at))
        .limit(2)
        .all()
    )
    for trend in recent_trends:
        minutes_ago = (
            int((now - trend.analyzed_at).total_seconds() / 60) if trend.analyzed_at else 0
        )
        processing.append(
            {
                "type": "TREND",
                "title": trend.name[:50] + "..." if len(trend.name) > 50 else trend.name,
                "time_ago": f"{minutes_ago}m ago",
                "score": trend.score,
            }
        )

    # Projects being generated
    generating_projects = (
        session.query(Project)
        .filter(Project.status == "generating")
        .order_by(desc(Project.created_at))
        .limit(2)
        .all()
    )
    for proj in generating_projects:
        processing.append(
            {
                "type": "PROJECT",
                "title": proj.name[:50] + "..." if len(proj.name) > 50 else proj.name,
                "time_ago": "generating",
                "status": proj.status,
            }
        )

    return {
        "stages": {
            "signals": {
                "count": total_signals,
                "rate": f"+{signals_last_hour}/hr",
                "status": "active" if signals_last_hour > 0 else "idle",
            },
            "trends": {
                "count": total_trends,
                "rate": f"+{trends_today}/day",
                "status": "active" if trends_today > 0 else "idle",
            },
            "ideas": {
                "count": total_ideas,
                "rate": f"+{ideas_today}/day",
                "status": "active" if ideas_today > 0 else "idle",
            },
            "plans": {
                "count": total_plans,
                "rate": f"+{plans_last_7d}/wk",
                "status": "active" if plans_last_7d > 0 else "idle",
            },
            "projects": {
                "count": total_projects,
                "rate": f"+{projects_last_7d}/wk",
                "status": (
                    "active"
                    if any(p.status == "generating" for p in generating_projects)
                    else ("idle" if projects_last_7d == 0 else "completed")
                ),
            },
        },
        "conversion_rates": {
            "signals_to_trends": round(signals_to_trends, 1),
            "trends_to_ideas": round(trends_to_ideas, 1),
            "ideas_to_plans": round(ideas_to_plans, 1),
            "plans_to_projects": round(plans_to_projects, 1),
        },
        "processing": processing[:5],  # Limit to 5 items
        "timestamp": utc_iso(now),
    }


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "MOSS.AO API",
        "version": __version__,
        "description": "Mossland Agentic Orchestrator API",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "status": "/status",
            "signals": "/signals",
            "trends": "/trends",
            "ideas": "/ideas",
            "plans": "/plans",
            "projects": "/projects",
            "debates": "/debates",
            "usage": "/usage",
            "activity": "/activity",
            "agents": "/agents",
            "adapters": "/adapters",
            "pipeline/live": "/pipeline/live",
            "docs": "/docs",
        },
    }


# =============================================================================
# Project Generation Endpoints
# =============================================================================

# Background task storage for project generation jobs
# Persisted to disk to survive server restarts
import json as _json
from pathlib import Path as _Path

_JOBS_FILE = _Path(__file__).parent.parent.parent.parent / "data" / "project_jobs.json"


def _load_jobs() -> Dict[str, Dict[str, Any]]:
    """Load jobs from disk."""
    try:
        if _JOBS_FILE.exists():
            return _json.loads(_JOBS_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_jobs():
    """Persist jobs to disk."""
    try:
        _JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _JOBS_FILE.write_text(_json.dumps(_project_jobs, indent=2, default=str))
    except Exception:
        pass


_project_jobs: Dict[str, Dict[str, Any]] = _load_jobs()


class GenerateProjectRequest(BaseModel):
    """Request body for project generation."""

    force_regenerate: bool = False


class GenerateProjectResponse(BaseModel):
    """Response for project generation trigger."""

    job_id: str
    status: str
    message: str


async def _generate_project_task(
    job_id: str,
    plan_id: str,
    force_regenerate: bool,
):
    """Background task for project generation."""
    from ..db import get_database
    from ..llm import HybridLLMRouter
    from ..project import ProjectScaffold

    _project_jobs[job_id]["status"] = "in_progress"
    _project_jobs[job_id]["started_at"] = utc_iso(utcnow())
    _save_jobs()

    session = None
    try:
        # Initialize components
        db = get_database()
        session = db.get_session()
        router = HybridLLMRouter()

        # Create scaffold and generate
        scaffold = ProjectScaffold(
            router=router,
            db_session=session,
        )

        result = await scaffold.generate_project(
            plan_id=plan_id,
            force_regenerate=force_regenerate,
        )

        session.commit()

        # Update job status
        _project_jobs[job_id]["status"] = "completed" if result.success else "failed"
        _project_jobs[job_id]["completed_at"] = utc_iso(utcnow())
        _project_jobs[job_id]["result"] = result.to_dict()
        _save_jobs()

    except Exception as e:
        # Generation can fail anywhere: the router, the scaffold, or the
        # commit. Only the success path used to close the session, so a run of
        # failures leaked a connection and an open transaction each time --
        # which, on the single-connection pool this used to run against, could
        # wedge the whole API.
        logger.exception("Project generation job %s failed", job_id)
        if session is not None:
            session.rollback()
        _project_jobs[job_id]["status"] = "failed"
        _project_jobs[job_id]["completed_at"] = utc_iso(utcnow())
        # GET /jobs/{id} returns this dict verbatim and is unauthenticated;
        # an OSError here carries the absolute path it failed on.
        _project_jobs[job_id]["error"] = redact_paths(str(e))
        _save_jobs()
    finally:
        if session is not None:
            session.close()


@app.post("/plans/{plan_id}/generate-project", response_model=GenerateProjectResponse)
async def generate_project(
    plan_id: str,
    request: GenerateProjectRequest = GenerateProjectRequest(),
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
):
    """
    Trigger project generation from an approved Plan.

    This endpoint starts an asynchronous project generation job.
    Use GET /jobs/{job_id} to check the status. A placeholder row has no plan
    document and is refused with 409, even with force_regenerate.
    """
    import uuid

    # Verify plan exists and is approved
    plan_repo = PlanRepository(session)
    plan = plan_repo.get_by_id(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

    # Ahead of the force check: force_regenerate redoes a project, it does not
    # turn a row with no plan document into something to scaffold from.
    if plan.status in NON_PLAN_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Plan {plan_id} has no plan document (status: {plan.status}).",
        )

    if plan.status != "approved" and not request.force_regenerate:
        raise HTTPException(
            status_code=400,
            detail=f"Plan must be approved for project generation. Current status: {plan.status}",
        )

    # Check if project already exists
    from ..db.models import COMPLETED_PROJECT_STATUSES

    project_repo = ProjectRepository(session)
    existing = project_repo.get_by_plan(plan_id)

    if existing and existing.status in COMPLETED_PROJECT_STATUSES and not request.force_regenerate:
        return GenerateProjectResponse(
            job_id="",
            status="exists",
            message="Project already exists. Use force_regenerate=true to regenerate.",
        )

    if existing and existing.status == "generating":
        return GenerateProjectResponse(
            job_id="",
            status="in_progress",
            message="Project generation is already in progress.",
        )

    # Create job ID
    job_id = str(uuid.uuid4())[:8]

    # Initialize job tracking
    _project_jobs[job_id] = {
        "job_id": job_id,
        "plan_id": plan_id,
        "status": "pending",
        "created_at": utc_iso(utcnow()),
    }

    # Start background task
    if background_tasks:
        background_tasks.add_task(
            _generate_project_task,
            job_id,
            plan_id,
            request.force_regenerate,
        )
    else:
        # Fallback: run synchronously (for testing)
        import asyncio

        asyncio.create_task(_generate_project_task(job_id, plan_id, request.force_regenerate))

    return GenerateProjectResponse(
        job_id=job_id,
        status="accepted",
        message=f"Project generation started. Check status at /jobs/{job_id}",
    )


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of an async job."""
    if job_id not in _project_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return _project_jobs[job_id]


@app.get("/projects")
async def get_projects(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Get list of generated projects."""
    repo = ProjectRepository(session)

    if status:
        projects = repo.get_by_status(status, limit=limit + offset)
        total = repo.count_by_status(status)
        paginated = projects[offset : offset + limit]
    else:
        projects = repo.get_all(limit=limit, offset=offset)
        total = repo.count_all()
        paginated = projects

    return {
        "projects": [p.to_dict() for p in paginated],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/projects/{project_id}")
async def get_project_detail(
    project_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed project information."""
    repo = ProjectRepository(session)
    plan_repo = PlanRepository(session)

    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Get associated plan
    plan = plan_repo.get_by_id(project.plan_id) if project.plan_id else None

    return {
        "project": project.to_dict(),
        "plan": plan.to_dict() if plan else None,
    }


@app.get("/plans/{plan_id}/project")
async def get_plan_project(
    plan_id: str,
    session: Session = Depends(get_session),
):
    """Get project associated with a plan."""
    project_repo = ProjectRepository(session)
    plan_repo = PlanRepository(session)

    # Verify plan exists
    plan = plan_repo.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

    # Get project
    project = project_repo.get_by_plan(plan_id)

    return {
        "project": project.to_dict() if project else None,
        "plan_id": plan_id,
    }


class ApprovePlanRequest(BaseModel):
    """Request body for plan approval."""

    generate_project: bool = False  # If True, also trigger project generation


class ApprovePlanResponse(BaseModel):
    """Response for plan approval."""

    plan_id: str
    status: str
    message: str
    job_id: Optional[str] = None


@app.post("/plans/{plan_id}/approve", response_model=ApprovePlanResponse)
async def approve_plan(
    plan_id: str,
    request: ApprovePlanRequest = ApprovePlanRequest(),
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
):
    """
    Manually approve a draft plan for project generation.

    This allows users to approve low-scoring plans that weren't auto-approved.
    If generate_project=true, also triggers project generation immediately.

    Use this for:
    - Plans with score < 8.0 that weren't auto-approved
    - Plans that need manual review before project generation

    A placeholder row is not a plan and is refused with 409.
    """
    import uuid

    plan_repo = PlanRepository(session)
    plan = plan_repo.get_by_id(plan_id)

    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")

    # First, and leaving the row untouched: approval is what unlocks project
    # generation, and a row with no plan document has nothing to approve.
    if plan.status in NON_PLAN_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Plan {plan_id} has no plan document (status: {plan.status}).",
        )

    if plan.status == "approved":
        message = "Plan is already approved."
        if request.generate_project:
            # Check if project exists
            project_repo = ProjectRepository(session)
            existing = project_repo.get_by_plan(plan_id)
            if existing and existing.status == "ready":
                message += " Project already exists."
            else:
                # Trigger project generation
                job_id = str(uuid.uuid4())[:8]
                _project_jobs[job_id] = {
                    "job_id": job_id,
                    "plan_id": plan_id,
                    "status": "pending",
                    "created_at": utc_iso(utcnow()),
                }
                if background_tasks:
                    background_tasks.add_task(_generate_project_task, job_id, plan_id, False)
                else:
                    import asyncio

                    asyncio.create_task(_generate_project_task(job_id, plan_id, False))
                return ApprovePlanResponse(
                    plan_id=plan_id,
                    status="approved",
                    message="Plan already approved. Project generation started.",
                    job_id=job_id,
                )
        return ApprovePlanResponse(
            plan_id=plan_id,
            status="approved",
            message=message,
        )

    # Approve the plan.
    #
    # extra_metadata is a plain JSON column, not MutableDict, so SQLAlchemy
    # cannot see an in-place mutation: assigning a *new* dict is what marks the
    # attribute dirty. Mutating the existing one (the previous code) silently
    # dropped the approval audit trail for every pipeline-created plan, since
    # those always arrive with extra_metadata already populated.
    plan.status = "approved"
    plan.extra_metadata = {
        **(plan.extra_metadata or {}),
        "manually_approved": True,
        # Left unmarked on purpose, unlike every other instant in this module:
        # this one is stored, not published. It goes into a JSON column that no
        # response emits -- Plan.to_dict() does not include extra_metadata, and
        # /plans/pending-approval reads named scalar keys out of it. A sweep
        # that "finishes the job" here would change a stored value, not a
        # published one.
        "approved_at": utcnow().isoformat(),
    }
    session.commit()

    job_id = None
    message = "Plan approved successfully."

    # Optionally generate project
    if request.generate_project:
        job_id = str(uuid.uuid4())[:8]
        _project_jobs[job_id] = {
            "job_id": job_id,
            "plan_id": plan_id,
            "status": "pending",
            "created_at": utc_iso(utcnow()),
        }
        if background_tasks:
            background_tasks.add_task(_generate_project_task, job_id, plan_id, False)
        else:
            import asyncio

            asyncio.create_task(_generate_project_task(job_id, plan_id, False))
        message = "Plan approved and project generation started."

    return ApprovePlanResponse(
        plan_id=plan_id,
        status="approved",
        message=message,
        job_id=job_id,
    )
