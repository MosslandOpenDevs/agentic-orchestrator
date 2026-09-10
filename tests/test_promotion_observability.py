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
from agentic_orchestrator.db.models import Base, Plan
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

    def test_a_placeholder_is_not_in_the_queue(self, client, session):
        """The queue is plans waiting on a human; a placeholder is not a plan."""
        self._add_drafts(session, 3)
        PlanRepository(session).create(
            {
                "id": "ph",
                "idea_id": "pi0",
                "title": "Plan: no document",
                "status": "placeholder",
                "version": 1,
            }
        )
        session.commit()
        # Guard: the row exists, so its absence below is the queue's doing.
        assert session.query(Plan).filter(Plan.status == "placeholder").count() == 1

        body = client.get("/plans/pending-approval").json()

        assert "ph" not in {p["id"] for p in body["plans"]}
        assert body["total"] == 3


class TestActivityFeedTimestamps:
    """A feed that spans twelve days must not render every row as a clock time.

    During the promotion stall the newest plan was twelve days old and the feed
    showed it as "08:45:09" — this morning, to any reader. The dashboard whose
    job is to show whether the pipeline is moving was stating the opposite of
    the truth, in the one place someone would look for it.
    """

    @staticmethod
    def _render(moment):
        from agentic_orchestrator.api.main import _activity_time

        return _activity_time(moment)

    def test_today_stays_a_bare_clock_time(self):
        now = utcnow()

        assert self._render(now.replace(hour=8, minute=45, second=9)) == "08:45:09"

    def test_an_older_row_says_which_day(self):
        stale = utcnow() - timedelta(days=12)

        rendered = self._render(stale)

        assert stale.strftime("%m-%d") in rendered
        assert rendered != stale.strftime("%H:%M:%S")

    def test_a_row_from_another_year_says_which_year(self):
        # timedelta, not `.replace(year=...)`: on 29 February the latter raises
        # ValueError, so the suite would go red once every four years in CI.
        old = utcnow() - timedelta(days=400)

        assert str(old.year) in self._render(old)

    def test_a_missing_timestamp_renders_as_empty(self):
        assert self._render(None) == ""

    def test_the_feed_uses_it(self, client, session):
        """End-to-end: a plan from twelve days ago must not read as today's."""
        idea_repo = IdeaRepository(session)
        plan_repo = PlanRepository(session)
        idea_repo.create(
            {
                "id": "ai",
                "title": "Old",
                "summary": "s",
                "source_type": "debate",
                "status": "promoted",
            }
        )
        plan = plan_repo.create(
            {"id": "ap", "idea_id": "ai", "title": "Plan: Old", "status": "draft", "version": 1}
        )
        stale = utcnow() - timedelta(days=12)
        plan.created_at = stale
        session.commit()

        rows = client.get("/activity").json()
        plan_rows = [r for r in rows.get("activities", rows) if r.get("type") == "plan"]

        assert plan_rows, "the feed should carry the plan row"
        assert stale.strftime("%m-%d") in plan_rows[0]["time"]


class TestActivityFeedAnnouncesOnlyPlans:
    def test_a_newer_placeholder_is_not_announced_while_the_draft_is(self, client, session):
        """The feed says "Plan created"; a placeholder row is not a plan.

        The placeholder is the newest row, so a feed that did not leave it out
        would list it first rather than push it past the cut.
        """
        IdeaRepository(session).create(
            {
                "id": "fi",
                "title": "Feed",
                "summary": "s",
                "source_type": "debate",
                "status": "promoted",
            }
        )
        plan_repo = PlanRepository(session)
        draft = plan_repo.create(
            {"id": "fd", "idea_id": "fi", "title": "Plan: Written", "status": "draft"}
        )
        placeholder = plan_repo.create(
            {"id": "fp", "idea_id": "fi", "title": "Plan: Never written", "status": "placeholder"}
        )
        draft.created_at = utcnow() - timedelta(hours=1)
        placeholder.created_at = utcnow()
        session.commit()
        # Guard: both rows exist and the placeholder really is the newer one.
        assert session.query(Plan).count() == 2
        assert placeholder.created_at > draft.created_at

        rows = client.get("/activity").json()
        messages = [r["message"] for r in rows.get("activities", rows) if r.get("type") == "plan"]

        assert any("Plan: Written" in m for m in messages), messages
        assert not any("Plan: Never written" in m for m in messages), messages


class TestBothWritersOfTheVerdictAreCounted:
    """Two writers, two shapes. Backlog triage nests the verdict under
    ``triage``; the debate path writes it at the top level. Reading only the
    triage shape made this report — the one thing that exists to make the gate
    visible — blind to every debate-time review. In a mixed population that is
    worse than blind: triage demotes alongside unseen debate confirmations read
    as a gate confirming nothing at all, which is a false alarm on the exact
    signal an operator is meant to trust.
    """

    @staticmethod
    def _debate_reviewed(repo, idea_id, verdict):
        """An idea as the DEBATE path writes it: second_pass at the top level."""
        idea = repo.create(
            {
                "id": idea_id,
                "title": f"Idea {idea_id}",
                "summary": "s",
                "source_type": "debate",
                "status": "promoted",
                "score": 8.0,
                "extra_metadata": {
                    "auto_score": {"total": 8.0},
                    "debate_topic": "Wallet UX",
                    "second_pass": {"verdict": verdict, "reason": "r", "score": 8.0},
                },
            }
        )
        idea.updated_at = utcnow()
        repo.session.flush()

    def test_debate_path_verdicts_are_counted(self, session):
        repo = IdeaRepository(session)
        for n in range(30):
            self._debate_reviewed(repo, f"d{n}", "confirm")

        stats = repo.second_pass_verdict_counts(days=7)

        assert stats["reviewed"] == 30
        assert stats["confirm_rate"] == 1.0
        assert stats["status"] == "healthy"

    def test_mixed_writers_are_summed_not_shadowed(self, session):
        repo = IdeaRepository(session)
        for n in range(30):
            self._debate_reviewed(repo, f"d{n}", "confirm")
        for n in range(30):
            add_reviewed_idea(repo, f"t{n}", "demote")

        stats = repo.second_pass_verdict_counts(days=7)

        assert stats["verdicts"] == {"confirm": 30, "demote": 30, "reject": 0, "unavailable": 0}
        assert stats["confirm_rate"] == 0.5
        assert stats["status"] == "healthy", "a working gate was reported as confirming nothing"
