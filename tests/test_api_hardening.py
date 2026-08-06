"""Regressions for public-API and background-job defects found in review.

Covers:
- pagination limits that could be driven negative to dump whole tables
- the approval audit trail silently lost to an untracked JSON mutation
- a retry of a failed project generation that did nothing and reported success
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.models import Base, Idea, Plan, Project, Signal
from agentic_orchestrator.project.scaffold import ProjectScaffold
from agentic_orchestrator.timeutil import utcnow

PAGINATED_ENDPOINTS = [
    "/signals",
    "/trends",
    "/ideas",
    "/plans",
    "/debates",
    "/projects",
    "/activity",
]


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # noqa: N806

    session = TestingSessionLocal()
    for i in range(5):
        session.add(
            Signal(
                id=f"sig-{i}",
                source="rss",
                title=f"Signal {i}",
                category="ai",
                score=0.5,
                collected_at=utcnow(),
            )
        )
    session.commit()
    session.close()

    def override_get_session():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


class TestPaginationLowerBound:
    """`le=` alone left the bottom open, and SQLite reads LIMIT -1 as
    "no limit" -- so ?limit=-1 walked straight past the documented cap and
    serialized every matching row."""

    @pytest.mark.parametrize("path", PAGINATED_ENDPOINTS)
    def test_negative_limit_is_rejected(self, client, path):
        assert client.get(f"{path}?limit=-1").status_code == 422

    @pytest.mark.parametrize("path", PAGINATED_ENDPOINTS)
    def test_zero_limit_is_rejected(self, client, path):
        assert client.get(f"{path}?limit=0").status_code == 422

    def test_valid_limit_still_works(self, client):
        response = client.get("/signals?limit=2")
        assert response.status_code == 200
        assert len(response.json()["signals"]) == 2


class TestApprovalAuditTrail:
    """extra_metadata is a plain JSON column, so SQLAlchemy only notices a
    *reassignment*. The old in-place mutation meant manually_approved and
    approved_at were dropped for every pipeline-created plan (they all arrive
    with extra_metadata already populated)."""

    def test_manual_approval_is_recorded(self, client, monkeypatch):
        monkeypatch.setenv("MOSS_API_KEY", "test-key")

        session_gen = app.dependency_overrides[get_session]()
        session = next(session_gen)
        session.add(Idea(id="idea-1", title="An idea", summary="seed", source_type="debate"))
        session.add(
            Plan(
                id="plan-1",
                idea_id="idea-1",
                title="A plan",
                status="draft",
                extra_metadata={"auto_promoted": True},
            )
        )
        session.commit()

        response = client.post(
            "/plans/plan-1/approve",
            json={"generate_project": False},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 200

        session.expire_all()
        plan = session.query(Plan).filter(Plan.id == "plan-1").one()
        assert plan.status == "approved"
        assert plan.extra_metadata["manually_approved"] is True
        assert plan.extra_metadata["approved_at"]
        # Existing metadata is preserved, not replaced.
        assert plan.extra_metadata["auto_promoted"] is True
        session.close()


@pytest.fixture
def scaffold_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)  # noqa: N806
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestFailedGenerationRetry:
    """The API lets an `error` project be retried, but the scaffold returned
    early for *any* existing row -- success=True, project_path=None, no work
    done -- and the background job recorded that as "completed"."""

    @pytest.mark.asyncio
    async def test_errored_project_is_regenerated(self, tmp_path, scaffold_session):
        scaffold_session.add(
            Idea(
                id="idea-1", title="Real-time market insights", summary="seed", source_type="debate"
            )
        )
        scaffold_session.add(
            Plan(
                id="plan-1",
                idea_id="idea-1",
                title="Real-time market insights",
                final_plan="# Plan\n",
            )
        )
        scaffold_session.add(Project(id="proj-err", plan_id="plan-1", name="x", status="error"))
        scaffold_session.commit()

        scaffold = ProjectScaffold(
            router=None,
            projects_dir=str(tmp_path / "projects"),
            db_session=scaffold_session,
        )
        result = await scaffold.generate_project(plan_id="plan-1")

        assert result.success, result.error
        # Real work happened rather than an early "already exists" return.
        assert result.project_path
        assert result.error != "Project already exists. Use force_regenerate=True to regenerate."

    @pytest.mark.asyncio
    async def test_in_flight_generation_is_not_restarted(self, tmp_path, scaffold_session):
        scaffold_session.add(Idea(id="idea-2", title="Busy", summary="seed", source_type="debate"))
        scaffold_session.add(
            Plan(id="plan-2", idea_id="idea-2", title="Busy", final_plan="# Plan\n")
        )
        scaffold_session.add(
            Project(id="proj-gen", plan_id="plan-2", name="x", status="generating")
        )
        scaffold_session.commit()

        scaffold = ProjectScaffold(
            router=None,
            projects_dir=str(tmp_path / "projects"),
            db_session=scaffold_session,
        )
        result = await scaffold.generate_project(plan_id="plan-2")

        assert not result.success
        assert "already in progress" in (result.error or "")

    @pytest.mark.asyncio
    async def test_a_stale_error_row_does_not_shadow_the_successful_one(
        self, tmp_path, scaffold_session
    ):
        """Retrying leaves the failed row behind and adds a new one, so a plan
        can have several projects. Picking an arbitrary one would let the old
        error record trigger a regeneration on every single call."""
        scaffold_session.add(
            Idea(id="idea-4", title="Retried", summary="seed", source_type="debate")
        )
        scaffold_session.add(
            Plan(id="plan-4", idea_id="idea-4", title="Retried", final_plan="# Plan\n")
        )
        scaffold_session.add(
            Project(
                id="proj-old-error",
                plan_id="plan-4",
                name="x",
                status="error",
                created_at=utcnow() - timedelta(hours=2),
            )
        )
        scaffold_session.add(
            Project(
                id="proj-new-ok",
                plan_id="plan-4",
                name="x",
                status="ready",
                directory_path="/somewhere",
                created_at=utcnow() - timedelta(hours=1),
            )
        )
        scaffold_session.commit()

        scaffold = ProjectScaffold(
            router=None,
            projects_dir=str(tmp_path / "projects"),
            db_session=scaffold_session,
        )
        result = await scaffold.generate_project(plan_id="plan-4")

        assert result.project_id == "proj-new-ok"
        assert "already exists" in (result.error or "")

    @pytest.mark.asyncio
    async def test_an_abandoned_generating_row_does_not_block_forever(
        self, tmp_path, scaffold_session
    ):
        """Nothing clears `generating` when the run that claimed it is killed,
        so without an expiry a crashed generation blocks that plan forever."""
        scaffold_session.add(
            Idea(id="idea-5", title="Stalled", summary="seed", source_type="debate")
        )
        scaffold_session.add(
            Plan(id="plan-5", idea_id="idea-5", title="Stalled", final_plan="# Plan\n")
        )
        scaffold_session.add(
            Project(
                id="proj-stuck",
                plan_id="plan-5",
                name="x",
                status="generating",
                created_at=utcnow() - timedelta(hours=6),
            )
        )
        scaffold_session.commit()

        scaffold = ProjectScaffold(
            router=None,
            projects_dir=str(tmp_path / "projects"),
            db_session=scaffold_session,
        )
        result = await scaffold.generate_project(plan_id="plan-5")

        assert result.success, result.error
        assert result.project_path

    @pytest.mark.asyncio
    async def test_completed_project_still_short_circuits(self, tmp_path, scaffold_session):
        scaffold_session.add(Idea(id="idea-3", title="Done", summary="seed", source_type="debate"))
        scaffold_session.add(
            Plan(id="plan-3", idea_id="idea-3", title="Done", final_plan="# Plan\n")
        )
        scaffold_session.add(
            Project(
                id="proj-ok",
                plan_id="plan-3",
                name="x",
                status="ready",
                directory_path="/somewhere",
            )
        )
        scaffold_session.commit()

        scaffold = ProjectScaffold(
            router=None,
            projects_dir=str(tmp_path / "projects"),
            db_session=scaffold_session,
        )
        result = await scaffold.generate_project(plan_id="plan-3")

        assert result.success
        assert result.project_id == "proj-ok"
        assert "already exists" in (result.error or "")
