"""The promotion gate must be observable, and the approval queue must be countable.

Promotion sat at exactly zero for twelve days. Nothing was broken in a way any
surface could report: the second-pass reviewer returned a verdict for every
idea, the verdict was written to ``extra_metadata.triage.second_pass``, and it
was read by nothing. ``/status`` said ``operational`` throughout, because a gate
that rejects everything and a gate that is merely strict produce identical
output everywhere except the verdict tally nobody kept.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from agentic_orchestrator.api.main import app, get_session
from agentic_orchestrator.db.models import Base
from agentic_orchestrator.db.repositories import IdeaRepository, PlanRepository
from agentic_orchestrator.timeutil import utcnow


@pytest.fixture
def session():
    # StaticPool + check_same_thread: TestClient serves requests on another
    # thread, and an in-memory SQLite connection belongs to the thread that
    # opened it. Sharing one connection is also what makes the rows written by
    # the test visible to the request.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    yield db
    db.close()


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


def add_reviewed_idea(repo, idea_id: str, verdict: str, *, updated_at: datetime = None):
    """An idea carrying a triage record, as ``backlog_triage`` writes one."""
    idea = repo.create(
        {
            "id": idea_id,
            "title": f"Idea {idea_id}",
            "summary": f"summary of idea {idea_id}",
            "source_type": "debate",
            "status": "archived",
            "score": 8.0,
            "extra_metadata": {
                "triage": {
                    "second_pass": {
                        "verdict": verdict,
                        "reason": "duplicate of an earlier idea",
                        "score": 5.0,
                        "model": "test-model",
                    }
                }
            },
        }
    )
    idea.updated_at = updated_at or utcnow()
    repo.session.flush()
    return idea


class TestSecondPassVerdictCounts:
    def test_a_gate_that_never_confirms_is_reported_as_such(self, session):
        """The production shape: 613 consecutive reviews, zero confirmations."""
        repo = IdeaRepository(session)
        for n in range(25):
            add_reviewed_idea(repo, f"i{n}", "demote")

        stats = repo.second_pass_verdict_counts(days=7)

        assert stats["verdicts"]["demote"] == 25
        assert stats["confirm_rate"] == 0.0
        assert stats["status"] == "no_confirmations"

    def test_a_working_gate_reads_healthy(self, session):
        repo = IdeaRepository(session)
        for n in range(20):
            add_reviewed_idea(repo, f"c{n}", "confirm")
        for n in range(20):
            add_reviewed_idea(repo, f"d{n}", "demote")

        stats = repo.second_pass_verdict_counts(days=7)

        assert stats["confirm_rate"] == 0.5
        assert stats["status"] == "healthy"

    def test_a_small_sample_is_not_called_a_stuck_gate(self, session):
        """A handful of rejections in a row is ordinary variance. Crying wolf
        here would train an operator to ignore the one signal that matters."""
        repo = IdeaRepository(session)
        for n in range(3):
            add_reviewed_idea(repo, f"i{n}", "demote")

        assert repo.second_pass_verdict_counts(days=7)["status"] == "insufficient_data"

    def test_an_outage_does_not_look_like_a_stuck_gate(self, session):
        """UNAVAILABLE is not a verdict — it means the reviewer could not be
        reached. Counting it against the confirm rate would report a provider
        outage as a rejecting gate and send the operator to the wrong place."""
        repo = IdeaRepository(session)
        for n in range(40):
            add_reviewed_idea(repo, f"u{n}", "unavailable")

        stats = repo.second_pass_verdict_counts(days=7)

        assert stats["verdicts"]["unavailable"] == 40
        assert stats["confirm_rate"] is None
        assert stats["status"] == "insufficient_data"

    def test_counts_reviews_by_when_they_happened_not_when_the_idea_was_made(self, session):
        """Triage re-scores the OLDEST backlog ideas, so today's reviews are
        attached to ideas created weeks ago. Windowing on ``created_at`` would
        show an empty tally on a busy day."""
        repo = IdeaRepository(session)
        for n in range(25):
            idea = add_reviewed_idea(repo, f"old{n}", "demote")
            idea.created_at = utcnow() - timedelta(days=30)
        session.flush()

        assert repo.second_pass_verdict_counts(days=7)["reviewed"] == 25

    def test_ideas_without_a_triage_record_are_ignored(self, session):
        repo = IdeaRepository(session)
        repo.create(
            {
                "id": "plain",
                "title": "No triage record",
                "summary": "s",
                "source_type": "debate",
                "status": "scored",
            }
        )
        repo.create(
            {
                "id": "empty",
                "title": "Empty metadata",
                "summary": "s",
                "source_type": "debate",
                "status": "scored",
                "extra_metadata": {},
            }
        )

        stats = repo.second_pass_verdict_counts(days=7)

        assert stats["reviewed"] == 0
        assert stats["status"] == "insufficient_data"


class TestUsageEndpointReportsTheGate:
    def test_usage_carries_the_promotion_review_tally(self, client, session):
        repo = IdeaRepository(session)
        for n in range(25):
            add_reviewed_idea(repo, f"i{n}", "demote")
        session.commit()

        body = client.get("/usage").json()

        assert body["promotion_review"]["status"] == "no_confirmations"
        assert body["promotion_review"]["verdicts"]["demote"] == 25


class TestPendingApprovalQueue:
    """The one endpoint whose whole job is telling a human how much is waiting."""

    @staticmethod
    def _add_drafts(session, count):
        idea_repo = IdeaRepository(session)
        plan_repo = PlanRepository(session)
        for n in range(count):
            idea_repo.create(
                {
                    "id": f"pi{n}",
                    "title": f"Idea {n}",
                    "summary": "s",
                    "source_type": "debate",
                    "status": "promoted",
                }
            )
            plan_repo.create(
                {
                    "id": f"p{n}",
                    "idea_id": f"pi{n}",
                    "title": f"Plan {n}",
                    "status": "draft",
                    "version": 1,
                }
            )
        session.commit()

    def test_total_counts_the_queue_not_the_page(self, client, session):
        """``total: len(result)`` meant ``?limit=5`` reported five plans
        pending when there were 39 — the queue could not grow in the operator's
        view no matter how long it actually got."""
        self._add_drafts(session, 39)

        body = client.get("/plans/pending-approval?limit=5").json()

        assert len(body["plans"]) == 5
        assert body["total"] == 39

    def test_the_queue_is_readable_past_the_first_page(self, client, session):
        """With no ``offset`` and a hard cap of 100, anything past the first
        page was permanently invisible."""
        self._add_drafts(session, 30)

        first = client.get("/plans/pending-approval?limit=10&offset=0").json()
        second = client.get("/plans/pending-approval?limit=10&offset=10").json()

        first_ids = {p["id"] for p in first["plans"]}
        second_ids = {p["id"] for p in second["plans"]}
        assert len(first_ids) == len(second_ids) == 10
        assert not (first_ids & second_ids)
        assert second["total"] == 30

    def test_approved_plans_are_not_in_the_queue(self, client, session):
        self._add_drafts(session, 3)
        IdeaRepository(session).create(
            {
                "id": "di",
                "title": "Done",
                "summary": "s",
                "source_type": "debate",
                "status": "promoted",
            }
        )
        PlanRepository(session).create(
            {"id": "done", "idea_id": "di", "title": "Approved", "status": "approved", "version": 1}
        )
        session.commit()

        body = client.get("/plans/pending-approval").json()

        assert body["total"] == 3
